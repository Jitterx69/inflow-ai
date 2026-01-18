from fastapi import FastAPI, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from typing import List, Optional
import uuid
import os
import json
from datetime import datetime
from pydantic import BaseModel
from confluent_kafka import Producer
import boto3
from botocore.exceptions import ClientError

from .database import get_db, engine, Base
from .models import Draft, DraftStatus, Asset

# --- Kafka Setup ---
producer_conf = {'bootstrap.servers': os.getenv("KAFKA_BOOTSTRAP_SERVERS", "localhost:9092")}
try:
    producer = Producer(producer_conf)
except Exception:
    producer = None

def delivery_report(err, msg):
    if err is not None:
        print(f"Message delivery failed: {err}")
    else:
        print(f"Message delivered to {msg.topic()} [{msg.partition()}]")

# --- S3 Setup ---
S3_BUCKET_NAME = os.getenv("S3_BUCKET_NAME", "inflow-assets-dev")
CDN_DOMAIN = os.getenv("CDN_DOMAIN") # e.g. https://cdn.inflow.ai
AWS_REGION = os.getenv("AWS_REGION", "us-east-1")

s3_client = boto3.client(
    "s3",
    region_name=AWS_REGION,
    aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
    aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY")
)

ALLOWED_MIME_TYPES = {
    "image/jpeg", "image/png", "image/gif", "image/webp",
    "video/mp4", "video/quicktime", "video/webm"
}




app = FastAPI(title="Creator Studio Service")

# --- Pydantic Schemas ---

class DraftBase(BaseModel):
    content: Optional[dict] = None

class DraftCreate(DraftBase):
    creator_id: str

class DraftUpdate(DraftBase):
    status: Optional[DraftStatus] = None
    scheduled_time: Optional[datetime] = None

class DraftResponse(DraftBase):
    id: uuid.UUID
    creator_id: str
    status: DraftStatus
    scheduled_time: Optional[datetime] = None
    last_updated: datetime

    class Config:
        from_attributes = True

class FeedbackRequest(BaseModel):
    draft_id: str
    action: str
    diff: str

class AssetUploadRequest(BaseModel):
    creator_id: str
    filename: str
    content_type: str

class AssetUploadResponse(BaseModel):
    upload_url: str
    fields: dict
    asset_id: uuid.UUID
    asset_url: str




# --- Lifecycle ---

@app.on_event("startup")
async def startup():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

# --- Endpoints ---

@app.get("/health")
async def health_check():
    return {"status": "ok"}

@app.get("/drafts/{creator_id}", response_model=List[DraftResponse])
async def get_drafts(creator_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Draft).where(Draft.creator_id == creator_id))
    drafts = result.scalars().all()
    return drafts

@app.post("/drafts", response_model=DraftResponse, status_code=status.HTTP_201_CREATED)
async def create_draft(draft: DraftCreate, db: AsyncSession = Depends(get_db)):
    new_draft = Draft(
        creator_id=draft.creator_id,
        content=draft.content,
        status=DraftStatus.DRAFT
    )
    db.add(new_draft)
    await db.commit()
    await db.refresh(new_draft)
    return new_draft

@app.put("/drafts/{draft_id}", response_model=DraftResponse)
async def update_draft(draft_id: uuid.UUID, draft_update: DraftUpdate, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Draft).where(Draft.id == draft_id))
    draft = result.scalars().first()
    
    if not draft:
        raise HTTPException(status_code=404, detail="Draft not found")
    
    if draft_update.content is not None:
        draft.content = draft_update.content
    
    if draft_update.status is not None:
        draft.status = draft_update.status
    
    if draft_update.scheduled_time is not None:
        draft.scheduled_time = draft_update.scheduled_time
        
    await db.commit()
    await db.refresh(draft)
    return draft

@app.get("/calendar/{creator_id}", response_model=List[DraftResponse])
async def get_calendar(creator_id: str, start_date: datetime, end_date: datetime, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(Draft)
        .where(Draft.creator_id == creator_id)
        .where(Draft.scheduled_time >= start_date)
        .where(Draft.scheduled_time <= end_date)
    )
    drafts = result.scalars().all()
    return drafts

@app.patch("/post/{draft_id}/schedule", response_model=DraftResponse)
async def schedule_post(draft_id: uuid.UUID, scheduled_time: datetime, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Draft).where(Draft.id == draft_id))
    draft = result.scalars().first()
    
    if not draft:
        raise HTTPException(status_code=404, detail="Draft not found")
        
    draft.scheduled_time = scheduled_time
    await db.commit()
    await db.refresh(draft)
    return draft

@app.post("/feedback")
async def submit_feedback(feedback: FeedbackRequest):
    if producer:
        producer.produce(
            "creator.feedback.v1",
            key=feedback.draft_id,
            value=json.dumps(feedback.dict()),
            callback=delivery_report
        )
        producer.poll(0)
        return {"status": "received"}
    return {"status": "received (kafka unavailable)"}

@app.post("/assets/upload-url", response_model=AssetUploadResponse)
async def generate_upload_url(request: AssetUploadRequest, db: AsyncSession = Depends(get_db)):
    """
    Generate a secure Presigned POST URL for S3 upload.
    Enforces content-type and size limits (500MB).
    """
    if request.content_type not in ALLOWED_MIME_TYPES:
        raise HTTPException(
            status_code=400, 
            detail=f"Invalid content type. Allowed: {ALLOWED_MIME_TYPES}"
        )

    # 1. Generate unique object key
    file_ext = request.filename.split('.')[-1] if '.' in request.filename else "bin"
    object_key = f"uploads/{request.creator_id}/{uuid.uuid4()}.{file_ext}"

    # 2. Determine Public URL (CDN or S3)
    if CDN_DOMAIN:
        # If CDN_DOMAIN doesn't start with http, assume https
        base = CDN_DOMAIN if CDN_DOMAIN.startswith("http") else f"https://{CDN_DOMAIN}"
        public_url = f"{base}/{object_key}"
    else:
        public_url = f"https://{S3_BUCKET_NAME}.s3.{AWS_REGION}.amazonaws.com/{object_key}"

    try:
        # 3. Generate Presigned POST (Policy Enforced)
        # Allows implementing file size limits and strict content-type
        presigned_data = s3_client.generate_presigned_post(
            Bucket=S3_BUCKET_NAME,
            Key=object_key,
            Fields={
                'Content-Type': request.content_type,
                'acl': 'public-read' # Optional: make it public or private based on bucket policy
            },
            Conditions=[
                {'Content-Type': request.content_type},
                {'acl': 'public-read'},
                ['content-length-range', 1024, 524288000] # 1KB to 500MB
            ],
            ExpiresIn=3600
        )
    except ClientError as e:
        raise HTTPException(status_code=500, detail=str(e))

    # 4. Create Asset Record in DB
    new_asset = Asset(
        creator_id=request.creator_id,
        s3_key=object_key,
        url=public_url,
        mime_type=request.content_type
    )
    db.add(new_asset)
    await db.commit()
    await db.refresh(new_asset)
        
    return AssetUploadResponse(
        upload_url=presigned_data['url'],
        fields=presigned_data['fields'],
        asset_id=new_asset.id,
        asset_url=public_url
    )




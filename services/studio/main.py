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

from .database import get_db, engine, Base
from .models import Draft, DraftStatus

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


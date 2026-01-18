import json
import logging
import datetime
from typing import Optional
from pydantic import BaseModel, ValidationError
from sqlalchemy import Column, String, DateTime, create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from confluent_kafka import Consumer, KafkaError, KafkaException

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

Base = declarative_base()

# --- Models ---

class InstagramEvent(BaseModel):
    post_id: str
    caption: str
    timestamp: datetime.datetime
    media_url: str
    platform_user_id: str

class RawSocialEvent(Base):
    __tablename__ = 'raw_social_events'

    id = Column(String, primary_key=True)  # Using post_id as PK
    post_id = Column(String, nullable=False)
    caption = Column(String, nullable=False)
    timestamp = Column(DateTime, nullable=False)
    media_url = Column(String, nullable=False)
    platform_user_id = Column(String, nullable=False)
    processed_at = Column(DateTime, nullable=True)

# --- Consumer ---

class InstagramConsumer:
    def __init__(self, kafka_conf: dict, db_url: str):
        self.consumer = Consumer(kafka_conf)
        self.engine = create_engine(db_url)
        self.Session = sessionmaker(bind=self.engine)
        
        # Ensure table exists (for simplicity in this task)
        Base.metadata.create_all(self.engine)

    def run(self, topic: str):
        self.consumer.subscribe([topic])
        logger.info(f"Subscribed to {topic}")

        try:
            while True:
                msg = self.consumer.poll(timeout=1.0)

                if msg is None:
                    continue

                if msg.error():
                    if msg.error().code() == KafkaError._PARTITION_EOF:
                        continue
                    else:
                        logger.error(f"Kafka Error: {msg.error()}")
                        continue

                # Process Message
                session = self.Session()
                try:
                    # 1. Decode & Parse
                    data = json.loads(msg.value().decode('utf-8'))
                    
                    # 2. Validate
                    event = InstagramEvent(**data)
                    logger.info(f"Received event: {event.post_id}")

                    # 3. Write to DB
                    db_record = RawSocialEvent(
                        id=event.post_id,
                        post_id=event.post_id,
                        caption=event.caption,
                        timestamp=event.timestamp,
                        media_url=event.media_url,
                        platform_user_id=event.platform_user_id,
                        processed_at=datetime.datetime.utcnow()
                    )
                    session.merge(db_record) # Use merge to handle duplicates/updates idempotent-ish
                    session.commit()
                    
                    # 4. Commit Offset
                    self.consumer.commit(asynchronous=False)
                    logger.info(f"Committed offset for {event.post_id}")

                except ValidationError as e:
                    logger.error(f"Schema Violation: {e}")
                    # Skip bad message, commit offset to move on
                    self.consumer.commit(asynchronous=False)
                except Exception as e:
                    logger.exception(f"Processing Error: {e}")
                    session.rollback()
                    # Decide: fail hard or skip? 
                    # Instruction says: "If validation fails... DO NOT commit to DB, but DO commit offset"
                    # For other errors, we might want to retry (looping), but for now let's just log.
                finally:
                    session.close()

        except KeyboardInterrupt:
            pass
        finally:
            self.consumer.close()

if __name__ == "__main__":
    # Example Usage
    conf = {
        'bootstrap.servers': 'localhost:9092',
        'group.id': 'instagram-consumer-group',
        'auto.offset.reset': 'earliest'
    }
    # In a real app, DB URL comes from env
    db_url = "postgresql://user:password@localhost/dbname" 
    
    consumer = InstagramConsumer(conf, db_url)
    consumer.run("platform.instagram.events")

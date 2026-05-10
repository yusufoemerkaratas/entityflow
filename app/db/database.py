from os import getenv

from dotenv import load_dotenv
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

load_dotenv()

DATABASE_URL = getenv("DATABASE_URL")

if not DATABASE_URL:
    raise ValueError("DATABASE_URL is not set in the environment.")

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def initialize_vision_schema():
    ddl_statements = [
        """
        CREATE TABLE IF NOT EXISTS vision_inspections (
            id SERIAL PRIMARY KEY,
            filename TEXT NOT NULL,
            image_width INTEGER NOT NULL,
            image_height INTEGER NOT NULL,
            uploaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """,
        """
        CREATE TABLE IF NOT EXISTS vision_detections (
            id SERIAL PRIMARY KEY,
            inspection_id INTEGER NOT NULL REFERENCES vision_inspections(id) ON DELETE CASCADE,
            label TEXT NOT NULL,
            confidence FLOAT NOT NULL,
            bbox_x INTEGER NOT NULL,
            bbox_y INTEGER NOT NULL,
            bbox_width INTEGER NOT NULL,
            bbox_height INTEGER NOT NULL,
            review_status TEXT DEFAULT 'pending' CHECK (review_status IN ('pending', 'accepted', 'rejected'))
        )
        """,
        """
        CREATE INDEX IF NOT EXISTS idx_vision_detections_inspection_id
        ON vision_detections(inspection_id)
        """,
        """
        CREATE INDEX IF NOT EXISTS idx_vision_detections_review_status
        ON vision_detections(review_status)
        """,
    ]

    with engine.begin() as connection:
        for ddl in ddl_statements:
            connection.execute(text(ddl))


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
from datetime import datetime as dt
import uuid
from typing import List
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from sqlalchemy import create_engine, Column, String, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from fastapi.middleware.cors import CORSMiddleware

DATABASE_URL = "sqlite:///./markdowns.db"
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

class MarkdownDB(Base):
    __tablename__ = "markdowns"

    id = Column(String, primary_key=True, index=True)
    content = Column(String, nullable=False)
    date = Column(DateTime, default=dt.utcnow)

Base.metadata.create_all(bind=engine)

class MarkdownCreate(BaseModel):
    content: str

class MarkdownResponse(MarkdownCreate):
    id: str
    date: dt

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], 
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"], 
)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

from fastapi import Depends
from sqlalchemy.orm import Session

@app.post("/markdowns/", response_model=MarkdownResponse)
def create_markdown(markdown: MarkdownCreate, db: Session = Depends(get_db)):
    new_markdown = MarkdownDB(id=str(uuid.uuid4()), content=markdown.content)
    db.add(new_markdown)
    db.commit()
    db.refresh(new_markdown)
    return new_markdown

@app.get("/markdowns/", response_model=List[MarkdownResponse])
def list_markdowns(db: Session = Depends(get_db)):
    return db.query(MarkdownDB).all()

@app.get("/markdowns/{markdown_id}", response_model=MarkdownResponse)
def get_markdown(markdown_id: str, db: Session = Depends(get_db)):
    markdown = db.query(MarkdownDB).filter(MarkdownDB.id == markdown_id).first()
    if not markdown:
        raise HTTPException(status_code=404, detail="Markdown not found")
    return markdown

@app.put("/markdowns/{markdown_id}", response_model=MarkdownResponse)
def update_markdown(markdown_id: str, markdown: MarkdownCreate, db: Session = Depends(get_db)):
    existing_markdown = db.query(MarkdownDB).filter(MarkdownDB.id == markdown_id).first()
    
    if not existing_markdown:
        raise HTTPException(status_code=404, detail="Markdown not found")

    existing_markdown.content = markdown.content
    db.commit()
    db.refresh(existing_markdown)

    return existing_markdown

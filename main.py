import os
from datetime import datetime
from typing import List, Optional

# Core FastAPI and Pydantic
from fastapi import FastAPI, Depends, HTTPException, status
from pydantic import BaseModel, EmailStr
from passlib.context import CryptContext

# Database and ORM
from sqlalchemy import create_engine, Column, Integer, String, Text, DateTime, ForeignKey, func, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship, Session
from sqlalchemy.schema import Index
from sqlalchemy.dialects.postgresql import ENUM

# --- 1. CONFIGURATION AND DATABASE SETUP ---

# This URL must be updated with your PostgreSQL credentials and server location.
# Example format: "postgresql+psycopg2://user:password@host:port/database_name"
DATABASE_URL = "postgresql+psycopg2://postgres:mysecretpassword@localhost:5432/sih_db"

# Passlib context for secure password hashing (using bcrypt)
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# SQLAlchemy setup
Base = declarative_base()
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Dependency function to get the database session
def get_db():
    """Provides a transactional database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Initialize FastAPI app
app = FastAPI(
    title="SIH Mental Health Support API",
    description="Backend for the AI-powered mental wellness platform.",
    version="1.0.0"
)

# --- 2. PASSWORD UTILITIES ---

def get_password_hash(password):
    """Generates the secure hash string (which contains the salt)."""
    return pwd_context.hash(password)

def verify_password(plain_password, hashed_password):
    """Verifies a plain password against the stored hash."""
    return pwd_context.verify(plain_password, hashed_password)

# --- 3. DATABASE MODELS (SQLAlchemy ORM) ---
# These map directly to your PostgreSQL tables.

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, nullable=False)
    email = Column(String(100), unique=True, nullable=False)
    # password_hash stores the full hash (including the salt and cost factors)
    password_hash = Column(Text, nullable=False)
    created_at = Column(DateTime(timezone=True), default=func.now())

    # Relationships
    posts = relationship("Post", back_populates="author")
    comments = relationship("Comment", back_populates="author")
    mood_entries = relationship("MoodEntry", back_populates="user")
    chat_sessions = relationship("ChatSession", back_populates="user")

    __table_args__ = (
        Index('idx_users_email', 'email'),
    )

class Post(Base):
    __tablename__ = "posts"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    title = Column(String(255), nullable=False)
    content = Column(Text, nullable=False)
    created_at = Column(DateTime(timezone=True), default=func.now())
    updated_at = Column(DateTime(timezone=True), default=func.now(), onupdate=func.now()) # Automatic update via SQLAlchemy

    # Relationships
    author = relationship("User", back_populates="posts")
    comments = relationship("Comment", back_populates="post")

    __table_args__ = (
        Index('idx_posts_user_id', 'user_id'),
        Index('idx_posts_created_at', 'created_at', postgresql_using='btree', postgresql_ops={'created_at': 'DESC NULLS LAST'}),
    )

class Comment(Base):
    __tablename__ = "comments"
    id = Column(Integer, primary_key=True, index=True)
    post_id = Column(Integer, ForeignKey("posts.id", ondelete="CASCADE"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    content = Column(Text, nullable=False)
    created_at = Column(DateTime(timezone=True), default=func.now())

    # Relationships
    post = relationship("Post", back_populates="comments")
    author = relationship("User", back_populates="comments")

    __table_args__ = (
        Index('idx_comments_post_id', 'post_id'),
    )

# --- New Models for Mental Health Features ---

class MoodEntry(Base):
    __tablename__ = "mood_entries"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    # Mood score from 1 (Very Low) to 10 (Very High)
    mood_score = Column(Integer, nullable=False)
    notes = Column(Text, nullable=True)
    entry_date = Column(DateTime(timezone=True), default=func.now())

    user = relationship("User", back_populates="mood_entries")

class ChatSession(Base):
    __tablename__ = "chat_sessions"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    # E.g., 'Anxiety', 'General Check-in'
    topic = Column(String(100), nullable=True)
    session_start = Column(DateTime(timezone=True), default=func.now())
    session_end = Column(DateTime(timezone=True), nullable=True)
    # Stores the full JSON/TEXT log of the conversation.
    log_content = Column(Text, nullable=True)
    # AI response analysis (e.g., 'High Stress Detected')
    ai_summary = Column(Text, nullable=True)

    user = relationship("User", back_populates="chat_sessions")

class Resource(Base):
    __tablename__ = "resources"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    resource_type = Column(String(50), nullable=False) # E.g., 'Hotline', 'Therapist', 'Article'
    contact_info = Column(String(255), nullable=True) # Phone or Email
    website_url = Column(String(255), nullable=True)
    description = Column(Text, nullable=True)
    is_verified = Column(Boolean, default=False)


# Create all tables (Run this once when setting up the database)
# Base.metadata.create_all(bind=engine)

# --- 4. PYDANTIC SCHEMAS (Data validation/serialization for the API) ---
# These define what the frontend sends and expects back.

# User Schemas
class UserBase(BaseModel):
    username: str
    email: EmailStr

class UserCreate(UserBase):
    password: str

class UserResponse(UserBase):
    id: int
    created_at: datetime
    class Config:
        orm_mode = True

# Post Schemas
class PostBase(BaseModel):
    title: str
    content: str

class PostCreate(PostBase):
    user_id: int # In a real app, this would be derived from the auth token

class CommentCreate(BaseModel):
    post_id: int
    user_id: int
    content: str

class CommentResponse(CommentCreate):
    id: int
    created_at: datetime
    class Config:
        orm_mode = True

class PostResponse(PostCreate):
    id: int
    created_at: datetime
    updated_at: datetime
    comments: List[CommentResponse] = []
    class Config:
        orm_mode = True

# Mental Health Schemas
class MoodEntryCreate(BaseModel):
    user_id: int
    mood_score: int # 1 to 10
    notes: Optional[str] = None

class MoodEntryResponse(MoodEntryCreate):
    id: int
    entry_date: datetime
    class Config:
        orm_mode = True

class ChatSessionCreate(BaseModel):
    user_id: int
    topic: Optional[str] = None
    log_content: str # Initial message or full log
    
class ResourceResponse(BaseModel):
    id: int
    name: str
    resource_type: str
    contact_info: Optional[str] = None
    website_url: Optional[str] = None
    description: Optional[str] = None
    class Config:
        orm_mode = True

# --- 5. FASTAPI ROUTES (API Endpoints) ---

@app.get("/", status_code=status.HTTP_200_OK)
def read_root():
    """Simple health check endpoint."""
    return {"message": "Welcome to the SIH Mental Health API - Status: Operational"}

# --- USER ROUTES ---

@app.post("/users/", response_model=UserResponse, status_code=status.HTTP_201_CREATED, tags=["Users"])
def create_user(user: UserCreate, db: Session = Depends(get_db)):
    """User registration endpoint."""
    # Check if email or username already exists
    if db.query(User).filter((User.email == user.email) | (User.username == user.username)).first():
        raise HTTPException(status_code=400, detail="Email or username already registered")

    # Hash the password securely
    hashed_password = get_password_hash(user.password)

    db_user = User(
        username=user.username,
        email=user.email,
        password_hash=hashed_password
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

# --- COMMUNITY FORUM ROUTES (Posts and Comments) ---

@app.post("/posts/", response_model=PostBase, status_code=status.HTTP_201_CREATED, tags=["Community"])
def create_post(post: PostCreate, db: Session = Depends(get_db)):
    """Create a new post in the community forum."""
    db_post = Post(**post.dict())
    db.add(db_post)
    db.commit()
    db.refresh(db_post)
    return db_post

@app.get("/posts/", response_model=List[PostResponse], tags=["Community"])
def list_posts(db: Session = Depends(get_db)):
    """Get a list of all posts with their comments, ordered by creation date."""
    posts = db.query(Post).order_by(Post.created_at.desc()).all()
    return posts

@app.post("/comments/", response_model=CommentResponse, status_code=status.HTTP_201_CREATED, tags=["Community"])
def create_comment(comment: CommentCreate, db: Session = Depends(get_db)):
    """Add a comment to an existing post."""
    db_comment = Comment(**comment.dict())
    db.add(db_comment)
    db.commit()
    db.refresh(db_comment)
    return db_comment


# --- MENTAL HEALTH FEATURE ROUTES ---

@app.post("/moods/", response_model=MoodEntryResponse, status_code=status.HTTP_201_CREATED, tags=["Mental Health Tracker"])
def log_mood(mood: MoodEntryCreate, db: Session = Depends(get_db)):
    """Log a user's daily mood score and optional notes."""
    if not 1 <= mood.mood_score <= 10:
        raise HTTPException(status_code=400, detail="Mood score must be between 1 and 10.")
        
    db_mood = MoodEntry(**mood.dict())
    db.add(db_mood)
    db.commit()
    db.refresh(db_mood)
    return db_mood

@app.get("/moods/{user_id}", response_model=List[MoodEntryResponse], tags=["Mental Health Tracker"])
def get_mood_history(user_id: int, db: Session = Depends(get_db)):
    """Retrieve the mood history for a specific user."""
    moods = db.query(MoodEntry).filter(MoodEntry.user_id == user_id).order_by(MoodEntry.entry_date.desc()).all()
    return moods

@app.post("/chats/start", tags=["AI Chatbot"])
def start_chat_session(chat: ChatSessionCreate, db: Session = Depends(get_db)):
    """Start and log the initial message of an AI chat session."""
    # NOTE: The actual AI call would happen here, but for now, we just log the session start.
    db_session = ChatSession(
        user_id=chat.user_id,
        topic=chat.topic,
        log_content=chat.log_content,
        # ai_summary would be updated later or by the AI processing service
    )
    db.add(db_session)
    db.commit()
    db.refresh(db_session)
    return {"message": "Chat session started and logged successfully.", "session_id": db_session.id}

@app.get("/resources/", response_model=List[ResourceResponse], tags=["Resources"])
def list_resources(db: Session = Depends(get_db)):
    """List verified mental health resources (hotlines, therapists, articles)."""
    resources = db.query(Resource).filter(Resource.is_verified == True).all()
    return resources

# --- SETUP INSTRUCTIONS ---
# To run this file:
# 1. Install dependencies: pip install fastapi uvicorn sqlalchemy pydantic passlib[bcrypt] psycopg2-binary
# 2. Update the DATABASE_URL with your PostgreSQL connection details.
# 3. UNCOMMENT the line 'Base.metadata.create_all(bind=engine)' to create your tables once.
# 4. Run the server: uvicorn app:app --reload

# Placeholder for running setup (keep commented out after initial run)
# Base.metadata.create_all(bind=engine)
from fastapi.middleware.cors import CORSMiddleware
# ...
app = FastAPI(...)

# ADD THIS BLOCK
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # Change this to your frontend URL in production!
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

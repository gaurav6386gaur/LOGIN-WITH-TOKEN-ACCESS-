# main.py - JWT Fixed Version
from fastapi import FastAPI, HTTPException, Depends, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import create_engine, Column, Integer, String, DateTime, ForeignKey, Boolean, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session, relationship
from passlib.context import CryptContext
import jwt  # Changed: Using PyJWT instead of python-jose
from datetime import datetime, timedelta
from pydantic import BaseModel, EmailStr
from typing import Optional, List
import uvicorn

# Database setup
SQLALCHEMY_DATABASE_URL = "sqlite:///./auth_system.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# Security
SECRET_KEY = "your-secret-key-change-in-production"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
security = HTTPBearer()

# Database Models
class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    full_name = Column(String, nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    user_firms = relationship("UserFirm", back_populates="user")

class Firm(Base):
    __tablename__ = "firms"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    description = Column(Text)
    address = Column(String)
    phone = Column(String)
    email = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)
    created_by = Column(Integer, ForeignKey("users.id"))
    
    user_firms = relationship("UserFirm", back_populates="firm")

class UserFirm(Base):
    __tablename__ = "user_firms"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    firm_id = Column(Integer, ForeignKey("firms.id"))
    role = Column(String, default="member")
    joined_at = Column(DateTime, default=datetime.utcnow)
    
    user = relationship("User", back_populates="user_firms")
    firm = relationship("Firm", back_populates="user_firms")

# Create tables
Base.metadata.create_all(bind=engine)

# Pydantic Models
class UserCreate(BaseModel):
    email: EmailStr
    password: str
    full_name: str

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class UserResponse(BaseModel):
    id: int
    email: str
    full_name: str
    is_active: bool
    created_at: datetime
    
    class Config:
        from_attributes = True


class FirmCreate(BaseModel):
    name: str
    description: Optional[str] = None
    address: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None

class FirmResponse(BaseModel):
    id: int
    name: str
    description: Optional[str]
    address: Optional[str]
    phone: Optional[str]
    email: Optional[str]
    created_at: datetime
    created_by: int
    
    class Config:
        from_attributes = True

class Token(BaseModel):
    access_token: str
    token_type: str

# FastAPI app
app = FastAPI(title="Token Authentication System")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Database dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Auth functions
def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password):
    return pwd_context.hash(password)

def get_user_by_email(db: Session, email: str):
    return db.query(User).filter(User.email == email).first()

def authenticate_user(db: Session, email: str, password: str):
    user = get_user_by_email(db, email)
    if not user or not verify_password(password, user.hashed_password):
        return False
    return user

def create_access_token(data: dict):
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security), db: Session = Depends(get_db)):
    try:
        payload = jwt.decode(credentials.credentials, SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("sub")
        if email is None:
            raise HTTPException(status_code=401, detail="Invalid token")
    except jwt.PyJWTError:  # Changed: Using PyJWT exception
        raise HTTPException(status_code=401, detail="Invalid token")
    
    user = get_user_by_email(db, email=email)
    if user is None:
        raise HTTPException(status_code=401, detail="User not found")
    return user

# Routes
@app.post("/register", response_model=UserResponse)
def register(user: UserCreate, db: Session = Depends(get_db)):
    if get_user_by_email(db, user.email):
        raise HTTPException(status_code=400, detail="Email already registered")
    
    db_user = User(
        email=user.email,
        hashed_password=get_password_hash(user.password),
        full_name=user.full_name
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

@app.post("/login", response_model=Token)
def login(user_credentials: UserLogin, db: Session = Depends(get_db)):
    user = authenticate_user(db, user_credentials.email, user_credentials.password)
    if not user:
        raise HTTPException(status_code=401, detail="Incorrect email or password")
    
    access_token = create_access_token(data={"sub": user.email})
    return {"access_token": access_token, "token_type": "bearer"}

@app.get("/profile", response_model=UserResponse)
def get_profile(current_user: User = Depends(get_current_user)):
    return current_user

@app.post("/firms", response_model=FirmResponse)
def create_firm(firm: FirmCreate, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    db_firm = Firm(**firm.dict(), created_by=current_user.id)
    db.add(db_firm)
    db.commit()
    db.refresh(db_firm)
    
    # Add user as admin
    user_firm = UserFirm(user_id=current_user.id, firm_id=db_firm.id, role="admin")
    db.add(user_firm)
    db.commit()
    
    return db_firm

@app.get("/firms", response_model=List[FirmResponse])
def get_firms(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    user_firms = db.query(UserFirm).filter(UserFirm.user_id == current_user.id).all()
    firm_ids = [uf.firm_id for uf in user_firms]
    return db.query(Firm).filter(Firm.id.in_(firm_ids)).all()

@app.post("/logout")
def logout(current_user: User = Depends(get_current_user)):
    return {"message": "Logged out successfully"}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
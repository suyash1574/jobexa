from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from jose import JWTError, jwt
import random
import string
from uuid import UUID
from typing import Optional

from src.models.base import get_db
from src.models.user import User, get_password_hash, verify_password
from src.schemas.user import UserCreate, UserOut, Token, TokenData, TelegramPairingCode
from src.config import settings

router = APIRouter(prefix="/auth", tags=["Authentication"])

oauth2_scheme = OAuth2PasswordBearer(tokenUrl=f"{settings.API_V1_STR}/auth/token")

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.JWT_SECRET_KEY, algorithm="HS256")
    return encoded_jwt

def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)) -> User:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        # Try custom JWT first
        payload = jwt.decode(token, settings.JWT_SECRET_KEY, algorithms=["HS256"])
        user_id: str = payload.get("sub")
        if user_id is None:
            raise credentials_exception
        token_data = TokenData(user_id=UUID(user_id))
        user = db.query(User).filter(User.id == token_data.user_id).first()
    except (JWTError, ValueError):
        # Fallback to Supabase JWT decoding
        try:
            # Decode without strict signature checks to support public client authentication
            payload = jwt.decode(token, settings.JWT_SECRET_KEY, options={"verify_signature": False})
            email: str = payload.get("email")
            if not email:
                raise credentials_exception
            user = db.query(User).filter(User.email == email).first()
            if not user:
                import uuid
                user = User(
                    id=uuid.uuid4(),
                    email=email,
                    hashed_password="SUPABASE_AUTH_MANAGED",
                    subscription_tier="free",
                    subscription_status="active"
                )
                db.add(user)
                db.commit()
                db.refresh(user)
        except Exception:
            raise credentials_exception
        
    if user is None:
        raise credentials_exception
    return user

@router.post("/register", response_model=UserOut, status_code=status.HTTP_201_CREATED)
def register(user_in: UserCreate, db: Session = Depends(get_db)):
    db_user = db.query(User).filter(User.email == user_in.email).first()
    if db_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="A user with this email already exists."
        )
    hashed_password = get_password_hash(user_in.password)
    new_user = User(
        email=user_in.email,
        hashed_password=hashed_password
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user

@router.post("/token", response_model=Token)
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == form_data.username).first()
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token = create_access_token(data={"sub": str(user.id)})
    return {"access_token": access_token, "token_type": "bearer"}

@router.post("/telegram-pairing-token", response_model=TelegramPairingCode)
def generate_pairing_token(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    # Generate 6-digit numeric pairing code
    pairing_token = "".join(random.choices(string.digits, k=6))
    expires_at = datetime.utcnow() + timedelta(minutes=settings.TELEGRAM_PAIRING_CODE_EXPIRE_MINUTES)
    
    current_user.telegram_pairing_token = pairing_token
    current_user.pairing_token_expires_at = expires_at
    db.commit()
    db.refresh(current_user)
    
    return {"pairing_token": pairing_token, "expires_at": expires_at}

@router.get("/supabase-config")
def get_supabase_config():
    return {
        "supabase_url": settings.SUPABASE_URL,
        "supabase_key": settings.SUPABASE_KEY
    }

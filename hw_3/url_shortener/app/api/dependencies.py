from url_shortener.app.db.session import SessionLocal
from fastapi import Depends
from sqlalchemy.orm import Session
from fastapi.security import OAuth2PasswordBearer
from url_shortener.app.core.config import REDIS_URL
import redis

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    # Импортируем вспомогательную функцию из auth
    from url_shortener.app.api.routers.auth import get_current_user_from_token
    return get_current_user_from_token(token, db)

def get_redis():
    return redis.Redis.from_url(REDIS_URL)
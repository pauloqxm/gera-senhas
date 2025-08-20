import uuid
from typing import Optional
from passlib.context import CryptContext
from sqlalchemy.orm import Session
from db import User

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def hash_password(password: str) -> str:
    return pwd_context.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

def create_user(db: Session, email: str, name: str, password: str, is_admin: bool=False, plan: str="free") -> User:
    u = User(
        id=str(uuid.uuid4()),
        email=email.strip().lower(),
        name=name.strip(),
        hashed_password=hash_password(password),
        is_admin=is_admin,
        plan=plan,
    )
    db.add(u)
    db.commit()
    db.refresh(u)
    return u

def get_user_by_email(db: Session, email: str) -> Optional[User]:
    return db.query(User).filter(User.email == email.strip().lower()).first()

def authenticate(db: Session, email: str, password: str) -> Optional[User]:
    u = get_user_by_email(db, email)
    if not u:
        return None
    if not verify_password(password, u.hashed_password):
        return None
    return u

from fastapi import HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert

from hashing import Hash
from models import *

def check_item(db: Session, name: str):
    return db.query(Item).filter(Item.name == name).first()

def check_username(db: Session, username: str):
    return db.query(Customer).filter(Customer.username == username).first()

def get_item_id(db: Session, item_name: str):
    return db.query(Item).filter(Item.name == item_name).first()

def authenticate(db: Session, username: str, password: str):
    user = check_username(db, username)

    if not user: raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Incorrect username or password")
    if not Hash.verify(user.password, password): raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Incorrect username or password")

    return user


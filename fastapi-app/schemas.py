from re import I
from pydantic import BaseModel
from typing import List, Optional

class Cart(BaseModel):
    order_id:int
    cid:int
    iid:int
    quantity:int

    class Config:
        orm_mode = True

class Item(BaseModel):
    id:int
    name:str
    description:str

    class Config:
        orm_mode = True

class Customer(BaseModel):
    id: int
    username: str
    password: str

    cart = {}
    class Config:
        orm_mode = True

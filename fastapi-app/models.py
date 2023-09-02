from database import Base
from sqlalchemy import ForeignKey, String, Integer, Text, Column, Table, PrimaryKeyConstraint
from sqlalchemy.orm import relationship

class Cart(Base):
    __tablename__ = "cart"
    cart_id = Column(String, primary_key=True)
    cid = Column(ForeignKey("customer.id"))
    iid = Column(ForeignKey("item.id"))
    quantity = Column(Integer, default=1)
    item = relationship("Item")
    PrimaryKeyConstraint('cart_id', 'cart_pkey')


class Item(Base):
    __tablename__ = 'item'
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(255), nullable=False, unique=True)
    description = Column(Text)

    def __repr__(self):
        return f"Item name={self.name} price={self.price}"

class Customer(Base):
    __tablename__ = 'customer'
    id = Column(Integer, primary_key=True, autoincrement=True)
    username = Column(String(255), nullable=False, unique=True)
    password = Column(String(255), nullable=False)
    items = relationship("Cart")

    def __repr__(self):
        return f"user username={self.username} password={self.password}"

from database import Base, engine
from models import Item, Customer

print("Creating database...")

Base.metadata.create_all(engine)

# engine.execute(Item.insert(), name="Milk", description="Cow milk")
# engine.execute(Item.insert(), name="Cookies", description="With chocolate")
# engine.execute(Item.insert(), name="Banana", description="Yellow fruit")
# engine.execute(Item.insert(), name="Croissant", description="Bistrooo")

# engine.execute(Customer.insert(), username="loukas", password="loukas")

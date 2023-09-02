from fastapi import FastAPI, HTTPException, Request, Response, Form, status, Depends
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from hashing import Hash

from schemas import Item, Customer
from database import SessionLocal
from typing import List, Dict

from starlette.middleware.sessions import SessionMiddleware

import models
import utils


app = FastAPI()

app.add_middleware(SessionMiddleware, secret_key="4ec57ae29a0f5ff3a78c932c7b106c3723bf69acce4df5ede8e384d097b81da6")
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

db = SessionLocal()

async def get_current_user(request: Request):
    user = utils.check_username(db, request.session.get('username'))
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authorized")
    return user

@app.get('/home', response_class=HTMLResponse)
async def index(request: Request):
    return templates.TemplateResponse("home.html", {"request": request})

@app.get('/login', response_class=HTMLResponse)
def visit_login(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})

@app.post('/login')
def login(request: Request, username:str=Form(), password:str=Form()):
    user = utils.authenticate(db, username, password)
    request.session['username'] = user.username
    request.session['cart'] = {}
    request.session['cart_ids'] = []
    return RedirectResponse(request.url_for('get_items'), status_code=303)

@app.get('/logout')
def logout(request: Request):
    request.session.pop("username")
    request.session.pop("cart")
    request.session.pop("cart_ids")
    return RedirectResponse(request.url_for('index'))

@app.get('/items', response_model = List[Item], response_class=HTMLResponse)
def get_items(request: Request, current_user = Depends(get_current_user)):
    items = db.query(models.Item).all()
    return templates.TemplateResponse("items.html", {"request": request, "items":items, "user": current_user})

# 
# Method for adding products of cart, in temporary session. 
# Not working with JMeter.
#
@app.post('/items/add/{item_id}', response_class=HTMLResponse, status_code=200)
def add_item(request: Request, item_id: str, quantity : int = Form(title="quantity"), current_user = Depends(get_current_user)):
    if not request.session.get('cart').get(item_id):
        request.session.get('cart')[item_id] = 0 + quantity
    else:
        request.session.get('cart')[item_id] += quantity
    return RedirectResponse(request.url_for('get_items'), status_code=303)

#
# Method for removing products of cart, from temporary session.
# Not working with JMeter.
#
@app.post('/items/remove/{item_id}', status_code=200)
def remove_item(request: Request, item_id: str, quantity: int = Form(title="quantity"), current_user = Depends(get_current_user)):
    if not request.session.get('cart').get(item_id):
        return RedirectResponse(request.url_for('get_items'), status_code=303)
    else:
        cur_quantity = request.session.get('cart').get(item_id)
        if cur_quantity >= quantity:
            request.session.get('cart')[item_id] -= quantity
    return RedirectResponse(request.url_for('get_items'), status_code=303)

# POST method adds all products in one transaction in database.
# Commented-out LOC contain interaction with session

@app.post('/purchase', status_code=201)
# async def purchase(request: Request, current_user = Depends(get_current_user)):
async def purchase(request: Request):
    # [request.session['cart_ids'].append(i) for i in request.session.get('cart').keys() if i]

    form_data = dict(await request.form())
    cust_id = form_data.pop("cust_id")

    with db.no_autoflush:
        for item_id, q in form_data.items():
            if q != "0":
                new_order = models.Cart(cart_id=(cust_id+str(item_id)), cid=cust_id, iid=item_id, quantity=q)
                db.merge(new_order)

    db.commit()
    # request.session.pop('cart')
    # request.session['cart'] = {}
    # request.session['cart_ids'].clear()
    return RedirectResponse(request.url_for('get_items'), status_code=303)

@app.get('/register', response_class=HTMLResponse)
def visit_register(request: Request):
    return templates.TemplateResponse("register.html", {"request": request})

@app.post('/register', response_model= Customer, status_code=status.HTTP_201_CREATED)
async def register_user(request: Request, username: str = Form(title="username"), password: str = Form(title="password")):
    if utils.check_username(db, username) is not None:
        raise HTTPException(status_code=400, detail="Username is being used")

    new_user = models.Customer(username = username, password = Hash.bcrypt(password))
    db.add(new_user)
    db.commit()
    
    return RedirectResponse(request.url_for('visit_login'), status_code=status.HTTP_303_SEE_OTHER)
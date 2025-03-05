from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlalchemy import create_engine, Column, Integer, String 
from sqlalchemy.orm import declarative_base
from sqlalchemy.orm import sessionmaker, Session
import uvicorn
import time
from typing import List

# Database setup
DATABASE_URL = "sqlite:///./test.db"
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

# Rate limiter (basic example)
REQUESTS = {}
RATE_LIMIT = 5  # max requests per minute

def rate_limiter(client_ip: str):
    current_time = time.time()
    if client_ip not in REQUESTS:
        REQUESTS[client_ip] = []
    REQUESTS[client_ip] = [t for t in REQUESTS[client_ip] if current_time - t < 60]
    if len(REQUESTS[client_ip]) >= RATE_LIMIT:
        raise HTTPException(status_code=429, detail="Rate limit exceeded")
    REQUESTS[client_ip].append(current_time)

# Model
class Item(Base):
    __tablename__ = "items"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    description = Column(String)

Base.metadata.create_all(bind=engine)

# Dependency

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

app = FastAPI()

# Authentication (dummy implementation, replace with a real auth system)
def fake_decode_token(token: str):
    if token == "secret-token":
        return {"sub": "user1"}
    return None

def get_current_user(token: str = Depends(oauth2_scheme)):
    user = fake_decode_token(token)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return user

@app.post("/token")
def login(form_data: OAuth2PasswordRequestForm = Depends()):
    if form_data.username == "admin" and form_data.password == "password":
        return {"access_token": "secret-token", "token_type": "bearer"}
    raise HTTPException(status_code=400, detail="Invalid credentials")

# CRUD operations
@app.post("/items/", response_model=dict, dependencies=[Depends(get_current_user)])
def create_item(name: str, description: str, db: Session = Depends(get_db)):
    new_item = Item(name=name, description=description)
    db.add(new_item)
    db.commit()
    db.refresh(new_item)
    return {"id": new_item.id, "name": new_item.name, "description": new_item.description}

@app.get("/items/", response_model=List[dict], dependencies=[Depends(get_current_user)])
def read_items(db: Session = Depends(get_db)):
    items = db.query(Item).all()
    return [{"id": item.id, "name": item.name, "description": item.description} for item in items]

@app.get("/items/{item_id}", response_model=dict, dependencies=[Depends(get_current_user)])
def read_item(item_id: int, db: Session = Depends(get_db)):
    item = db.query(Item).filter(Item.id == item_id).first()
    if item is None:
        raise HTTPException(status_code=404, detail="Item not found")
    return {"id": item.id, "name": item.name, "description": item.description}

@app.put("/items/{item_id}", response_model=dict, dependencies=[Depends(get_current_user)])
def update_item(item_id: int, name: str, description: str, db: Session = Depends(get_db)):
    item = db.query(Item).filter(Item.id == item_id).first()
    if item is None:
        raise HTTPException(status_code=404, detail="Item not found")
    item.name = name
    item.description = description
    db.commit()
    return {"id": item.id, "name": item.name, "description": item.description}

@app.delete("/items/{item_id}", response_model=dict, dependencies=[Depends(get_current_user)])
def delete_item(item_id: int, db: Session = Depends(get_db)):
    item = db.query(Item).filter(Item.id == item_id).first()
    if item is None:
        raise HTTPException(status_code=404, detail="Item not found")
    db.delete(item)
    db.commit()
    return {"message": "Item deleted"}

# CORS Configuration (allow only trusted origins)
from fastapi.middleware.cors import CORSMiddleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # Change as needed
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)

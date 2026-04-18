# backend/main.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from backend.db.database import engine
from backend.db.models import Base

Base.metadata.create_all(bind=engine)

app = FastAPI(title="World Cup Predictor API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def health():
    return {"status": "ok"}


from backend.routes.predictions import router as predictions_router
app.include_router(predictions_router)

from backend.routes.users import router as users_router
app.include_router(users_router)

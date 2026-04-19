# backend/main.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from backend.db.database import engine
from backend.db.models import Base

Base.metadata.create_all(bind=engine)

app = FastAPI(title="World Cup Predictor API", version="1.0.0")

import re
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request as StarletteRequest

ALLOWED_ORIGINS = re.compile(
    r"^(http://localhost:\d+|https://[\w-]+-amrabujabal35-2594s-projects\.vercel\.app|https://frontend-nine-alpha-56\.vercel\.app)$"
)

class DynamicCORSMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: StarletteRequest, call_next):
        origin = request.headers.get("origin", "")
        response = await call_next(request)
        if ALLOWED_ORIGINS.match(origin):
            response.headers["Access-Control-Allow-Origin"] = origin
            response.headers["Access-Control-Allow-Credentials"] = "true"
            response.headers["Access-Control-Allow-Methods"] = "*"
            response.headers["Access-Control-Allow-Headers"] = "*"
        return response

app.add_middleware(DynamicCORSMiddleware)

# Preflight handler
@app.options("/{rest_of_path:path}")
async def preflight(rest_of_path: str, request: StarletteRequest):
    from fastapi import Response
    origin = request.headers.get("origin", "")
    headers = {}
    if ALLOWED_ORIGINS.match(origin):
        headers = {
            "Access-Control-Allow-Origin": origin,
            "Access-Control-Allow-Methods": "*",
            "Access-Control-Allow-Headers": "*",
            "Access-Control-Allow-Credentials": "true",
        }
    return Response(status_code=204, headers=headers)


@app.get("/health")
def health():
    return {"status": "ok"}


from backend.routes.predictions import router as predictions_router
app.include_router(predictions_router)

from backend.routes.users import router as users_router
app.include_router(users_router)

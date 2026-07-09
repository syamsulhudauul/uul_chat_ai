from fastapi import Depends, FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.auth import AuthenticatedUser, verify_jwt
from app.config import settings
from app.routes.chat import router as chat_router
from app.routes.voice import router as voice_router

app = FastAPI(title="uul_chat_ai backend")
app.include_router(chat_router)
app.include_router(voice_router)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def health() -> dict:
    return {"status": "ok"}


@app.get("/me")
def me(user: AuthenticatedUser = Depends(verify_jwt)) -> dict:
    return {"user_id": user.user_id, "email": user.email}

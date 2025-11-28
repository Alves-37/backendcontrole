from datetime import datetime, timedelta
from typing import List
import os

from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from db import get_db, engine, Base, AsyncSessionLocal
from models import User


app = FastAPI(
    title="NeoControle Auth Backend",
    description="Serviço de autenticação central para NeoControle/NeoPDV",
    version="0.1.0",
)

# CORS para permitir o frontend acessar este backend
app.add_middleware(
  CORSMiddleware,
  allow_origins=[
    "http://localhost:5173",
    "http://127.0.0.1:5173",
    "https://neocontrole.vercel.app",
  ],
  allow_credentials=True,
  allow_methods=["*"],
  allow_headers=["*"],
)


# Modelos de requisição/resposta
class LoginRequest(BaseModel):
    username: str
    password: str


class Estabelecimento(BaseModel):
    id: str
    nome: str
    url_front: str


class LoginResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    usuario: str
    expires_at: datetime
    estabelecimentos: List[Estabelecimento]


@app.on_event("startup")
async def on_startup() -> None:
  """Garantir que a tabela auth_users exista e criar usuários padrão."""
  # Criar tabelas
  async with engine.begin() as conn:
    await conn.run_sync(Base.metadata.create_all)

  # Garantir usuários padrão
  async with AsyncSessionLocal() as session:
    # Nelson / Nelson4
    result = await session.execute(select(User).where(User.username == "Nelson"))
    nelson = result.scalar_one_or_none()
    if not nelson:
      nelson = User(username="Nelson", password="Nelson4", nome="Nelson", is_active=True)
      session.add(nelson)

    # Neotrix / 842384
    result = await session.execute(select(User).where(User.username == "Neotrix"))
    neotrix = result.scalar_one_or_none()
    if not neotrix:
      neotrix = User(username="Neotrix", password="842384", nome="Neotrix Tecnologias", is_active=True)
      session.add(neotrix)

    await session.commit()


@app.post("/auth/login", response_model=LoginResponse)
async def login(data: LoginRequest, db: AsyncSession = Depends(get_db)):
    # Por enquanto a senha é comparada em texto simples.
    # Depois podemos trocar para hash (bcrypt, etc.).
    result = await db.execute(select(User).where(User.username == data.username))
    user: User | None = result.scalar_one_or_none()
    if not user or not user.is_active or user.password != data.password:
        raise HTTPException(status_code=401, detail="Credenciais inválidas")

    # Por enquanto o token é apenas uma string simples.
    # Depois podemos trocar para JWT com segredo compartilhado.
    token = f"fake-token-{user.username}-{int(datetime.utcnow().timestamp())}"

    estabelecimentos = [
        Estabelecimento(id="neopdv1", nome="NeoPDV 1", url_front="https://neopdv1.vercel.app"),
        Estabelecimento(id="neopdv2", nome="NeoPDV 2", url_front="https://neopdv2.vercel.app"),
        Estabelecimento(id="neopdv3", nome="NeoPDV 3", url_front="https://neopdv3.vercel.app"),
        Estabelecimento(id="neopdv4", nome="NeoPDV 4", url_front="https://neopdv4.vercel.app"),
    ]

    return LoginResponse(
        access_token=token,
        usuario=user.nome,
        expires_at=datetime.utcnow() + timedelta(hours=8),
        estabelecimentos=estabelecimentos,
    )


@app.get("/")
async def root():
    return {"message": "NeoControle Auth Backend running"}


if __name__ == "__main__":
  import uvicorn

  port = int(os.getenv("PORT", "8000"))
  uvicorn.run("main:app", host="0.0.0.0", port=port)

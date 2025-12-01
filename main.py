from datetime import datetime, timedelta
from typing import List
import os

from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from db import get_db, engine, Base, AsyncSessionLocal
from models import User, Establishment


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


class UserUpdate(BaseModel):
    nome: str | None = None
    password: str | None = None


@app.on_event("startup")
async def on_startup() -> None:
  """Garantir tabelas e dados padrão (usuários e estabelecimentos)."""
  # Criar tabelas
  async with engine.begin() as conn:
    await conn.run_sync(Base.metadata.create_all)

  # Garantir usuários e estabelecimentos padrão
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

    # Estabelecimentos padrão (se a tabela estiver vazia)
    result = await session.execute(select(Establishment))
    existentes = result.scalars().all()
    if not existentes:
      defaults = [
        Establishment(id="neopdv1", nome="NeoPDV 1", url_front="https://neopdv1.vercel.app"),
        Establishment(id="neopdv2", nome="NeoPDV 2", url_front="https://neopdv2.vercel.app"),
        Establishment(id="neopdv3", nome="NeoPDV 3", url_front="https://neopdv3.vercel.app"),
        Establishment(id="neopdv4", nome="NeoPDV 4", url_front="https://neopdv4.vercel.app"),
      ]
      session.add_all(defaults)

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

    # Carregar estabelecimentos do banco
    result = await db.execute(select(Establishment))
    estabs_db = result.scalars().all()

    if estabs_db:
      estabelecimentos = [
        Estabelecimento(
          id=e.id,
          nome=e.nome,
          url_front=e.url_front,
        )
        for e in estabs_db
      ]
    else:
      # Fallback em caso de banco vazio (não deveria ocorrer após startup)
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


class EstabelecimentoUpdate(BaseModel):
    nome: str


@app.put("/estabelecimentos/{estab_id}", response_model=Estabelecimento)
async def atualizar_estabelecimento(estab_id: str, data: EstabelecimentoUpdate, db: AsyncSession = Depends(get_db)):
    # Atualiza apenas o nome do estabelecimento no banco
    est = await db.get(Establishment, estab_id)
    if not est:
        raise HTTPException(status_code=404, detail="Estabelecimento não encontrado")

    est.nome = data.nome
    await db.commit()
    await db.refresh(est)

    return Estabelecimento(id=est.id, nome=est.nome, url_front=est.url_front)


@app.put("/users/{username}")
async def atualizar_usuario(username: str, data: UserUpdate, db: AsyncSession = Depends(get_db)):
    """Atualiza nome e/ou senha de um usuário do auth (sem autenticação forte por enquanto)."""
    result = await db.execute(select(User).where(User.username == username))
    user: User | None = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="Usuário não encontrado")

    if data.nome is not None and data.nome.strip():
        user.nome = data.nome.strip()
    if data.password is not None and data.password.strip():
        # Por enquanto senha em texto simples; depois trocar para hash
        user.password = data.password

    await db.commit()

    return {
        "username": user.username,
        "nome": user.nome,
        "is_active": user.is_active,
    }


@app.get("/")
async def root():
    return {"message": "NeoControle Auth Backend running"}


if __name__ == "__main__":
  import uvicorn

  port = int(os.getenv("PORT", "8000"))
  uvicorn.run("main:app", host="0.0.0.0", port=port)

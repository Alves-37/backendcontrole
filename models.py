from sqlalchemy import Column, String, Boolean
from sqlalchemy.dialects.postgresql import UUID
import uuid

from db import Base


class User(Base):
  __tablename__ = "auth_users"

  id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
  username = Column(String(50), unique=True, nullable=False, index=True)
  password = Column(String(255), nullable=False)  # por enquanto texto simples; depois podemos trocar para hash
  nome = Column(String(100), nullable=False)
  is_active = Column(Boolean, default=True, nullable=False)

import asyncio

from sqlalchemy import text

from db import engine


async def reset_auth_db() -> None:
    print("Conectando ao banco de dados do auth...")
    async with engine.begin() as conn:
        # TRUNCATE remove todos os registros e reinicia IDs; CASCADE garante integridade se houver FKs
        await conn.execute(text("TRUNCATE TABLE auth_estabelecimentos, auth_users RESTART IDENTITY CASCADE;"))
    print("Tabelas auth_users e auth_estabelecimentos foram limpas com sucesso.")
    print("Ao reiniciar o serviço FastAPI, os usuários e estabelecimentos padrão serão recriados pelo on_startup.")


if __name__ == "__main__":
    asyncio.run(reset_auth_db())

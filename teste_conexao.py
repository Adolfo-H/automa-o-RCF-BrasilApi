from sqlalchemy import create_engine, text

from app.config import DATABASE_URL

engine = create_engine(DATABASE_URL)

with engine.connect() as conn:
    resultado = conn.execute(text("SELECT version();"))
    for linha in resultado:
        print(linha[0])

print("Conexao realizada com sucesso!")

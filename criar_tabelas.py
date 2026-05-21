from sqlalchemy import text

from app.database import engine
from app.models import Base

Base.metadata.create_all(engine)

with engine.begin() as conn:
    conn.execute(
        text(
            "ALTER TABLE leads_empresas "
            "ADD COLUMN IF NOT EXISTS natureza_juridica VARCHAR(120)"
        )
    )
    conn.execute(
        text(
            "ALTER TABLE leads_empresas "
            "ALTER COLUMN natureza_juridica TYPE VARCHAR(120)"
        )
    )

with engine.begin() as conn:
    conn.execute(
        text("ALTER TABLE leads_empresas ADD COLUMN IF NOT EXISTS whatsapp_valido BOOLEAN")
    )
print("Coluna whatsapp_valido adicionada com sucesso!")

print("Tabelas criadas ou atualizadas com sucesso!")

import pandas as pd
from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert

from app.database import engine
from app.models import LeadEmpresa


def salvar_leads(df: pd.DataFrame) -> int:
    if df.empty:
        return 0

    registros = df.to_dict(orient="records")

    with engine.begin() as conn:
        stmt = insert(LeadEmpresa).values(registros)
        stmt = stmt.on_conflict_do_nothing(index_elements=["cnpj"])
        resultado = conn.execute(stmt)
        return resultado.rowcount or 0


def buscar_cnpjs_ja_salvos(cnpjs: list[str]) -> set[str]:
    if not cnpjs:
        return set()

    with engine.connect() as conn:
        stmt = select(LeadEmpresa.cnpj).where(LeadEmpresa.cnpj.in_(cnpjs))
        rows = conn.execute(stmt).fetchall()

    return {row[0] for row in rows}

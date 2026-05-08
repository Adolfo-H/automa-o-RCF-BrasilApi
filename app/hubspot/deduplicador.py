from sqlalchemy import select

from app.database import engine
from app.models import HubspotEmpresa


def buscar_dominios_hubspot() -> set:

    with engine.connect() as conn:

        stmt = select(HubspotEmpresa.dominio)

        rows = conn.execute(stmt).fetchall()

    return {row[0] for row in rows if row[0]}
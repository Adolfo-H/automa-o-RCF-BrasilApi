from datetime import datetime

from sqlalchemy import DateTime, Integer, Numeric, String
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


class LeadEmpresa(Base):
    __tablename__ = "leads_empresas"

    id: Mapped[int] = mapped_column(primary_key=True)
    cnpj: Mapped[str] = mapped_column(String(14), unique=True, nullable=False)
    razao_social: Mapped[str] = mapped_column(String(255))
    nome_fantasia: Mapped[str | None]
    cnae_principal: Mapped[str | None]
    natureza_juridica: Mapped[str | None] = mapped_column(String(120))
    uf: Mapped[str | None]
    municipio: Mapped[str | None]
    porte: Mapped[int | None]
    telefone: Mapped[str | None]
    email: Mapped[str | None]
    capital_social: Mapped[float | None] = mapped_column(Numeric(18, 2))
    socios: Mapped[str | None]
    origem_match: Mapped[str | None] = mapped_column(String(20))          # 'PRINCIPAL' ou 'SECUNDARIO'
    cnae_match_secundario: Mapped[str | None] = mapped_column(String(255)) # CNAE do filtro achado nos secundários
    created_at: Mapped[datetime] = mapped_column(default=datetime.utcnow)
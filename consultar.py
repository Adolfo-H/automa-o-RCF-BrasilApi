from rich.console import Console
from rich.table import Table
from sqlalchemy import text

from app.database import engine

console = Console()


def listar_todos():
    with engine.connect() as conn:
        rows = conn.execute(
            text(
                "SELECT cnpj, razao_social, uf, municipio, email, telefone "
                "FROM leads_empresas ORDER BY created_at DESC"
            )
        ).fetchall()

    tabela = Table(title=f"Leads ({len(rows)} encontrados)")
    tabela.add_column("CNPJ")
    tabela.add_column("Razao Social")
    tabela.add_column("UF")
    tabela.add_column("Municipio")
    tabela.add_column("Email")
    tabela.add_column("Telefone")

    for row in rows:
        tabela.add_row(*[str(c or "") for c in row])

    console.print(tabela)


def buscar(termo: str):
    with engine.connect() as conn:
        rows = conn.execute(
            text(
                "SELECT cnpj, razao_social, uf, municipio, email, telefone "
                "FROM leads_empresas "
                "WHERE razao_social ILIKE :t OR municipio ILIKE :t OR uf ILIKE :t "
                "ORDER BY razao_social"
            ),
            {"t": f"%{termo}%"},
        ).fetchall()

    tabela = Table(title=f'Busca por "{termo}" - {len(rows)} resultado(s)')
    tabela.add_column("CNPJ")
    tabela.add_column("Razao Social")
    tabela.add_column("UF")
    tabela.add_column("Municipio")
    tabela.add_column("Email")
    tabela.add_column("Telefone")

    for row in rows:
        tabela.add_row(*[str(c or "") for c in row])

    console.print(tabela)


if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1:
        buscar(" ".join(sys.argv[1:]))
    else:
        listar_todos()

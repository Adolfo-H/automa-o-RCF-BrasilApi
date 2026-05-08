import pandas as pd
from sqlalchemy.dialects.postgresql import insert

from app.database import engine
from app.models import HubspotEmpresa


def extrair_dominio(valor):

    if pd.isna(valor):
        return None

    valor = str(valor).lower().strip()

    valor = valor.replace("http://", "")
    valor = valor.replace("https://", "")
    valor = valor.replace("www.", "")

    return valor.split("/")[0]


# ==================================
# LE EXCEL
# ==================================

df = pd.read_excel(
    "data/hubspot-crm-exports-todos-os-empresas-2026-05-08.xlsx"
)

# ==================================
# CRIA DOMINIO
# ==================================

df["dominio"] = (
    df["Nome de domínio da empresa"]
    .fillna(df["URL do site"])
    .apply(extrair_dominio)
)

# remove vazios
df = df[df["dominio"].notna()]

# ==================================
# PREPARA REGISTROS
# ==================================

registros = []

for _, row in df.iterrows():

    registros.append({
        "nome_empresa": row["Nome da empresa"],
        "dominio": row["dominio"]
    })

# ==================================
# SALVA
# ==================================

with engine.begin() as conn:

    stmt = insert(HubspotEmpresa).values(registros)

    stmt = stmt.on_conflict_do_nothing(
        index_elements=["dominio"]
    )

    conn.execute(stmt)

print("Importação HubSpot concluída.")
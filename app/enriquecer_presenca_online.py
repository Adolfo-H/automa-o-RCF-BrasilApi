import pandas as pd

from sqlalchemy import text

from app.database import engine
from app.enrichment import buscar_presenca_online


def enriquecer_empresas():

    query = """
    SELECT id, razao_social, nome_fantasia
    FROM leads_empresas
    WHERE site IS NULL
    AND linkedin IS NULL
    LIMIT 5
    """

    df = pd.read_sql(query, engine)

    for _, row in df.iterrows():

        nome = (
            row["nome_fantasia"]
            or row["razao_social"]
        )

        enrich = buscar_presenca_online(nome)

        update = text("""
        UPDATE leads_empresas
        SET
            site = :site,
            linkedin = :linkedin,
            tem_site = :tem_site,
            tem_linkedin = :tem_linkedin
        WHERE id = :id
        """)

        dados = {
            "id": row["id"],
            "site": enrich["SITE"],
            "linkedin": enrich["LINKEDIN"],
            "tem_site": enrich["TEM_SITE"],
            "tem_linkedin": enrich["TEM_LINKEDIN"],
        }

        with engine.begin() as conn:
            conn.execute(update, dados)

        print(f"Enriquecido: {nome}")


if __name__ == "__main__":
    enriquecer_empresas()
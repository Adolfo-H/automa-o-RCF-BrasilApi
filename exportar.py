import pandas as pd

from app.database import engine


def exportar_leads(caminho_saida: str = "leads_exportados.xlsx"):
    df = pd.read_sql("SELECT * FROM leads_empresas ORDER BY created_at DESC", engine)
    df.to_excel(caminho_saida, index=False)
    print(f"{len(df)} leads exportados para {caminho_saida}")


if __name__ == "__main__":
    exportar_leads()

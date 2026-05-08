import pandas as pd


def extrair_socios(qsa):

    if not qsa:
        return ""

    nomes = [
        socio.get("nome_socio", "")
        for socio in qsa
    ]

    return " | ".join(filter(None, nomes))


def extrair_dominio(valor):

    if pd.isna(valor):
        return None

    valor = str(valor).lower().strip()

    # email
    if "@" in valor:
        return valor.split("@")[-1]

    # url
    valor = valor.replace("http://", "")
    valor = valor.replace("https://", "")
    valor = valor.replace("www.", "")

    return valor.split("/")[0]
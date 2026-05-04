import pandas as pd

from app.config import CAPITAL_SOCIAL_ACEITAR_ZERO, CAPITAL_SOCIAL_MINIMO, NATUREZAS_JURIDICAS

COLUNAS_ESTABELECIMENTOS = [
    "CNPJ_BASICO", "CNPJ_ORDEM", "CNPJ_DV",
    "IDENTIFICADOR_MATRIZ_FILIAL", "NOME_FANTASIA",
    "SITUACAO_CADASTRAL", "DATA_SITUACAO_CADASTRAL",
    "MOTIVO_SITUACAO_CADASTRAL", "NOME_CIDADE_EXTERIOR", "PAIS",
    "DATA_INICIO_ATIVIDADE", "CNAE_FISCAL_PRINCIPAL",
    "CNAE_FISCAL_SECUNDARIA", "TIPO_LOGRADOURO", "LOGRADOURO",
    "NUMERO", "COMPLEMENTO", "BAIRRO", "CEP", "UF", "MUNICIPIO",
    "DDD_1", "TELEFONE_1", "DDD_2", "TELEFONE_2",
    "DDD_FAX", "FAX", "CORREIO_ELETRONICO",
    "SITUACAO_ESPECIAL", "DATA_SITUACAO_ESPECIAL",
]

COLUNAS_ESTABELECIMENTOS_USADAS = [
    "CNPJ_BASICO",
    "CNPJ_ORDEM",
    "CNPJ_DV",
    "NOME_FANTASIA",
    "SITUACAO_CADASTRAL",
    "CNAE_FISCAL_PRINCIPAL",
    "UF",
    "CORREIO_ELETRONICO",
]

COLUNAS_EMPRESAS = [
    "CNPJ_BASICO", "RAZAO_SOCIAL", "NATUREZA_JURIDICA",
    "QUALIFICACAO_RESPONSAVEL", "CAPITAL_SOCIAL",
    "PORTE_EMPRESA", "ENTE_FEDERATIVO_RESPONSAVEL",
]


def _capital_social_para_float(serie: pd.Series) -> pd.Series:
    return pd.to_numeric(serie.str.replace(",", ".", regex=False), errors="coerce")


def carregar_base(
    arquivo_estab: str,
    arquivo_empresas: str,
    cnaes=None,
    ufs=None,
    portes=None,
    naturezas_juridicas=None,
) -> pd.DataFrame:
    df_emp = pd.read_csv(
        arquivo_empresas,
        sep=";",
        dtype=str,
        encoding="latin-1",
        header=None,
        names=COLUNAS_EMPRESAS,
        low_memory=False,
        usecols=["CNPJ_BASICO", "PORTE_EMPRESA", "CAPITAL_SOCIAL", "NATUREZA_JURIDICA"],
    )

    porte_numerico = pd.to_numeric(df_emp["PORTE_EMPRESA"], errors="coerce")
    capital_social_numerico = _capital_social_para_float(df_emp["CAPITAL_SOCIAL"])

    if portes is not None:
        df_emp = df_emp[porte_numerico.isin(portes)]
        porte_numerico = porte_numerico.loc[df_emp.index]
        capital_social_numerico = capital_social_numerico.loc[df_emp.index]

    filtro_capital = capital_social_numerico >= CAPITAL_SOCIAL_MINIMO
    if CAPITAL_SOCIAL_ACEITAR_ZERO:
        filtro_capital = filtro_capital | (capital_social_numerico == 0)
    df_emp = df_emp[filtro_capital]

    if naturezas_juridicas is None:
        naturezas_juridicas = NATUREZAS_JURIDICAS
    if naturezas_juridicas:
        df_emp = df_emp[df_emp["NATUREZA_JURIDICA"].isin(naturezas_juridicas)]

    mapa_empresas = (
        df_emp.drop_duplicates("CNPJ_BASICO")
        .set_index("CNPJ_BASICO")[["PORTE_EMPRESA", "CAPITAL_SOCIAL", "NATUREZA_JURIDICA"]]
    )

    partes = []
    leitor = pd.read_csv(
        arquivo_estab,
        sep=";",
        dtype=str,
        encoding="latin-1",
        header=None,
        names=COLUNAS_ESTABELECIMENTOS,
        usecols=COLUNAS_ESTABELECIMENTOS_USADAS,
        chunksize=200_000,
        low_memory=False,
    )

    for chunk in leitor:
        chunk["CNPJ_COMPLETO"] = (
            chunk["CNPJ_BASICO"].str.zfill(8)
            + chunk["CNPJ_ORDEM"].str.zfill(4)
            + chunk["CNPJ_DV"].str.zfill(2)
        )
        if cnaes is not None:
            chunk = chunk[chunk["CNAE_FISCAL_PRINCIPAL"].isin(cnaes)]
        if ufs is not None:
            chunk = chunk[chunk["UF"].isin(ufs)]

        chunk = chunk[chunk["SITUACAO_CADASTRAL"] == "02"]
        chunk = chunk.join(mapa_empresas, on="CNPJ_BASICO", how="left")
        chunk = chunk[chunk["PORTE_EMPRESA"].notna()]

        if not chunk.empty:
            partes.append(chunk)

    if not partes:
        colunas_saida = COLUNAS_ESTABELECIMENTOS_USADAS + [
            "CNPJ_COMPLETO",
            "PORTE_EMPRESA",
            "CAPITAL_SOCIAL",
            "NATUREZA_JURIDICA",
        ]
        return pd.DataFrame(columns=colunas_saida)

    return pd.concat(partes, ignore_index=True)


def filtrar_empresas(df: pd.DataFrame, cnaes, ufs, portes, naturezas_juridicas=None) -> pd.DataFrame:
    porte_numerico = pd.to_numeric(df["PORTE_EMPRESA"], errors="coerce")
    capital_social_numerico = _capital_social_para_float(df["CAPITAL_SOCIAL"])
    filtro_capital = capital_social_numerico >= CAPITAL_SOCIAL_MINIMO

    if CAPITAL_SOCIAL_ACEITAR_ZERO:
        filtro_capital = filtro_capital | (capital_social_numerico == 0)

    if naturezas_juridicas is None:
        naturezas_juridicas = NATUREZAS_JURIDICAS

    filtro_natureza = True
    if naturezas_juridicas:
        filtro_natureza = df["NATUREZA_JURIDICA"].isin(naturezas_juridicas)

    return df[
        (df["CNAE_FISCAL_PRINCIPAL"].isin(cnaes)) &
        (df["UF"].isin(ufs)) &
        (porte_numerico.isin(portes)) &
        filtro_capital &
        filtro_natureza &
        (df["SITUACAO_CADASTRAL"] == "02")
    ].copy()

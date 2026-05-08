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
    "CNAE_FISCAL_SECUNDARIA",   # ← incluído para busca nos secundários
    "UF",
    "CORREIO_ELETRONICO",
]

COLUNAS_EMPRESAS = [
    "CNPJ_BASICO", "RAZAO_SOCIAL", "NATUREZA_JURIDICA",
    "QUALIFICACAO_RESPONSAVEL", "CAPITAL_SOCIAL",
    "PORTE_EMPRESA", "ENTE_FEDERATIVO_RESPONSAVEL",
]


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _capital_social_para_float(serie: pd.Series) -> pd.Series:
    return pd.to_numeric(serie.str.replace(",", ".", regex=False), errors="coerce")


def _extrair_secundarios(valor: str) -> set:
    """
    Transforma a string bruta de CNAEs secundários em um conjunto de strings.

    O campo pode vir de duas formas na base da Receita Federal:
      - Colado de 7 em 7 dígitos : "01113000112101"
      - Separado por espaço/vírgula: "0111300 0112101"

    A função trata os dois casos automaticamente.
    """
    if not valor or pd.isna(valor):
        return set()

    valor = valor.strip()
    if not valor:
        return set()

    # Se contém separadores, usa split
    if " " in valor or "," in valor:
        partes = valor.replace(",", " ").split()
        return {p.strip() for p in partes if p.strip()}

    # Caso contrário, fatia de 7 em 7
    return {valor[i:i + 7] for i in range(0, len(valor), 7) if len(valor[i:i + 7]) == 7}


def _cnae_secundario_match(serie_secundaria: pd.Series, cnaes: set) -> pd.Series:
    """
    Retorna uma máscara booleana: True se qualquer CNAE do filtro
    aparecer na lista de CNAEs secundários da empresa.
    """
    cnaes_str = {str(c) for c in cnaes}
    return serie_secundaria.apply(
        lambda v: bool(_extrair_secundarios(v) & cnaes_str)
    )


def _cnae_secundario_matched(serie_secundaria: pd.Series, cnaes: set) -> pd.Series:
    """
    Retorna qual CNAE do filtro foi encontrado nos secundários.
    Se houver mais de um match, retorna todos separados por '|'.
    Retorna None quando não há match.
    """
    cnaes_str = {str(c) for c in cnaes}

    def encontrar(v):
        matches = _extrair_secundarios(v) & cnaes_str
        return "|".join(sorted(matches)) if matches else None

    return serie_secundaria.apply(encontrar)


def _adicionar_colunas_match(chunk: pd.DataFrame, cnaes: set) -> pd.DataFrame:
    """
    Acrescenta ao DataFrame duas colunas de diagnóstico:

    - ORIGEM_MATCH:
        'PRINCIPAL'  → o CNAE do filtro está no CNAE principal
        'SECUNDARIO' → o CNAE do filtro só aparece nos secundários

    - CNAE_MATCH_SECUNDARIO:
        Preenchido apenas quando ORIGEM_MATCH == 'SECUNDARIO'.
        Mostra exatamente qual(is) CNAE(s) do seu filtro foram
        encontrados nos secundários da empresa.
    """
    cnaes_str = {str(c) for c in cnaes}

    match_principal  = chunk["CNAE_FISCAL_PRINCIPAL"].isin(cnaes_str)
    match_secundario = _cnae_secundario_match(chunk["CNAE_FISCAL_SECUNDARIA"], cnaes_str)

    chunk = chunk.copy()
    chunk["ORIGEM_MATCH"] = "PRINCIPAL"
    chunk.loc[~match_principal & match_secundario, "ORIGEM_MATCH"] = "SECUNDARIO"

    chunk["CNAE_MATCH_SECUNDARIO"] = None
    mask_sec = chunk["ORIGEM_MATCH"] == "SECUNDARIO"
    if mask_sec.any():
        chunk.loc[mask_sec, "CNAE_MATCH_SECUNDARIO"] = _cnae_secundario_matched(
            chunk.loc[mask_sec, "CNAE_FISCAL_SECUNDARIA"], cnaes_str
        )

    return chunk


# ---------------------------------------------------------------------------
# Funções públicas
# ---------------------------------------------------------------------------

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

    porte_numerico         = pd.to_numeric(df_emp["PORTE_EMPRESA"], errors="coerce")
    capital_social_numerico = _capital_social_para_float(df_emp["CAPITAL_SOCIAL"])

    if portes is not None:
        df_emp                  = df_emp[porte_numerico.isin(portes)]
        porte_numerico          = porte_numerico.loc[df_emp.index]
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

    cnaes_set = {str(c) for c in cnaes} if cnaes is not None else None

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

        if cnaes_set is not None:
            filtro_principal  = chunk["CNAE_FISCAL_PRINCIPAL"].isin(cnaes_set)
            filtro_secundario = _cnae_secundario_match(chunk["CNAE_FISCAL_SECUNDARIA"], cnaes_set)
            chunk = chunk[filtro_principal | filtro_secundario]

        if ufs is not None:
            chunk = chunk[chunk["UF"].isin(ufs)]

        chunk = chunk[chunk["SITUACAO_CADASTRAL"] == "02"]
        chunk = chunk.join(mapa_empresas, on="CNPJ_BASICO", how="left")
        chunk = chunk[chunk["PORTE_EMPRESA"].notna()]

        # ── Adiciona colunas de diagnóstico de match ──────────────────────
        if cnaes_set is not None and not chunk.empty:
            chunk = _adicionar_colunas_match(chunk, cnaes_set)

        if not chunk.empty:
            partes.append(chunk)

    if not partes:
        colunas_saida = COLUNAS_ESTABELECIMENTOS_USADAS + [
            "CNPJ_COMPLETO", "PORTE_EMPRESA", "CAPITAL_SOCIAL",
            "NATUREZA_JURIDICA", "ORIGEM_MATCH", "CNAE_MATCH_SECUNDARIO",
        ]
        return pd.DataFrame(columns=colunas_saida)

    return pd.concat(partes, ignore_index=True)


def filtrar_empresas(
    df: pd.DataFrame,
    cnaes,
    ufs,
    portes,
    naturezas_juridicas=None,
) -> pd.DataFrame:
    porte_numerico          = pd.to_numeric(df["PORTE_EMPRESA"], errors="coerce")
    capital_social_numerico = _capital_social_para_float(df["CAPITAL_SOCIAL"])
    filtro_capital          = capital_social_numerico >= CAPITAL_SOCIAL_MINIMO
    
    df = df[df["CNPJ_ORDEM"] == "0001"].copy()

    if CAPITAL_SOCIAL_ACEITAR_ZERO:
        filtro_capital = filtro_capital | (capital_social_numerico == 0)

    if naturezas_juridicas is None:
        naturezas_juridicas = NATUREZAS_JURIDICAS

    filtro_natureza = True
    if naturezas_juridicas:
        filtro_natureza = df["NATUREZA_JURIDICA"].isin(naturezas_juridicas)

    cnaes_set = {str(c) for c in cnaes} if cnaes else set()

    filtro_cnae = (
        df["CNAE_FISCAL_PRINCIPAL"].isin(cnaes_set) |
        _cnae_secundario_match(df["CNAE_FISCAL_SECUNDARIA"], cnaes_set)
    )

    resultado = df[
        filtro_cnae &
        (df["UF"].isin(ufs)) &
        (porte_numerico.isin(portes)) &
        filtro_capital &
        filtro_natureza &
        (df["SITUACAO_CADASTRAL"] == "02")
    ].copy()

    # ── Adiciona colunas de diagnóstico de match ──────────────────────────
    if cnaes_set and not resultado.empty:
        resultado = _adicionar_colunas_match(resultado, cnaes_set)

    return resultado
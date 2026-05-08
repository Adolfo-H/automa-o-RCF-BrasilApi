from concurrent.futures import ThreadPoolExecutor, as_completed

import pandas as pd

from app.brasilapi import consultar_cnpj
from app.config import BATCH_SIZE, MAX_WORKERS
from app.utils import extrair_socios



def _capital_social_para_float(valor):
    if valor is None or valor == "":
        return None
    if isinstance(valor, str):
        valor = valor.replace(",", ".")
    try:
        return float(valor)
    except (TypeError, ValueError):
        return None


def _valor_texto(valor):
    if valor is None:
        return None
    if pd.isna(valor):
        return None
    texto = str(valor).strip()
    return texto or None


def enriquecer_lote(registros: list[dict], max_workers: int = MAX_WORKERS) -> pd.DataFrame:
    leads = []

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = {
            executor.submit(consultar_cnpj, registro["CNPJ_COMPLETO"]): registro
            for registro in registros
        }

        for future in as_completed(futures):
            dados_originais = futures[future]
            try:
                dados = future.result()
                leads.append({
                    "cnpj":                  _valor_texto(dados.get("cnpj")),
                    "razao_social":          _valor_texto(dados.get("razao_social")),
                    "nome_fantasia":         _valor_texto(dados.get("nome_fantasia")),
                    "cnae_principal":        _valor_texto(dados.get("cnae_fiscal")),
                    "natureza_juridica":     _valor_texto(dados.get("natureza_juridica")) or _valor_texto(dados_originais.get("NATUREZA_JURIDICA")),
                    "uf":                    _valor_texto(dados.get("uf")),
                    "municipio":             _valor_texto(dados.get("municipio")),
                    "porte":                 int(dados_originais.get("PORTE_EMPRESA") or 0),
                    "telefone":              _valor_texto(dados.get("ddd_telefone_1")),
                    "email":                 _valor_texto(dados.get("email")) or _valor_texto(dados_originais.get("CORREIO_ELETRONICO")),
                    "capital_social":        _capital_social_para_float(dados.get("capital_social")) or _capital_social_para_float(dados_originais.get("CAPITAL_SOCIAL")),
                    "socios":                _valor_texto(extrair_socios(dados.get("qsa"))),
                    # ── Colunas de diagnóstico do match de CNAE ──────────────
                    "origem_match":          _valor_texto(dados_originais.get("ORIGEM_MATCH")),
                    "cnae_match_secundario": _valor_texto(dados_originais.get("CNAE_MATCH_SECUNDARIO")),
                })
            except Exception as e:
                print(f"Erro ao consultar CNPJ {dados_originais['CNPJ_COMPLETO']}: {e}")

    return pd.DataFrame(leads)


def iterar_lotes(df: pd.DataFrame, batch_size: int = BATCH_SIZE):
    registros = df.to_dict(orient="records")
    for inicio in range(0, len(registros), batch_size):
        yield registros[inicio:inicio + batch_size]
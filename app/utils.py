def extrair_socios(qsa):
    if not qsa:
        return ""

    nomes = [
        socio.get("nome_socio", "")
        for socio in qsa
    ]

    return " | ".join(filter(None, nomes))
from sqlalchemy import text

from app.database import engine


def remover_empresas_por_nomes_razao_social(nomes_razao_social: list[str]) -> None:
    """Remove empresas por razão social (igualdade exata, ignorando maiúsc/minúsc).

    Espera-se que `nomes_razao_social` contenha apenas itens já limpos (sem vazios).
    """

    query = text(
        """
        DELETE FROM leads_empresas
        WHERE LOWER(razao_social) = LOWER(:nome)
        """
    )

    removidas_por_item = []

    with engine.begin() as conn:
        for nome in nomes_razao_social:
            resultado = conn.execute(query, {"nome": nome})
            removidas_por_item.append((nome, resultado.rowcount))

    total = sum(count for _, count in removidas_por_item)

    for nome, count in removidas_por_item:
        print(f"{count} empresas removidas para: {nome}")
    print(f"Total removido: {total}")


if __name__ == "__main__":
    entrada = input(
        "Digite a(s) razão(ões) social(is) para remover (separe por vírgula): "
    )

    # Divide por vírgula e remove espaços; mantém igualdade exata (sem normalização extra)
    nomes = [item.strip() for item in entrada.split(",") if item.strip()]

    if not nomes:
        print("Nenhuma razão social informada. Nenhuma empresa removida.")
    else:
        remover_empresas_por_nomes_razao_social(nomes)


import pandas as pd
from rich import print
from sqlalchemy import text

from app.database import engine
from app.enrichment import buscar_presenca_online


def obter_leads_por_input_terminal():
    print("\n[bold cyan]📥 PROSPECÇÃO CIRÚRGICA — PRESENÇA ONLINE[/bold cyan]")
    print("[yellow]👉 Cole os IDs das empresas do Excel separados por vírgula (Ex: 1,12,23):[/yellow]")
    
    # Captura a colagem do terminal feito pelo usuário
    entrada = input(">> ").strip()
    
    if not entrada:
        print("[red]❌ Nenhum ID foi informado. Encerrando script.[/red]")
        return []

    # Trata espaços vazios e converte o texto para uma lista limpa de strings/números
    ids_limpos = [id_str.strip() for id_str in entrada.split(",") if id_str.strip()]
    
    # Valida se a colagem contém apenas dígitos numéricos para evitar quebras no banco
    for id_atual in ids_limpos:
        if not id_atual.isdigit():
            print(f"[bold red]❌ Erro: '{id_atual}' não é um ID numérico válido. Digite apenas números e vírgulas.[/bold red]")
            return []

    return ids_limpos


def enriquecer_empresas():
    # Obtém a lista cirúrgica de IDs direto do input do terminal
    ids_para_buscar = obter_leads_por_input_terminal()
    
    if not ids_para_buscar:
        return

    # Converte os IDs em formato string para inteiros antes de passar para a tupla do SQL
    ids_inteiros = tuple(int(i) for i in ids_para_buscar)

    # Caso seja apenas 1 ID, a tupla do Python fica (id,). Ajustamos para o SQL não quebrar.
    if len(ids_inteiros) == 1:
        query = f"SELECT id, razao_social, nome_fantasia FROM leads_empresas WHERE id = {ids_inteiros[0]}"
    else:
        query = f"SELECT id, razao_social, nome_fantasia FROM leads_empresas WHERE id IN {ids_inteiros}"

    df = pd.read_sql(query, engine)

    if df.empty:
        print("[bold yellow]⚠ Nenhuma empresa encontrada no banco de dados para os IDs informados.[/bold yellow]")
        return

    print(f"\n[bold green]🚀 Iniciando a verificação de presença online de {len(df)} empresas![/bold green]\n")

    for _, row in df.iterrows():
        # Define se usará o nome fantasia ou a razão social na busca do Google
        nome = row["nome_fantasia"] or row["razao_social"]

        print(f"🔍 Pesquisando canais digitais para: [bold]{nome[:35]}[/bold]...", end=" ")

        # Faz a chamada para a SerpAPI
        enrich = buscar_presenca_online(nome)

        update_stmt = text("""
        UPDATE leads_empresas
        SET
            site = :site,
            linkedin = :linkedin,
            tem_site = :tem_site,
            tem_linkedin = :tem_linkedin
        WHERE id = :id
        """)

        dados = {
            "id": int(row["id"]),
            "site": enrich["SITE"],
            "linkedin": enrich["LINKEDIN"],
            "tem_site": enrich["TEM_SITE"],
            "tem_linkedin": enrich["TEM_LINKEDIN"],
        }

        # Salva o resultado no banco na mesma hora
        with engine.begin() as conn:
            conn.execute(update_stmt, dados)

        # Print de feedback visual do que foi encontrado
        status_site = "[green]SITE OK[/green]" if enrich["TEM_SITE"] else "[red]SEM SITE[/red]"
        status_lkd = "[blue]LINKEDIN OK[/blue]" if enrich["TEM_LINKEDIN"] else "[red]SEM LKND[/red]"
        print(f"➔ {status_site} | {status_lkd}")

    print("\n[bold green]🏁 Enriquecimento sob demanda finalizado com sucesso![/bold green]")


if __name__ == "__main__":
    enriquecer_empresas()
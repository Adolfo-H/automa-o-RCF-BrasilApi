from rich import print

from app.config import BATCH_SIZE, CNAES, MAX_WORKERS, NATUREZAS_JURIDICAS, PORTES, UFS
from app.pipeline import enriquecer_lote, iterar_lotes
from app.receita import carregar_base
from salvar import buscar_cnpjs_ja_salvos, salvar_leads


def main():
    print("[cyan]Carregando base da Receita Federal...[/cyan]")

    df = carregar_base(
        "data/estabelecimentos_0.csv",
        "data/empresas_0.csv",
        cnaes=CNAES,
        ufs=UFS,
        portes=PORTES,
        naturezas_juridicas=NATUREZAS_JURIDICAS,
    )

    print(f"[green]{len(df)} empresas elegiveis encontradas.[/green]")

    cnpjs_existentes = buscar_cnpjs_ja_salvos(df["CNPJ_COMPLETO"].tolist())
    if cnpjs_existentes:
        df = df[~df["CNPJ_COMPLETO"].isin(cnpjs_existentes)].copy()

    print(f"[yellow]{len(df)} empresas pendentes para enriquecer.[/yellow]")

    total_salvos = 0
    total_lotes = (len(df) + BATCH_SIZE - 1) // BATCH_SIZE if len(df) else 0

    try:
        for indice, lote in enumerate(iterar_lotes(df, batch_size=BATCH_SIZE), start=1):
            print(
                f"[cyan]Processando lote {indice}/{total_lotes} "
                f"com {len(lote)} empresas usando {MAX_WORKERS} worker(s)...[/cyan]"
            )
            leads = enriquecer_lote(lote, max_workers=MAX_WORKERS)
            salvos_no_lote = salvar_leads(leads)
            total_salvos += salvos_no_lote
            print(
                f"[green]Lote {indice} concluido: "
                f"{len(leads)} enriquecidos, {salvos_no_lote} novos salvos.[/green]"
            )
    except KeyboardInterrupt:
        print(
            f"\n[yellow]Execucao interrompida pelo usuario. "
            f"{total_salvos} lead(s) ja foram salvos no banco.[/yellow]"
        )
        return

    print(f"[bold green]Pipeline concluido com sucesso! {total_salvos} novos leads salvos.[/bold green]")


if __name__ == "__main__":
    main()

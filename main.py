from rich import print

from app.config import (
    BATCH_SIZE,
    CNAES,
    MAX_WORKERS,
    NATUREZAS_JURIDICAS,
    PORTES,
    UFS
)

from app.pipeline import enriquecer_lote, iterar_lotes
from app.receita import carregar_base

from salvar import (
    buscar_cnpjs_ja_salvos,
    salvar_leads
)

from app.hubspot.deduplicador import (
    buscar_dominios_hubspot
)

from app.utils import extrair_dominio

import glob
import os


def main():

    print(
        "[cyan]Iniciando processamento em lote da Receita Federal...[/cyan]"
    )

    # ==========================================
    # BUSCA DOMINIOS JA EXISTENTES NO HUBSPOT
    # ==========================================

    dominios_hubspot = buscar_dominios_hubspot()

    print(
        f"[green]{len(dominios_hubspot)} dominios carregados do HubSpot.[/green]"
    )

    # ==========================================
    # BUSCA ARQUIVOS DA RECEITA
    # ==========================================

    arquivos_est = sorted(
        glob.glob("data/estabelecimentos_*.csv")
    )

    total_geral_salvos = 0

    for path_est in arquivos_est:

        # ==========================================
        # DESCOBRE NUMERO DO ARQUIVO
        # ==========================================

        nome_arquivo = os.path.basename(path_est)

        index = nome_arquivo.split('_')[1].split('.')[0]

        path_emp = f"data/empresas_{index}.csv"

        if not os.path.exists(path_emp):

            print(
                f"[yellow]Aviso: Arquivo {path_emp} não encontrado. Pulando...[/yellow]"
            )

            continue

        print(
            f"\n[bold blue]>>> Processando Par {index}: "
            f"{nome_arquivo} e empresas_{index}.csv[/bold blue]"
        )

        # ==========================================
        # CARREGA BASE FILTRADA
        # ==========================================

        df = carregar_base(
            path_est,
            path_emp,
            cnaes=CNAES,
            ufs=UFS,
            portes=PORTES,
            naturezas_juridicas=NATUREZAS_JURIDICAS,
        )

        if len(df) == 0:

            print(
                f"[yellow]Nenhum dado encontrado para o par {index}.[/yellow]"
            )

            continue

        # ==========================================
        # REMOVE CNPJS JA EXISTENTES
        # ==========================================

        cnpjs_existentes = buscar_cnpjs_ja_salvos(
            df["CNPJ_COMPLETO"].tolist()
        )

        if cnpjs_existentes:

            df = df[
                ~df["CNPJ_COMPLETO"].isin(cnpjs_existentes)
            ].copy()

        if len(df) == 0:

            print(
                f"[yellow]Todas as empresas do par {index} já constam no banco.[/yellow]"
            )

            continue

        print(
            f"[yellow]{len(df)} empresas pendentes para enriquecer no par {index}.[/yellow]"
        )

        # ==========================================
        # PROCESSAMENTO DOS LOTES
        # ==========================================

        total_lotes = (
            len(df) + BATCH_SIZE - 1
        ) // BATCH_SIZE

        try:

            for indice, lote in enumerate(
                iterar_lotes(df, batch_size=BATCH_SIZE),
                start=1
            ):

                print(
                    f"[cyan]Par {index} | "
                    f"Lote {indice}/{total_lotes} "
                    f"({len(lote)} empresas)...[/cyan]"
                )

                # ==========================================
                # ENRIQUECE LEADS
                # ==========================================

                leads = enriquecer_lote(
                    lote,
                    max_workers=MAX_WORKERS
                )

                if leads.empty:

                    print(
                        "[yellow]Nenhum lead enriquecido neste lote.[/yellow]"
                    )

                    continue

                # ==========================================
                # CONFERE COLUNA EMAIL
                # ==========================================

                if "email" not in leads.columns:

                    print(
                        "[red]Coluna 'email' nao encontrada nos leads.[/red]"
                    )

                    continue

                # ==========================================
                # EXTRAI DOMINIO
                # ==========================================

                leads["dominio"] = (
                    leads["email"]
                    .fillna("")
                    .apply(extrair_dominio)
                )

                # ==========================================
                # REMOVE DOMINIOS JA EXISTENTES NO HUBSPOT
                # ==========================================

                antes = len(leads)

                leads = leads[
                    ~leads["dominio"].isin(dominios_hubspot)
                ]

                removidos = antes - len(leads)

                print(
                    f"[yellow]{removidos} leads removidos por ja existirem no HubSpot.[/yellow]"
                )

                if leads.empty:

                    print(
                        "[yellow]Todos os leads deste lote ja existem no HubSpot.[/yellow]"
                    )

                    continue

                # ==========================================
                # REMOVE COLUNA AUXILIAR
                # ==========================================

                leads = leads.drop(
                    columns=["dominio"],
                    errors="ignore"
                )

                # ==========================================
                # SALVA LEADS NOVOS
                # ==========================================

                salvos_no_lote = salvar_leads(leads)

                total_geral_salvos += salvos_no_lote

                print(
                    f"[green]Lote {indice} concluido: "
                    f"{len(leads)} enriquecidos, "
                    f"{salvos_no_lote} novos salvos.[/green]"
                )

        except KeyboardInterrupt:

            print(
                f"\n[yellow]Interrompido. "
                f"Total salvo até agora: "
                f"{total_geral_salvos}[/yellow]"
            )

            return

    print(
        f"\n[bold green]Pipeline Finalizado! "
        f"Total de {total_geral_salvos} "
        f"novos leads no banco.[/bold green]"
    )


if __name__ == "__main__":
    main()
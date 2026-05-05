from rich import print
from app.config import BATCH_SIZE, CNAES, MAX_WORKERS, NATUREZAS_JURIDICAS, PORTES, UFS
from app.pipeline import enriquecer_lote, iterar_lotes
from app.receita import carregar_base
from salvar import buscar_cnpjs_ja_salvos, salvar_leads
import glob
import os

def main():
    print("[cyan]Iniciando processamento em lote da Receita Federal...[/cyan]")

    # 1. Busca todos os arquivos de estabelecimentos na pasta data
    arquivos_est = sorted(glob.glob("data/estabelecimentos_*.csv"))
    
    total_geral_salvos = 0  # Contador para o somatório de todos os arquivos

    for path_est in arquivos_est:
        # 2. Descobre o número do arquivo
        nome_arquivo = os.path.basename(path_est)
        index = nome_arquivo.split('_')[1].split('.')[0]
        path_emp = f"data/empresas_{index}.csv"
        
        if not os.path.exists(path_emp):
            print(f"[yellow]Aviso: Arquivo {path_emp} não encontrado. Pulando...[/yellow]")
            continue

        print(f"\n[bold blue]>>> Processando Par {index}: {nome_arquivo} e empresas_{index}.csv[/bold blue]")

        # 3. Carrega a base filtrada
        df = carregar_base(
            path_est,
            path_emp,
            cnaes=CNAES,
            ufs=UFS,
            portes=PORTES,
            naturezas_juridicas=NATUREZAS_JURIDICAS,
        )

        if len(df) == 0:
            print(f"[yellow]Nenhum dado encontrado para o par {index}.[/yellow]")
            continue

        # 4. Filtra CNPJs já existentes no banco
        cnpjs_existentes = buscar_cnpjs_ja_salvos(df["CNPJ_COMPLETO"].tolist())
        if cnpjs_existentes:
            df = df[~df["CNPJ_COMPLETO"].isin(cnpjs_existentes)].copy()

        if len(df) == 0:
            print(f"[yellow]Todas as empresas do par {index} já constam no banco.[/yellow]")
            continue

        print(f"[yellow]{len(df)} empresas pendentes para enriquecer no par {index}.[/yellow]")

        # --- A LOGICA DE PROCESSAMENTO DEVE ESTAR AQUI (DENTRO DO FOR) ---
        total_lotes = (len(df) + BATCH_SIZE - 1) // BATCH_SIZE
        
        try:
            for indice, lote in enumerate(iterar_lotes(df, batch_size=BATCH_SIZE), start=1):
                print(
                    f"[cyan]Par {index} | Lote {indice}/{total_lotes} "
                    f"({len(lote)} empresas)...[/cyan]"
                )
                
                leads = enriquecer_lote(lote, max_workers=MAX_WORKERS)
                salvos_no_lote = salvar_leads(leads)
                total_geral_salvos += salvos_no_lote
                
                print(
                    f"[green]Lote {indice} concluido: "
                    f"{len(leads)} enriquecidos, {salvos_no_lote} novos salvos.[/green]"
                )
        except KeyboardInterrupt:
            print(f"\n[yellow]Interrompido. Total salvo até agora: {total_geral_salvos}[/yellow]")
            return

    print(f"\n[bold green]Pipeline Finalizado! Total de {total_geral_salvos} novos leads no banco.[/bold green]")

if __name__ == "__main__":
    main()
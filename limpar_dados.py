import pandas as pd
from sqlalchemy import select, func, delete
from app.database import engine, SessionLocal
from app.models import LeadEmpresa
from rich import print

def buscar_empresas_duplicadas():
    print("[yellow]Buscando empresas com múltiplas razões sociais no banco...[/yellow]")
    with engine.connect() as conn:
        stmt = (
            select(LeadEmpresa.razao_social)
            .group_by(LeadEmpresa.razao_social)
            .having(func.count(LeadEmpresa.razao_social) > 1)
        )
        result = conn.execute(stmt).fetchall()
        return [row[0] for row in result]

def remover_filiais_seguro(lista_nomes):
    if not lista_nomes:
        print("[white]Nenhuma duplicata para limpar.[/white]")
        return

    ids_para_deletar = []
    total_processado = 0
    
    # Usamos Session para ter mais controle sobre os objetos
    session = SessionLocal()
    
    try:
        for nome in lista_nomes:
            # Busca todos os registros que possuem essa Razão Social
            registros = session.query(LeadEmpresa).filter(LeadEmpresa.razao_social == nome).all()
            
            # Lógica para encontrar a Matriz (independente do tamanho da string)
            # O 0001 sempre fica antes dos últimos 2 dígitos (DV)
            matriz = None
            for r in registros:
                cnpj_limpo = r.cnpj.zfill(14) # Garante que tratamos como 14 dígitos
                if cnpj_limpo[8:12] == "0001":
                    matriz = r
                    break
            
            # Se não encontrou um "0001", mantemos o primeiro registro por segurança 
            # para a empresa não sumir do banco
            if not matriz and registros:
                matriz = registros[0]
                print(f"[orange1]Aviso: {nome} não possui CNPJ 0001. Mantendo ID {matriz.id} por segurança.[/orange1]")

            # Todos os outros IDs desse grupo vão para a lista de exclusão
            for r in registros:
                if r.id != matriz.id:
                    ids_para_deletar.append(r.id)
            
            total_processado += 1

        # Deleta todos os IDs de filiais de uma vez só (alta performance)
        if ids_para_deletar:
            session.query(LeadEmpresa).filter(LeadEmpresa.id.in_(ids_para_deletar)).delete(synchronize_session=False)
            session.commit()
            print(f"[bold green]Sucesso! {len(ids_para_deletar)} filiais removidas de {total_processado} empresas.[/bold green]")
        else:
            print("[blue]Nenhuma filial encontrada para os critérios de exclusão.[/blue]")

    except Exception as e:
        session.rollback()
        print(f"[red]Erro durante a limpeza: {e}[/red]")
    finally:
        session.close()

if __name__ == "__main__":
    duplicadas = buscar_empresas_duplicadas()
    if duplicadas:
        print(f"[cyan]Empresas identificadas:[/cyan] {len(duplicadas)}")
        remover_filiais_seguro(duplicadas)
import time
import re
from rich import print
from sqlalchemy import select, update
from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeout

from app.database import SessionLocal
from app.models import LeadEmpresa

# Pasta onde a sessão do WhatsApp ficará salva para evitar ler o QR Code toda vez
USER_DATA_DIR = "./whatsapp_session"


def limpar_numero(telefone: str) -> str:
    """
    Remove caracteres especiais do telefone e garante o DDI 55 (Brasil)
    no início para o link do WhatsApp.
    """
    if not telefone:
        return ""
    
    # Mantém apenas os números
    numeros = re.sub(r'\D', '', str(telefone))
    
    # Se o número tiver 10 ou 11 dígitos, assume que é Brasil e adiciona o 55
    if len(numeros) in (10, 11):
        numeros = f"55{numeros}"
        
    return numeros


def validar_numero_playwright(page, numero: str) -> bool | None:
    """
    Navega até o link do WhatsApp Web e valida se o número possui conta.
    """
    url = f"https://web.whatsapp.com/send?phone={numero}"
    
    try:
        page.goto(url)

        # 1. Aguarda ou o chat real abrir (#main) OR o modal de erro específico aparecer.
        # O modal de erro do WhatsApp sempre contém um botão "OK" (geralmente dentro de um botão ou div com texto).
        # Vamos usar um seletor composto: se aparecer o chat ou um pop-up de texto, avançamos.
        page.wait_for_selector(
            'button:has-text("OK"), #main', 
            timeout=22000
        )
        
        # 2. Se o painel principal do chat (#main) estiver visível, o número é 100% válido
        if page.locator('#main').is_visible():
            return True

        # 3. Se não abriu o chat, procuramos pelo pop-up de erro usando filtros de texto precisos
        # Procuramos o primeiro elemento de modal que contenha textos de aviso de número inválido
        modal_erro = page.locator('div[data-animate-modal-popup="true"]').filter(
            has_text="não está no WhatsApp"
        ).or_(
            page.locator('div[data-animate-modal-popup="true"]').filter(has_text="inválido")
        ).or_(
            page.locator('div[data-animate-modal-popup="true"]').filter(has_text="incorreto")
        )

        # Usamos .first para garantir que se houver duplicidade oculta no DOM, pegamos apenas um e evitamos o Crash
        if modal_erro.first.is_visible():
            texto_modal = modal_erro.first.inner_text().lower()
            if "não está" in texto_modal or "inválido" in texto_modal or "incorreto" in texto_modal or "invalid" in texto_modal:
                # Clica no botão OK do modal para fechar o pop-up e limpar a tela para a próxima requisição
                botao_ok = page.locator('button:has-text("OK")')
                if botao_ok.is_visible():
                    botao_ok.click()
                    time.sleep(0.5)
                return False
            
        # Se saiu dos testes e o #main não está visível, mas também não achou erro claro, 
        # pode ser lentidão no carregamento da conversa. Retorna None para reavaliar depois.
        return None

    except PlaywrightTimeout:
        print(f"[yellow]Timeout na validação do número {numero}. Mantendo como pendente...[/yellow]")
        return None


def main():
    print("[bold cyan]🤖 Iniciando Validador de WhatsApp Automatizado[/bold cyan]")

    # 1. Busca os primeiros 100 leads pendentes (telefone preenchido e whatsapp_valido é nulo)
    with SessionLocal() as db:
        stmt = select(LeadEmpresa).where(
            LeadEmpresa.telefone.isnot(None),
            LeadEmpresa.whatsapp_valido.is_(None)
        ).limit(569)
        
        leads_pendentes = db.scalars(stmt).all()

    if not leads_pendentes:
        print("[bold green]✅ Nenhum número pendente de validação encontrado no banco![/bold green]")
        return

    print(f"[cyan]📦 Encontrados {len(leads_pendentes)} leads para validar neste lote.[/cyan]")

    # 2. Inicializa o navegador através do Playwright
    with sync_playwright() as p:
        browser = p.chromium.launch_persistent_context(
            user_data_dir=USER_DATA_DIR,
            headless=False,  # Deixe False para conseguir ver a tela e escanear o QR Code
            args=["--no-sandbox"]
        )
        
        page = browser.pages[0]
        page.goto("https://web.whatsapp.com")
        
        print("[bold yellow]⏳ Aguardando carregamento do WhatsApp Web...[/bold yellow]")
        print("[yellow]👉 Se for a primeira vez, escaneie o QR Code no seu celular agora.[/yellow]")
        
        # Espera a barra lateral de conversas carregar para confirmar o login completo
        page.wait_for_selector('div#pane-side', timeout=60000)
        print("[bold green]🚀 Conectado ao WhatsApp Web com sucesso![/bold green]")

        # 3. Itera sobre os leads e atualiza o banco em tempo real
        with SessionLocal() as db:
            for lead in leads_pendentes:
                numero_limpo = limpar_numero(lead.telefone)
                
                # Tratamento para telefones obviamente errados ou vazios
                if not numero_limpo or len(numero_limpo) < 12:
                    print(f"[red]❌ Número inválido/incompleto no banco:[/red] {lead.telefone} ({lead.razao_social})")
                    
                    stmt_update = (
                        update(LeadEmpresa)
                        .where(LeadEmpresa.id == lead.id)
                        .values(whatsapp_valido=False)
                    )
                    db.execute(stmt_update)
                    db.commit()
                    continue

                print(f"🔍 Validando: [bold]{lead.razao_social[:30]}[/bold] | {numero_limpo}...", end=" ")
                
                # Executa a validação visual na página do navegador
                resultado = validar_numero_playwright(page, numero_limpo)
                
                if resultado is True:
                    print("[bold green]VÁLIDO[/bold green]")
                elif resultado is False:
                    print("[bold red]INVÁLIDO[/bold red]")
                else:
                    print("[yellow]TIMEOUT (Pulado)[/yellow]")

                # Se o resultado for True ou False (não nulo), envia a query direta de UPDATE ao banco
                if resultado is not None:
                    stmt_update = (
                        update(LeadEmpresa)
                        .where(LeadEmpresa.id == lead.id)
                        .values(whatsapp_valido=resultado)
                    )
                    db.execute(stmt_update)
                    db.commit()
                
                # Delay de 2.5 segundos entre checagens para evitar bloqueios por comportamento robótico
                time.sleep(2.5)

        browser.close()
        
    print("[bold green]🏁 Lote concluído! Rode o script de exportação para ver os resultados no Excel.[/bold green]")


if __name__ == "__main__":
    main()
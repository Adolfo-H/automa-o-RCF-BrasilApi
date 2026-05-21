# 📊 Leads — Inteligência de Dados & Prospecção

Pipeline de alta performance desenvolvido em Python para extração, filtragem, enriquecimento de dados da base pública da Receita Federal e validação automatizada de canais de contato. O projeto transforma dados brutos em leads qualificados com foco em inteligência comercial e prospecção B2B de grande porte.

---

## 📌 Visão Geral

O **Leads** automatiza o ciclo completo de inteligência de dados:

- **Ingestão e Filtragem:** Leitura analítica de bases brutas da Receita Federal focando em empresas de grande porte
- **Deduplicação Estratégica:** Cruzamento de domínios em tempo real com a base existente no CRM HubSpot
- **Enriquecimento Avançado:** Consultas assíncronas concorrentes para estruturação de dados societários e de contato
- **Validação de Canais:** Verificação automatizada via browser para confirmar quais leads possuem contas ativas de WhatsApp

---

## ✨ Diferenciais do Projeto

### 🔎 Filtro Inteligente de Origem

Redução automática de ruído ao processar apenas estabelecimentos **Matriz (0001)**, evitando duplicidade de filiais, desperdício de requisições em APIs e inconsistências comerciais.

### ⚡ Arquitetura Escalável e Assíncrona

Utilização de `ThreadPoolExecutor` para consultas massivas paralelas na BrasilAPI (CNPJ v1), com controle rígido de *Rate Limit*, travas de concorrência (`threading.Lock`) e *Backoff* incremental para proteção contra erros `429`.

### 🛡️ Validação de WhatsApp Baseada em Interface (Playwright)

Automação ponta a ponta que varre a base em lotes, simulando navegação humana e interpretando respostas visuais do WhatsApp Web para marcar o status de conectividade real do lead, contornando travas de interface.

### 🗄️ Persistência Robusta

Gerenciamento transacional completo via **PostgreSQL** com cláusulas `ON CONFLICT DO NOTHING`, prevenção de duplicidades por chave única (`cnpj`), controle de estados (`None` / `True` / `False`) e isolamento de escopo por sessões (`SessionLocal`).

---

## 📂 Estrutura do Projeto

```
leadstributarios/
├── app/
│   ├── hubspot/
│   │   └── deduplicador.py     # Sincronização e extração de domínios do CRM HubSpot
│   ├── brasilapi.py            # Motor assíncrono de consulta ao CNPJ com controle de rate limit
│   ├── config.py               # Central de variáveis de ambiente, filtros (CNAEs, UFs, Portes)
│   ├── database.py             # Configuração da Engine do SQLAlchemy e SessionLocal (Postgres)
│   ├── models.py               # Mapeamento declarativo de tabelas (Schema das tabelas)
│   ├── pipeline.py             # Orquestrador de threads concorrentes para enriquecimento de lotes
│   ├── receita.py              # Parser analítico e filtros matemáticos dos CSVs da Receita
│   └── utils.py                # Utilitários de strings (extração de domínios e tratamento de QSA)
├── data/                       # Diretório reservado para os arquivos CSV brutos da Receita Federal
├── whatsapp_session/           # Diretório de persistência de estado do navegador (Session Cookies)
├── criar_tabelas.py            # Inicializador de tabelas e injeção de patches estruturais de colunas
├── exportar.py                 # Exportador de leads qualificados para relatórios Excel (.xlsx)
├── main.py                     # Script principal de execução do pipeline de dados da Receita
├── salvar.py                   # Repositório de persistência em lote via inserções nativas Postgres
└── validar_whatsapp.py         # Script de validação visual e automação do WhatsApp Web
```

---

## ⚙️ Instalação e Configuração

### 📋 Pré-requisitos

- **Python 3.11+** (Recomendado 3.12+)
- **PostgreSQL** ativo e configurado
- Arquivos `.csv` de estabelecimentos da Receita Federal dentro da pasta `data/`

### 🔧 Instalação das Dependências

Abra o terminal na raiz do projeto e instale as bibliotecas necessárias:

```bash
# Instalação das bibliotecas do ecossistema Python
pip install pandas sqlalchemy requests openpyxl tqdm rich python-dotenv playwright

# Instalação obrigatória do driver do Chromium para o Playwright
python -m playwright install chromium
```

### 🗂️ Configuração das Variáveis de Ambiente

Crie um arquivo `.env` na raiz do projeto e configure as credenciais operacionais:

```env
DATABASE_URL=postgresql://usuario:senha@localhost:5432/seu_banco
MAX_WORKERS=30
BATCH_SIZE=200
REQUEST_INTERVAL_SECONDS=0.1
REQUEST_TIMEOUT_SECONDS=20
```

---

## 🔄 Fluxo de Operação do Pipeline

### 1️⃣ Inicialização do Schema do Banco

Cria a estrutura de tabelas relacionais (`leads_empresas` e `hubspot_empresas`) e aplica correções de colunas necessárias como `natureza_juridica` e `whatsapp_valido`.

```bash
python criar_tabelas.py
```

### 2️⃣ Execução do Pipeline Principal

O fluxo executa a leitura inteligente dos blocos de arquivos na pasta `data/`, aplica os filtros de corte por capital social e porte grande, e inicia o motor concorrente:

```
[ Arquivos CSV ]
     ↓
[ Filtragem Interna ] ─→ Apenas Matrizes (0001) + Capital Social ≥ R$ 1MM
     ↓
[ Deduplicação HubSpot ] ─→ Remove leads que já possuem o mesmo domínio no CRM
     ↓
[ Enriquecimento Thread ] ─→ Consultas paralelas à BrasilAPI com Trava de Taxa (Lock)
     ↓
[ Gravação Postgres ] ─→ Inserção via ON CONFLICT DO NOTHING (Previne duplicar CNPJ)
```

Para iniciar o processamento:

```bash
python main.py
```

---

## 🛡️ Engenharia do Módulo de Validação

### Validação de WhatsApp (validar_whatsapp.py)

Para evitar gastos desnecessários com APIs de envio e validação de terceiros, o sistema utiliza uma camada de automação visual baseada em interface web via Playwright.

#### 🧩 Como Funciona a Fila de Validação

O script opera em lotes dinâmicos de 100 leads por vez por motivos de segurança do chip corporativo. Ele realiza um filtro no banco buscando apenas registros com telefone existente e campo de validação nulo:

```python
# A fila consome apenas o estado indefinido (None)
select(LeadEmpresa).where(
    LeadEmpresa.telefone.isnot(None), 
    LeadEmpresa.whatsapp_valido.is_(None)
).limit(100)
```

Toda vez que o script finaliza, você pode rodá-lo novamente e ele consumirá as próximas 100 empresas da fila sem repetir ou sobrecarregar registros antigos.

#### 🦾 Arquitetura Anti-Crash e Resolução de Modais

O script foi projetado para lidar com as variações estruturais dinâmicas da interface do WhatsApp Web, protegendo a execução contra o encerramento inesperado:

- **Detecção de Estado por Seletores Compostos:** Aguarda concorrentemente a renderização da conversa aberta (`#main`) ou a exibição de botões de erro (`button:has-text("OK")`)
- **Isolamento de Modais Temporários:** Filtra cirurgicamente o texto interno de contêineres de animação através de métodos estruturados (`.filter(has_text="não está no WhatsApp")`), ignorando modais intermediários
- **Limpeza e Desengasgo de Interface:** Sempre que um número é detectado como inválido, o robô clica fisicamente no botão OK para fechar o pop-up, limpando o DOM para o próximo registro
- **Sessão Persistente:** Salva cookies de autenticação na pasta `whatsapp_session/`. Você lê o QR Code apenas na primeira execução; nas subsequentes, o robô entra conectado diretamente

Para rodar a validação de canais ativos:

```bash
python validar_whatsapp.py
```

#### 💡 Nota Operacional

Caso deseje resetar empresas que falharam por lentidão técnica ou internet oscilante para reavaliá-las no próximo lote:

```sql
UPDATE leads_empresas SET whatsapp_valido = NULL WHERE whatsapp_valido = FALSE;
```

---

## 📈 Exportação e Inteligência Comercial

O script final compila toda a inteligência armazenada no banco de dados estruturado e exporta para relatórios corporativos em formato Excel, permitindo a distribuição imediata para times de prospecção.

```bash
python exportar.py
```

### 📋 Layout do Relatório Gerado (leads_exportados.xlsx)

| Grupo de Dados | Atributos | Objetivo Comercial |
|---|---|---|
| **Identificação Fiscal** | `cnpj`, `razao_social`, `nome_fantasia`, `natureza_juridica` | Validação cadastral e segmentação |
| **Classificação de Mercado** | `cnae_principal`, `cnae_match_secundario`, `porte`, `capital_social` | Verificação de fit de receita e tamanho da conta |
| **Canais de Contato** | `telefone`, `email`, `uf`, `municipio` | Dados de contato originais purificados |
| **Qualificação Digital** | `whatsapp_valido` | Filtro operacional: Alocação de contatos válidos (True/False) |
| **Estrutura de Decisões** | `socios` | Mapeamento de tomadores de decisão (QSA) para abordagem de Cold Calling |

---

## 🛠️ Stack Tecnológica

| Tecnologia | Propósito |
|---|---|
| **Python 3.12** | Núcleo de desenvolvimento e manipulação assíncrona |
| **PostgreSQL** | Armazenamento relacional persistente da base purificada de leads |
| **SQLAlchemy** | Camada de abstração de dados (ORM) e gerenciador de conexões em pool |
| **Playwright (Python)** | Engine de automação web em headless/headful para simulação de comportamento humano |
| **Pandas** | Estruturação de dados multidimensionais e tratamento de arquivos textuais em lote |
| **Rich** | Customização gráfica de logs em console para rastreamento em tempo real do pipeline |

---

## 📝 Licença

Projeto de uso interno. Todos os direitos reservados.

---

## 👥 Suporte e Contribuições

Para dúvidas, sugestões ou reportar problemas, abra uma issue no repositório do projeto.
# Leads Tributarios

Pipeline em Python para gerar leads B2B a partir de bases públicas da Receita Federal, enriquecer dados via BrasilAPI, eliminar duplicidades com base já existente no HubSpot, validar números no WhatsApp Web e exportar o resultado para Excel.

O projeto foi estruturado para operação prática: você alimenta a pasta `data/` com os arquivos da Receita, roda o pipeline principal, valida canais quando necessário e exporta a base final para uso comercial.

## Objetivo

O sistema transforma dados brutos de empresas em uma base de prospecção mais utilizável, aplicando:

- filtro por CNAE, UF, porte, capital social e natureza jurídica;
- deduplicação por CNPJ já salvo no banco;
- deduplicação por domínio já existente no HubSpot;
- enriquecimento de dados cadastrais via BrasilAPI;
- validação operacional de WhatsApp via automação no navegador;
- exportação da base tratada para `.xlsx`.

## Fluxo do projeto

```text
Arquivos CSV da Receita
        |
        v
Leitura e filtros iniciais
        |
        v
Deduplicação por CNPJ já salvo
        |
        v
Enriquecimento concorrente via BrasilAPI
        |
        v
Deduplicação por domínio do HubSpot
        |
        v
Persistência no PostgreSQL
        |
        +--> Validação de WhatsApp Web
        |
        +--> Enriquecimento manual de presença online
        |
        +--> Exportação para Excel
```

## Stack

- Python
- PostgreSQL
- SQLAlchemy
- Pandas
- Requests
- Playwright
- Rich
- Python Dotenv

## Estrutura do repositório

```text
leadstributarios/
|-- app/
|   |-- hubspot/
|   |   `-- deduplicador.py
|   |-- scripts/
|   |   `-- importar_hubspot.py
|   |-- brasilapi.py
|   |-- config.py
|   |-- database.py
|   |-- enrichment.py
|   |-- enriquecer_presenca_online.py
|   |-- models.py
|   |-- pipeline.py
|   |-- receita.py
|   `-- utils.py
|-- data/
|-- whatsapp_session/
|-- consultar.py
|-- criar_tabelas.py
|-- exportar.py
|-- limpar_dados.py
|-- main.py
|-- remover_empresa.py
|-- salvar.py
|-- teste_conexao.py
|-- validar_whatsapp.py
`-- requirements.txt
```

## Banco de dados

O projeto usa PostgreSQL via `DATABASE_URL`.

As tabelas principais são:

### `leads_empresas`

Armazena os leads gerados pelo pipeline, com campos como:

- `cnpj`
- `razao_social`
- `nome_fantasia`
- `cnae_principal`
- `natureza_juridica`
- `uf`
- `municipio`
- `porte`
- `telefone`
- `email`
- `capital_social`
- `socios`
- `origem_match`
- `cnae_match_secundario`
- `whatsapp_valido`
- `created_at`

### `hubspot_empresas`

Tabela de apoio para deduplicação por domínio, com:

- `nome_empresa`
- `dominio`
- `created_at`

## Pré-requisitos

- Python 3.11 ou superior
- PostgreSQL acessível
- arquivos CSV da Receita Federal no diretório `data/`
- Chromium do Playwright instalado para o validador de WhatsApp

## Instalação

Crie e ative um ambiente virtual, depois instale as dependências:

```bash
pip install -r requirements.txt
pip install openpyxl playwright serpapi
python -m playwright install chromium
```

Observação: `requirements.txt` hoje cobre apenas o núcleo do pipeline. Para usar exportação Excel, validação de WhatsApp e busca de presença online, você também precisa das bibliotecas acima.

## Configuração

Crie um arquivo `.env` na raiz do projeto com base em `.env.example`.

Exemplo:

```env
DATABASE_URL=postgresql+psycopg2://usuario:senha@host:5432/banco
MAX_WORKERS=2
BATCH_SIZE=50
REQUEST_INTERVAL_SECONDS=1.0
REQUEST_TIMEOUT_SECONDS=20
MAX_RETRIES=5
BACKOFF_BASE_SECONDS=3.0
SERP_API_KEY=sua_chave_serpapi
```

### Variáveis importantes

- `DATABASE_URL`: conexão com o PostgreSQL.
- `MAX_WORKERS`: paralelismo do enriquecimento na BrasilAPI.
- `BATCH_SIZE`: tamanho de cada lote processado.
- `REQUEST_INTERVAL_SECONDS`: intervalo mínimo entre chamadas à BrasilAPI.
- `REQUEST_TIMEOUT_SECONDS`: timeout por requisição.
- `MAX_RETRIES`: total de tentativas em caso de falha.
- `BACKOFF_BASE_SECONDS`: base do backoff progressivo.
- `SERP_API_KEY`: necessária para o módulo de presença online.

## Dados de entrada

O pipeline principal espera pares de arquivos no diretório `data/` com o padrão:

```text
data/estabelecimentos_<indice>.csv
data/empresas_<indice>.csv
```

Exemplo:

```text
data/estabelecimentos_1.csv
data/empresas_1.csv
```

O `main.py` percorre automaticamente todos os pares encontrados.

## Regras de filtragem atuais

As regras principais ficam em [app/config.py](/abs/path/c:/Users/adolf/OneDrive/leadstributarios/app/config.py) e [app/receita.py](/abs/path/c:/Users/adolf/OneDrive/leadstributarios/app/receita.py).

Hoje o projeto trabalha com:

- CNAEs específicos definidos em `CNAES`;
- UFs definidas em `UFS`;
- porte `5`;
- capital social mínimo de `1_000_000.0`;
- opção de aceitar capital social igual a zero;
- naturezas jurídicas específicas em `NATUREZAS_JURIDICAS`;
- situação cadastral ativa (`02`).

Além disso, o código identifica se o match do CNAE veio do principal ou dos secundários, preenchendo:

- `origem_match`
- `cnae_match_secundario`

## Como executar

### 1. Testar conexão com o banco

```bash
python teste_conexao.py
```

### 2. Criar ou atualizar as tabelas

```bash
python criar_tabelas.py
```

Esse script cria as tabelas mapeadas no ORM e também garante a existência das colunas `natureza_juridica` e `whatsapp_valido`.

### 3. Importar base de domínios do HubSpot

Se você tiver o arquivo de exportação do CRM no caminho esperado pelo script:

```bash
python app/scripts/importar_hubspot.py
```

Esse processo popula `hubspot_empresas` para que o pipeline remova leads cujo domínio já exista no HubSpot.

### 4. Rodar o pipeline principal

```bash
python main.py
```

O `main.py` faz:

- leitura dos pares de arquivos da Receita;
- aplicação dos filtros de negócio;
- remoção de CNPJs já salvos no banco;
- enriquecimento em paralelo via BrasilAPI;
- fallback para dados originais quando necessário;
- extração de domínio a partir do e-mail;
- exclusão de leads com domínio já existente no HubSpot;
- inserção no PostgreSQL com `ON CONFLICT DO NOTHING`.

### 5. Validar WhatsApp dos leads

```bash
python validar_whatsapp.py
```

O script:

- busca registros com `telefone` preenchido e `whatsapp_valido IS NULL`;
- abre o WhatsApp Web com sessão persistida em `whatsapp_session/`;
- permite leitura de QR Code apenas na primeira vez;
- marca o lead como `True`, `False` ou mantém `NULL` quando houver timeout.

Observações operacionais:

- o navegador roda em modo visível (`headless=False`);
- existe delay entre validações para reduzir risco de bloqueio;
- a sessão do WhatsApp é reaproveitada entre execuções.

### 6. Exportar a base final

```bash
python exportar.py
```

Por padrão o arquivo gerado é `leads_exportados.xlsx`.

## Scripts auxiliares

### `consultar.py`

Lista todos os leads ou busca por termo em `razao_social`, `municipio` ou `uf`.

```bash
python consultar.py
python consultar.py goias
```

### `limpar_dados.py`

Procura razões sociais duplicadas e remove registros excedentes, tentando preservar a matriz cujo CNPJ tenha ordem `0001`.

```bash
python limpar_dados.py
```

### `remover_empresa.py`

Remove empresas manualmente por razão social exata, ignorando diferença entre maiúsculas e minúsculas.

```bash
python remover_empresa.py
```

### `app/enriquecer_presenca_online.py`

Executa um enriquecimento manual sob demanda para preencher:

- `site`
- `linkedin`
- `tem_site`
- `tem_linkedin`

Esse script usa a SerpAPI e pede os IDs dos leads via terminal.

Importante: o modelo ORM atual em [app/models.py](/abs/path/c:/Users/adolf/OneDrive/leadstributarios/app/models.py) não declara essas colunas, então esse fluxo depende de elas já existirem no banco.

## Arquitetura dos módulos principais

### `app/receita.py`

Responsável por:

- ler os CSVs da Receita em chunks;
- combinar estabelecimentos com empresas;
- aplicar filtros de negócio;
- montar `CNPJ_COMPLETO`;
- identificar match por CNAE principal ou secundário.

### `app/brasilapi.py`

Responsável por:

- consultar `https://brasilapi.com.br/api/cnpj/v1`;
- respeitar um intervalo mínimo entre chamadas;
- aplicar retries com backoff;
- tratar `429 Too Many Requests`.

### `app/pipeline.py`

Responsável por:

- dividir o DataFrame em lotes;
- enriquecer cada lote em paralelo com `ThreadPoolExecutor`;
- transformar a resposta da API em registros prontos para persistência.

### `salvar.py`

Responsável por:

- salvar registros em lote no PostgreSQL;
- evitar duplicidade por `cnpj` com `ON CONFLICT DO NOTHING`;
- consultar CNPJs já existentes antes do processamento.

### `app/hubspot/deduplicador.py`

Responsável por:

- carregar os domínios já cadastrados na tabela `hubspot_empresas`;
- permitir remoção preventiva de leads que já existem no CRM.

## Saídas geradas

As principais saídas do projeto são:

- registros persistidos em `leads_empresas`;
- base deduplicada de domínios em `hubspot_empresas`;
- planilha `leads_exportados.xlsx`;
- sessão persistida do WhatsApp em `whatsapp_session/`.

## Limitações e pontos de atenção

- `requirements.txt` não lista todas as dependências usadas pelos scripts auxiliares.
- O módulo de presença online depende de colunas no banco que não estão refletidas no ORM atual.
- O script de importação do HubSpot usa um nome de arquivo fixo dentro de `data/`.
- O validador de WhatsApp depende da estrutura visual atual do WhatsApp Web e pode exigir ajustes se a interface mudar.
- Há regras de negócio hardcoded em `app/config.py`; para mudar segmentação, é melhor revisar esse arquivo antes de rodar o pipeline.

## Sequência recomendada de uso

1. Configurar `.env`.
2. Validar conexão com o banco.
3. Criar tabelas.
4. Importar domínios do HubSpot.
5. Colocar os arquivos da Receita em `data/`.
6. Rodar `main.py`.
7. Rodar `validar_whatsapp.py`, se quiser qualificar o canal.
8. Rodar `exportar.py`.

## Licença

Projeto de uso interno.

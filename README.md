# 🚀 Leads — Inteligência de Dados & Prospecção

> Pipeline de alta performance desenvolvido em Python para extração, filtragem e enriquecimento de dados da base pública da Receita Federal.
> O projeto transforma dados brutos em leads qualificados com foco em e prospecção B2B.

---

## 📌 Visão Geral

O **Leads** automatiza o processo de:

- Extração de dados da Receita Federal
- Filtragem estratégica de empresas
- Enriquecimento cadastral e digital
- Persistência estruturada em PostgreSQL
- Exportação para análises comerciais

O sistema foi projetado para lidar com grandes volumes de dados utilizando processamento escalável e tolerância a falhas.

---

## ✨ Diferenciais do Projeto

### 🔎 Filtro Inteligente de Origem

Redução automática de ruído ao processar apenas estabelecimentos **Matriz (0001)**, evitando:

- duplicidade de filiais
- desperdício de requisições em APIs
- inconsistência de dados comerciais

### ⚡ Arquitetura Escalável

Processamento em **chunks/lotes**, permitindo trabalhar com:

- milhões de registros
- arquivos massivos da Receita Federal
- baixo consumo de memória RAM

### 🌐 Enriquecimento Multicamada

Integração com APIs externas para complementar os dados públicos:

- **BrasilAPI** → dados cadastrais e QSA
- **SerpAPI** → presença digital, site e LinkedIn

### 🗄️ Persistência Robusta

Gerenciamento completo via **PostgreSQL** com:

- controle de transações
- prevenção de duplicidade
- retomada automática de execução
- consistência operacional

---

## 🛠️ Arquitetura do Sistema

O pipeline operacional é dividido em três etapas principais:

### 1️⃣ Ingestão & Filtro

Responsável por:

- leitura dos CSVs da Receita Federal
- filtragem por: CNAE, UF, Porte e Natureza Jurídica
- validação inicial dos dados

### 2️⃣ Enriquecimento

Consulta e complementação de informações através de APIs externas:

- quadro societário (QSA)
- capital social
- presença online
- site institucional
- LinkedIn corporativo

### 3️⃣ Manutenção & Gestão

Scripts auxiliares para:

- limpeza de registros
- remoção de duplicidades
- exclusão de leads indesejados
- curadoria da base comercial

---

## 📂 Estrutura do Projeto

```
leadstributarios/
├── app/
│   ├── config.py          # Configurações gerais, filtros e variáveis do sistema
│   ├── database.py        # Conexão e sessão com PostgreSQL
│   ├── models.py          # Definição das tabelas SQLAlchemy
│   ├── pipeline.py        # Lógica principal de processamento e concorrência
│   ├── receita.py         # Motor de leitura e filtragem dos CSVs da Receita
│   └── enrichment.py      # Integrações externas (BrasilAPI / SerpAPI / LinkedIn)
│
├── data/                  # Arquivos CSV da Receita Federal
│
├── main.py                # Script principal de execução
├── criar_tabelas.py       # Inicialização da estrutura do banco
├── limpar_dados.py        # Remoção de filiais duplicadas
├── remover_empresa.py     # Exclusão de leads específicos
└── exportar.py            # Geração do relatório final em Excel
```

---

## ⚙️ Instalação e Uso

### 📋 Pré-requisitos

Antes de iniciar, certifique-se de possuir:

- Python 3.12+
- PostgreSQL ativo
- Arquivos da Receita Federal disponíveis na pasta `data/`

### 🔧 Configuração

Crie um arquivo `.env` na raiz do projeto:

```env
DATABASE_URL=postgresql+psycopg2://usuario:senha@localhost:5432/seu_banco

SERP_API_KEY=sua_chave_aqui

MAX_WORKERS=2
BATCH_SIZE=25
```

### ▶️ Execução

**1. Instalar dependências**

```bash
pip install -r requirements.txt
```

**2. Criar estrutura do banco**

```bash
python criar_tabelas.py
```

**3. Iniciar pipeline principal**

```bash
python main.py
```

---

## 🧹 Ferramentas de Manutenção

O projeto inclui scripts auxiliares para garantir a qualidade da base de leads.

### 🧼 `limpar_dados.py`

Analisa o banco em busca de:

- razões sociais duplicadas
- filiais redundantes
- inconsistências cadastrais

Mantém automaticamente apenas o registro da **Matriz**, inclusive em casos onde o CNPJ possui zeros à esquerda.

```bash
python limpar_dados.py
```

### ❌ `remover_empresa.py`

Permite remover rapidamente empresas específicas da base através do nome. Ideal para:

- exclusão de concorrentes
- remoção de empresas inválidas
- limpeza comercial do funil

```bash
python remover_empresa.py
```

### 🌐 Enriquecimento de Presença Online

Busca automaticamente site institucional e LinkedIn corporativo.

```bash
python -m app.enriquecer_presenca_online
```

---

## 📊 Exportação de Dados

O script `exportar.py` gera uma planilha Excel estruturada contendo:

| Categoria | Campos |
|---|---|
| 🏢 **Dados Fiscais** | CNPJ, Razão Social, CNAE Principal, CNAEs Secundários, Natureza Jurídica, Porte |
| 📞 **Contatos** | E-mail, Telefone, Endereço |
| 👥 **Inteligência Empresarial** | Quadro Societário (QSA), Capital Social |
| 🌐 **Presença Digital** | Site Institucional, LinkedIn Corporativo |

```bash
python exportar.py
```

---

## 👨‍💻 Stack Tecnológica

| Tecnologia | Uso |
|---|---|
| Python 3.12 | Linguagem principal |
| PostgreSQL | Banco de dados relacional |
| SQLAlchemy | ORM e gerenciamento de sessões |
| Pandas | Manipulação e análise de dados |
| BrasilAPI | Enriquecimento cadastral |
| SerpAPI | Presença digital e web scraping |
| OpenPyXL | Geração de planilhas Excel |
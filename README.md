# Leads Tributarios

Pipeline em Python para filtrar empresas da base publica da Receita Federal, enriquecer os dados via BrasilAPI e salvar os leads em PostgreSQL.

## Visao geral

O projeto foi estruturado para trabalhar com arquivos grandes da Receita sem estourar memoria e para permitir retomada segura da coleta.

Principais caracteristicas:

- leitura dos CSVs em chunks;
- filtros aplicados antes do enriquecimento para reduzir custo;
- enriquecimento em lotes com controle de taxa para evitar `429`;
- persistencia incremental no banco;
- retomada automatica ao pular CNPJs ja salvos;
- scripts auxiliares para consulta, exportacao e teste de conexao.

## Regras atuais de filtro

No estado atual, o pipeline busca apenas empresas:

- ativas (`SITUACAO_CADASTRAL = 02`);
- com `porte = 5`;
- com capital social maior ou igual a `1.000.000` ou igual a `0`;
- com natureza juridica:
  `2062` - Sociedade Empresaria Limitada
  `2046` - Sociedade Anonima Aberta
  `2054` - Sociedade Anonima Fechada
- dentro dos CNAEs configurados em `app/config.py`;
- dentro das UFs configuradas em `app/config.py`.

## Estrutura do projeto

```text
leadstributarios/
|- app/
|  |- brasilapi.py
|  |- config.py
|  |- database.py
|  |- models.py
|  |- pipeline.py
|  |- receita.py
|  |- utils.py
|- data/
|  |- empresas_0.csv
|  |- estabelecimentos_0.csv
|- consultar.py
|- criar_tabelas.py
|- exportar.py
|- main.py
|- salvar.py
|- teste_conexao.py
|- requirements.txt
```

## Requisitos

- Python 3.12 ou superior
- PostgreSQL
- Arquivos da Receita em `data/`

## Instalacao

1. Crie e ative um ambiente virtual.
2. Instale as dependencias:

```powershell
pip install -r requirements.txt
```

3. Crie um arquivo `.env` com base em `.env.example`.

## Configuracao

Exemplo de `.env`:

```env
DATABASE_URL=postgresql+psycopg2://usuario:senha@host:5432/banco
MAX_WORKERS=2
BATCH_SIZE=50
REQUEST_INTERVAL_SECONDS=1.0
REQUEST_TIMEOUT_SECONDS=20
MAX_RETRIES=5
BACKOFF_BASE_SECONDS=3.0
```

## Uso

Criar ou atualizar a tabela:

```powershell
python criar_tabelas.py
```

Testar conexao com o banco:

```powershell
python teste_conexao.py
```

Executar a coleta:

```powershell
python main.py
```

Consultar os leads salvos:

```powershell
python consultar.py
```

Buscar por termo:

```powershell
python consultar.py sao paulo
```

Exportar os leads:

```powershell
python exportar.py
```

## Comportamento operacional

- `Ctrl+C` interrompe a coleta com seguranca.
- Os lotes concluidos permanecem salvos no banco.
- Ao reiniciar `python main.py`, o pipeline ignora os CNPJs que ja existem na tabela.

## Personalizacao

Os filtros de negocio ficam em `app/config.py`.

Voce pode ajustar:

- CNAEs;
- estados (`UFS`);
- portes;
- capital social minimo;
- naturezas juridicas;
- tamanho do lote;
- numero de workers;
- ritmo das requisicoes.

## Observacoes

- A BrasilAPI pode retornar `429 Too Many Requests` se o ritmo ficar agressivo demais.
- O projeto ja aplica retry e espera entre chamadas, mas ainda assim vale manter configuracoes conservadoras.
- O email e preenchido com prioridade para a BrasilAPI e, quando vazio, usa o `CORREIO_ELETRONICO` da base da Receita.

## Proximos passos recomendados

- adicionar logs estruturados em arquivo;
- separar comandos em uma CLI unica;
- criar migracoes de banco;
- adicionar testes automatizados para filtros e persistencia.

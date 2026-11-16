# B3 Tracker

Um rastreador enxuto de cotações da B3: atualiza os ativos cadastrados, calcula
indicadores básicos e mostra um resumo no terminal ou pelo Telegram, a partir de
uma base local confiável e fácil de consultar. 📈

## O que já faz

- Busca histórico de cotações de ativos brasileiros usando o Yahoo Finance.
- Guarda cotações diárias e cadastro de ativos em um banco DuckDB local.
- Cadastra ativos com validação do ticker, sem duplicar os que já existem.
- Atualiza os ativos cadastrados, buscando dados desde a última data disponível.
- Calcula retorno diário, média móvel de 20 pregões, volatilidade anualizada e
  drawdown.
- Imprime no terminal uma linha por ativo, ordenada pelo ticker.
- Envia o resumo dos ativos por mensagem no Telegram.
- Mantém um bot do Telegram que responde apenas ao dono configurado.
- Registra a execução em arquivo de log com rotação.

> O projeto está em desenvolvimento. A saída é informativa e não constitui
> recomendação de investimento.

## Requisitos

- Python e `pip`.
- Dependências e versões fixadas em [`requirements.txt`](requirements.txt).
- Para os recursos do Telegram: um bot criado pelo
  [@BotFather](https://t.me/BotFather) e o seu `chat_id`.

Na raiz do repositório, instale as dependências:

```bash
python -m pip install -r requirements.txt
```

## Configuração

As configurações sensíveis ficam em um arquivo `.env` na raiz do repositório
(ignorado pelo Git). Use [`.env.example`](.env.example) como modelo:

```bash
cp .env.example .env
```

| Variável           | Uso                                                     |
| ------------------ | ------------------------------------------------------- |
| `TELEGRAM_TOKEN`   | Token do bot, fornecido pelo @BotFather.                |
| `TELEGRAM_CHAT_ID` | Conversa que recebe o resumo e única autorizada no bot. |

As variáveis só são exigidas pelos recursos do Telegram; `main.py` funciona sem
elas. Quando uma delas falta, o programa informa quais estão ausentes.

Para descobrir o seu `chat_id`, preencha o `TELEGRAM_TOKEN`, mande `/start` ao
seu bot e rode:

```bash
python -m scripts.get_chat_id
```

As demais configurações (caminho do banco, limites de cadastro, tentativas de
rede, logging) ficam em [`src/config.py`](src/config.py).

## Executar

Todos os comandos devem ser rodados na raiz do repositório. Os scripts da pasta
`scripts/` são executados como módulos (`python -m scripts.<nome>`), para que
os imports de `src` funcionem.

### Atualizar e ver o resumo no terminal

```bash
python main.py
```

O programa atualiza os ativos registrados e imprime o resumo mais recente. Na
primeira execução, o banco e suas tabelas são criados automaticamente em
`data/b3.duckdb`. Ativos não encontrados, inválidos ou com a fonte indisponível
são avisados no terminal, sem interromper a atualização dos demais.

### Enviar o resumo pelo Telegram

```bash
python -m scripts.send_summary
```

Lê o resumo já guardado no banco e o envia ao `TELEGRAM_CHAT_ID`. Esse comando
**não atualiza** as cotações: rode `main.py` antes para enviar dados recentes.
Resumos longos são divididos em mais de uma mensagem para respeitar o limite de
tamanho do Telegram.

Para apenas testar a conexão com o bot, `python -m scripts.send_test` envia a
mensagem "teste".

### Bot do Telegram

```bash
python -m scripts.run_bot
```

Inicia o bot em modo *polling*. Por enquanto ele responde ao comando `/start`,
e somente na conversa definida em `TELEGRAM_CHAT_ID`; mensagens de outras
conversas são ignoradas.

## Cadastro e escopo dos dados

O programa atualiza **somente os ativos que já estão cadastrados** na tabela
`dim_ticker`; executar `main.py` não adiciona tickers automaticamente. O cadastro
de ativos está disponível pela função `add_tickers` em `src/service.py`. Por
exemplo, a partir da raiz:

```python
from src.database.bootstrap_db import bootstrap_db
from src.database.connect_db import connect
from src.service import add_tickers

with connect(read_only=False) as con:
    bootstrap_db(con)  # cria as tabelas, caso o banco ainda não exista
    print(add_tickers(con, ["PETR4", "VALE3"]))
```

Regras do cadastro:

- O ticker precisa ter de 4 a 8 caracteres alfanuméricos e terminar em dígito.
  O sufixo `.SA` é adicionado automaticamente quando ausente.
- No máximo 10 tickers por chamada.
- Tickers repetidos na entrada são considerados uma vez; os já cadastrados não
  são buscados de novo.
- Cada ativo é gravado em uma transação: ou entram o cadastro e as cotações, ou
  nada é salvo.

A função devolve o resultado de cada ticker:

| Status        | Significado                                   |
| ------------- | --------------------------------------------- |
| `OK`          | Cadastrado com sucesso.                       |
| `EXISTS`      | Já estava cadastrado.                         |
| `INVALID`     | Formato de ticker inválido.                   |
| `NOT_FOUND`   | Ticker sem dados no Yahoo Finance.            |
| `UNAVAILABLE` | Fonte indisponível (rede, bloqueio ou limite). |

Se a fonte ficar indisponível 3 vezes seguidas, os ativos restantes são marcados
como `UNAVAILABLE` sem novas tentativas. A mesma regra vale para a atualização.

O cadastro busca aproximadamente **10 anos de histórico** por ativo. Essa
decisão mantém o banco proporcional aos ativos que a pessoa escolheu acompanhar,
em vez de acumular cotações de todo o mercado.

## Fonte de dados e ajustes

As cotações vêm do [`yfinance`](https://github.com/ranaroussi/yfinance), que
consulta dados disponibilizados pelo Yahoo Finance. Essa é uma integração **não
oficial**: não há garantia de disponibilidade, estabilidade, completude ou
exatidão. Mudanças no serviço, limites de acesso, falhas de rede ou alterações
na biblioteca podem interromper a coleta. Confira os valores em uma fonte
confiável antes de tomar decisões.

O histórico é solicitado com `auto_adjust=True`. Assim, os preços retornados
pelo Yahoo Finance são ajustados para eventos como dividendos e desdobramentos,
conforme os dados fornecidos pela plataforma. Os valores podem diferir de uma
cotação não ajustada exibida por uma corretora.

### Regra B2: atualizar após proventos ou desdobramentos

Uma atualização normal busca os dados desde a última data guardada. Se esse
trecho contiver dividendos ou desdobramentos, a regra B2 considera que o
histórico anterior pode precisar de ajustes: em vez de salvar apenas o trecho
recente, busca novamente o histórico desde a primeira data armazenada e
substitui as cotações correspondentes.

Essa regra mantém a série local coerente com os ajustes retornados pela fonte.
Ela depende dos eventos identificados pelo Yahoo Finance no trecho consultado;
portanto, não elimina as limitações da fonte não oficial.

## Indicadores do resumo

- **Retorno diário:** variação percentual do fechamento em relação ao pregão
  anterior.
- **Média móvel:** média dos últimos 20 pregões.
- **Volatilidade anualizada:** desvio-padrão amostral dos retornos diários dos
  últimos 20 pregões, anualizado usando `√252`.
- **Drawdown:** distância percentual do fechamento atual em relação ao maior
  fechamento observado na série do ativo.

Os indicadores usam as cotações ajustadas disponíveis no banco. O resumo exibe
o registro mais recente de cada ativo.

## Banco de dados

O banco DuckDB em `data/b3.duckdb` tem três tabelas:

- `dim_date`: calendário diário de 2016-01-01 a 2035-12-31.
- `dim_ticker`: ativos cadastrados e seus nomes.
- `daily_quotes`: cotações diárias (abertura, máxima, mínima, fechamento e
  volume) por ativo e data.

## Logs

Cada execução registra eventos em `logs/b3_tracker.log` (nível `DEBUG`) e no
terminal (nível `INFO`). O arquivo é rotacionado ao atingir cerca de 1 MB,
mantendo até 5 cópias anteriores. Os logs de bibliotecas externas são reduzidos
para evitar ruído.

## Estrutura

```text
main.py                 # Atualiza o banco e exibe o resumo no terminal
scripts/
  send_summary.py       # Envia o resumo pelo Telegram
  run_bot.py            # Inicia o bot do Telegram
  get_chat_id.py        # Descobre o chat_id da conversa com o bot
  send_test.py          # Envia uma mensagem de teste
src/
  config.py             # Configurações e leitura do .env
  service.py            # Cadastro e atualização dos ativos
  summary.py            # Formatação dos valores para o terminal
  errors.py             # Exceções do projeto
  logging_config.py     # Configuração dos logs
  sources/yahoo.py      # Coleta e preparação dos dados do Yahoo Finance
  database/             # Conexão, esquema, carga e consultas DuckDB
  bot/                  # Cliente, bot e mensagens do Telegram
data/
  b3.duckdb             # Banco local criado na execução
logs/
  b3_tracker.log        # Log da aplicação
```

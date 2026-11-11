# B3 Tracker

Um rastreador enxuto de cotações da B3: atualiza os ativos cadastrados, calcula
indicadores básicos e mostra um resumo direto no terminal. Sem dashboard por
enquanto — primeiro, uma base local confiável e fácil de consultar. 📈

## O que já faz

- Busca histórico de cotações de ativos brasileiros usando o Yahoo Finance.
- Guarda cotações diárias e cadastro de ativos em um banco DuckDB local.
- Atualiza os ativos que já estão cadastrados, buscando dados desde a última
  data disponível.
- Calcula retorno diário, média móvel de 20 pregões, volatilidade anualizada e
  drawdown.
- Imprime no terminal uma linha por ativo, ordenada pelo ticker.
- Mostra um aviso quando ainda não há ativos cadastrados.

> O projeto está em desenvolvimento. A saída é informativa e não constitui
> recomendação de investimento.

## Requisitos

- Python e `pip`.
- Dependências e versões fixadas em [`requirements.txt`](requirements.txt).

Na raiz do repositório, instale as dependências:

```bash
python -m pip install -r requirements.txt
```

## Executar

Na raiz do repositório, rode:

```bash
python main.py
```

O programa atualiza os ativos registrados e imprime o resumo mais recente. Na
primeira execução, o banco e suas tabelas são criados automaticamente em
`data/b3.duckdb`.

## Cadastro e escopo dos dados

O programa atualiza **somente os ativos que já estão cadastrados** na tabela
`dim_ticker`; executar `main.py` não adiciona tickers automaticamente. O cadastro
de ativos está disponível pela função `add_tickers` em `src/service.py`. Por
exemplo, a partir da raiz:

```python
from src.database.connect_db import connect
from src.service import add_tickers

con = connect(read_only=False)
try:
    print(add_tickers(con, ["PETR4", "VALE3"]))
finally:
    con.close()
```

O cadastro busca aproximadamente **10 anos de histórico** por ativo. Essa
decisão mantém o banco proporcional aos ativos que a pessoa escolheu acompanhar,
em vez de acumular cotações de todo o mercado. Uma solução para ampliar a
escala — por exemplo, ingestão mais abrangente ou armazenamento histórico maior
— fica para uma etapa futura.

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
- **Volatilidade anualizada:** desvio-padrão amostral dos retornos diários,
  anualizado usando `√252`.
- **Drawdown:** distância percentual do fechamento atual em relação ao maior
  fechamento observado na série do ativo.

Os indicadores usam as cotações ajustadas disponíveis no banco. O resumo exibe
o registro mais recente de cada ativo.

## Estrutura

```text
main.py                 # Atualiza o banco e exibe o resumo
src/
  service.py            # Cadastro e atualização dos ativos
  summary.py            # Formatação dos valores para o terminal
  sources/yahoo.py      # Coleta e preparação dos dados do Yahoo Finance
  database/             # Conexão, esquema, carga e consultas DuckDB
data/
  b3.duckdb             # Banco local criado na execução
```

class LimiteExcedidoError(ValueError):
    """Mais tickers numa mensagem do que o permitido."""

class FonteError(Exception):
    """Erro ao obter dados da fonte."""

class TickerNaoEncontradoError(FonteError):
    """O ticker não existe ou não tem dados na fonte"""

class FonteIndisponivelError(FonteError):
    """A fonte não respondeu (rede, bloqueio ou limite de requisições)."""
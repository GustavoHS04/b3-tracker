import pandas as pd

def build_summary_blocks(df: pd.DataFrame) -> list[str]:
    blocks = ["Resumo dos ativos"]
    for row in df.to_dict("records"):
        blocks.append(
            f"{row['ticker']} ({row['date']})\n"
            f"Fechamento:   R${row['close']} | Dia: {row['daily_return']}\n"
            f"Média móvel:  R${row['moving_avg']} | Volatilidade {row['volatility_ann']}\n"
            f"Drawdown:     {row['drawdown']}"
        )

    return blocks

def split_message(blocks: list[str], limit: int) -> list[str]:
    messages = []
    current = ""

    for block in blocks:
        block = block.strip()
        if not block:
            continue
        if len(block) > limit:
            raise ValueError(f"Bloco de {len(block)} caracteres excede o limite de {limit}.")

        candidate = f"{current}\n\n{block}" if current else block
        if len(candidate) <= limit:
            current = candidate
        else:
            messages.append(current)
            current = block

    if current:
        messages.append(current)

    return messages
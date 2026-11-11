import pandas as pd

FORMATOS = {
    "daily_return": ".2%",
    "volatility_ann": ".2%",
    "drawdown": ".2%",
    "close": ".2f",
    "moving_avg": ".2f",
}

def format_summary(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()

    out["volatility"] = out["volatility"] * 252 ** 0.5
    out = out.rename(columns={"volatility": "volatility_ann"})

    for col, fmt in FORMATOS.items():
        out[col] = out[col].map(lambda v: "-" if pd.isna(v) else f"{v:{fmt}}")

    return out
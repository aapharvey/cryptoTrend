import pandas as pd

def ema(series: pd.Series, window: int) -> pd.Series:
    return series.ewm(span=window, adjust=False).mean()

def supertrend(df: pd.DataFrame, period: int = 10, multiplier: float = 3.0) -> pd.Series:
    hl2 = (df['high'] + df['low']) / 2.0
    tr1 = df['high'] - df['low']
    tr2 = (df['high'] - df['close'].shift()).abs()
    tr3 = (df['low'] - df['close'].shift()).abs()
    tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
    atr = tr.ewm(alpha=1/period, adjust=False).mean()

    upperband = hl2 + multiplier * atr
    lowerband = hl2 - multiplier * atr

    st = pd.Series(index=df.index, dtype=float)
    direction = pd.Series(index=df.index, dtype=int)

    st.iloc[0] = upperband.iloc[0]
    direction.iloc[0] = 1  # 1=downtrend band, -1=uptrend band for init

    for i in range(1, len(df)):
        if df['close'].iloc[i] > st.iloc[i-1]:
            direction.iloc[i] = -1  # uptrend -> use lower band
        elif df['close'].iloc[i] < st.iloc[i-1]:
            direction.iloc[i] = 1   # downtrend -> use upper band
        else:
            direction.iloc[i] = direction.iloc[i-1]

        if direction.iloc[i] == -1:
            st.iloc[i] = max(lowerband.iloc[i], st.iloc[i-1])
        else:
            st.iloc[i] = min(upperband.iloc[i], st.iloc[i-1])

    return st

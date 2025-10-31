def timeframe_to_ms(tf: str) -> int:
    unit = tf[-1]
    value = int(tf[:-1])
    if unit == 'm':
        return value * 60_000
    if unit == 'h':
        return value * 60 * 60_000
    if unit == 'd':
        return value * 24 * 60 * 60_000
    raise ValueError(f"Unsupported timeframe: {tf}")

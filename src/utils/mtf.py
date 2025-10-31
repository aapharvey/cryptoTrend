import pandas as pd

def align_to_lower_tf(higher_tf_series: pd.Series, lower_index: pd.DatetimeIndex) -> pd.Series:
    s = higher_tf_series.copy().sort_index()
    return s.reindex(lower_index, method='ffill')

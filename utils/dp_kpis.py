import pandas as pd

class DPKPIs:
    def __init__(self, df):
        self.df = df.copy()
        self.prefix_sums = {}
        for col in df.select_dtypes(include='number').columns:
            self.prefix_sums[col] = df[col].cumsum()

    def total(self, col, start_idx=0, end_idx=None):
        """Return total of column from start_idx to end_idx"""
        if end_idx is None:
            end_idx = len(self.df) - 1
        if start_idx == 0:
            return self.prefix_sums[col].iloc[end_idx]
        else:
            return self.prefix_sums[col].iloc[end_idx] - self.prefix_sums[col].iloc[start_idx - 1]

# ml_pipeline/forecast.py
import pandas as pd
from prophet import Prophet

def forecast_sales(df, date_col="timestamp", value_col="amount", periods=30):
    """
    Forecast next 'periods' days using Prophet
    """
    df_forecast = df[[date_col, value_col]].rename(columns={date_col: "ds", value_col: "y"})
    model = Prophet()
    model.fit(df_forecast)
    future = model.make_future_dataframe(periods=periods)
    forecast = model.predict(future)
    return forecast

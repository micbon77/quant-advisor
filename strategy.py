import pandas as pd
import numpy as np

def compute_indicators(df, sma_period=200, mom_period=252):
    """
    Compute the necessary indicators for the strategy.
    Expects a DataFrame with a 'Close' column.
    """
    if 'Close' not in df.columns:
        return df
    
    # Extract close prices
    close = df['Close']
    
    # 200-day SMA
    df['SMA'] = close.rolling(window=sma_period).mean()
    
    # 12-month (252 days) Momentum: (Current - Past) / Past
    df['Momentum'] = close.pct_change(periods=mom_period)
    
    return df

def generate_signals(df):
    """
    Generate daily signals based on indicators.
    BUY if Close > SMA AND Momentum > 0.
    Else CASH.
    """
    if 'Close' not in df.columns or 'SMA' not in df.columns or 'Momentum' not in df.columns:
        return df
        
    df['Signal_Daily'] = "CASH"
    
    # Condition: Close > SMA and Momentum > 0
    buy_condition = (df['Close'] > df['SMA']) & (df['Momentum'] > 0)
    
    df.loc[buy_condition, 'Signal_Daily'] = "BUY"
    
    return df

def apply_monthly_rebalancing(df):
    """
    Filter the daily signals to only trigger rebalancing on the last trading day of the month.
    """
    df['Signal'] = "CASH" 
    df['Is_Month_End'] = False
    
    # Identify the last trading day of each month
    df['YearMonth'] = df.index.to_period('M')
    
    # Find the max date for each month
    month_end_dates = df.groupby('YearMonth').apply(lambda x: x.index.max())
    
    df.loc[df.index.isin(month_end_dates), 'Is_Month_End'] = True
    
    # Forward fill the signal from the end of the month
    df['Actionable_Signal'] = None
    df.loc[df['Is_Month_End'], 'Actionable_Signal'] = df.loc[df['Is_Month_End'], 'Signal_Daily']
    
    df['Signal'] = df['Actionable_Signal'].ffill().fillna("CASH")
    
    # Clean up
    df = df.drop(columns=['YearMonth', 'Actionable_Signal'])
    
    return df

def run_strategy(df, sma_period=200, mom_period=252):
    df = df.copy()
    df = compute_indicators(df, sma_period, mom_period)
    df = generate_signals(df)
    df = apply_monthly_rebalancing(df)
    return df

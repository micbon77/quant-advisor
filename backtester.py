import pandas as pd
import numpy as np

def run_backtest(df, initial_capital=10000, transaction_fee=2.0):
    """
    Run backtest on a single asset DataFrame.
    """
    df = df.copy()
    
    if len(df) == 0 or 'Signal' not in df.columns:
        return df, {}
        
    # "BUY" = 1.0 (100% invested), "CASH" = 0.0
    df['Target_Position'] = np.where(df['Signal'] == 'BUY', 1.0, 0.0)
    
    # Prevent look-ahead bias: Signal from day t is actionable on day t+1
    df['Actual_Position'] = df['Target_Position'].shift(1).fillna(0.0)
    
    df['Asset_Return'] = df['Close'].pct_change().fillna(0)
    df['Strategy_Return'] = df['Actual_Position'] * df['Asset_Return']
    
    # Trading fees calculation
    df['Trade_Flag'] = df['Actual_Position'].diff().abs().fillna(0)
    df['Fee_Impact'] = np.where(df['Trade_Flag'] > 0, transaction_fee, 0.0)
    
    capital = initial_capital
    equity_curve = []
    
    for idx, row in df.iterrows():
        daily_pnl = capital * row['Strategy_Return']
        capital += daily_pnl
        capital -= row['Fee_Impact']
        equity_curve.append(capital)
        
    df['Strategy_Equity'] = equity_curve
    df['BnH_Equity'] = initial_capital * (1 + df['Asset_Return']).cumprod()
    
    metrics = calculate_metrics(df, initial_capital)
    
    return df, metrics

def calculate_metrics(df, initial_capital):
    if len(df) == 0:
        return {}
        
    final_equity = df['Strategy_Equity'].iloc[-1]
    cum_return = (final_equity / initial_capital) - 1
    
    peak = df['Strategy_Equity'].cummax()
    drawdown = (df['Strategy_Equity'] - peak) / peak
    max_drawdown = drawdown.min()
    
    strat_pct_ret = df['Strategy_Equity'].pct_change().fillna(0)
    mean_ret = strat_pct_ret.mean()
    std_ret = strat_pct_ret.std()
    
    sharpe = np.sqrt(252) * mean_ret / std_ret if std_ret > 0 else 0
    
    trades = []
    entry_price = 0
    for idx, row in df.iterrows():
        if row['Trade_Flag'] > 0:
            if row['Actual_Position'] == 1.0: 
                entry_price = row['Close']
            elif row['Actual_Position'] == 0.0 and entry_price > 0: 
                trades.append((row['Close'] - entry_price) / entry_price)
                entry_price = 0
                
    if len(trades) > 0:
        wins = [t for t in trades if t > 0]
        win_rate = len(wins) / len(trades)
    else:
        win_rate = 0.0
        
    return {
        "Rendimento Totale (%)": cum_return * 100,
        "Drawdown Massimo (%)": max_drawdown * 100,
        "Indice di Sharpe": sharpe,
        "Tasso di Vittoria (%)": win_rate * 100,
        "Trade Totali": len(trades)
    }

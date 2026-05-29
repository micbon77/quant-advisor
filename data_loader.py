import yfinance as yf
import pandas as pd
import os
from datetime import datetime, timedelta

DATA_DIR = "data"

def load_data(tickers=["SPY", "QQQ", "GLD", "TLT", "BITO"], years=10):
    """
    Load daily OHLCV data for the given tickers.
    Uses local cache if available to prevent rate limiting.
    """
    if not os.path.exists(DATA_DIR):
        os.makedirs(DATA_DIR)
        
    end_date = datetime.now()
    start_date = end_date - timedelta(days=365 * years)
    
    data_dict = {}
    
    for ticker in tickers:
        file_path = os.path.join(DATA_DIR, f"{ticker}.csv")
        
        if os.path.exists(file_path):
            # Load from cache
            df = pd.read_csv(file_path, index_col=0, parse_dates=True)
            # Ensure timezone is removed
            if df.index.tz is not None:
                df.index = df.index.tz_localize(None)
        else:
            # Download from yfinance
            df = yf.download(ticker, start=start_date.strftime("%Y-%m-%d"), end=end_date.strftime("%Y-%m-%d"))
            
            # Flatten MultiIndex columns if present
            if isinstance(df.columns, pd.MultiIndex):
                df.columns = df.columns.get_level_values(0)
            
            # Clean datetime index
            if df.index.tz is not None:
                df.index = df.index.tz_localize(None)
            
            # Save to cache
            df.to_csv(file_path)
            
        data_dict[ticker] = df
        
    return data_dict

if __name__ == "__main__":
    # Simple test to verify the loader
    print("Loading data...")
    data = load_data()
    for t, d in data.items():
        print(f"{t}: {len(d)} rows from {d.index.min().date() if len(d) > 0 else 'N/A'} to {d.index.max().date() if len(d) > 0 else 'N/A'}")

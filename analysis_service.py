# analysis_service.py
import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import train_test_split
from sqlalchemy import create_engine
from config import POSTGRES_USER, POSTGRES_PASSWORD

class StockAnalyzer:
    def __init__(self):
        self.engine = create_engine(
            f"postgresql://{POSTGRES_USER}:{POSTGRES_PASSWORD}@localhost:5432/stock_data"
        )
    
    def load_data(self, symbol, lookback_days=30):
        """Flexible data loader that handles both database and direct DataFrames"""
        if isinstance(symbol, pd.DataFrame):
            # If a DataFrame is passed directly
            df = symbol.copy()
            # Standardize column names
            df.columns = [col.lower() for col in df.columns]
            return df.tail(lookback_days)
        else:
            # Database loading
            query = f"""
            SELECT date, open, high, low, close, volume 
            FROM stock_prices 
            WHERE symbol = '{symbol}'
            ORDER BY date DESC 
            LIMIT {lookback_days}
            """
            return pd.read_sql(query, self.engine)
    
    def predict_next_day(self, symbol):
        """Enhanced prediction with flexible data source"""
        df = self.load_data(symbol)
        
        if len(df) < 10:
            raise ValueError("Need at least 10 days of historical data")
        
        # Flexible column naming
        cols = {
            'open': 'open' if 'open' in df.columns else 'Open',
            'high': 'high' if 'high' in df.columns else 'High',
            'low': 'low' if 'low' in df.columns else 'Low',
            'close': 'close' if 'close' in df.columns else 'Close',
            'volume': 'volume' if 'volume' in df.columns else 'Volume'
        }
        
        # Feature engineering
        df['returns'] = df[cols['close']].pct_change()
        df['ma_5'] = df[cols['close']].rolling(5).mean()
        df.dropna(inplace=True)
        
        # Prepare data
        features = [cols['open'], cols['high'], cols['low'], cols['volume'], 'ma_5']
        X = df[features]
        y = df[cols['close']]
        
        # Train model
        model = RandomForestRegressor(n_estimators=100)
        model.fit(X, y)
        
        # Predict
        last_record = X.iloc[-1].values.reshape(1, -1)
        return {
            "symbol": symbol if isinstance(symbol, str) else "Current",
            "predicted_close": round(model.predict(last_record)[0], 2),
            "accuracy": round(model.score(X, y), 2),
            "last_close": df[cols['close']].iloc[-1]
        }

    def detect_trends(self, symbol):
        """Trend detection with column name flexibility"""
        df = self.load_data(symbol)

        if 'date' not in df.columns:
            df = df.rename(columns={'Date': 'date'})  # Handle capital D
        
        if df.empty:
            return []
            
        close_col = 'close' if 'close' in df.columns else 'Close'
        date_col = 'date' if 'date' in df.columns else 'Date'
        
        df['trend'] = np.where(
            df[close_col].rolling(5).mean().diff() > 0,
            'Up',
            'Down'
        )
        return df[[date_col, close_col, 'trend']].tail(10).to_dict('records')
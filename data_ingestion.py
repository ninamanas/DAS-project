import streamlit as st
import yfinance as yf
import requests
import plotly.express as px  # Changed from pe to px for consistency
import io
import pandas as pd
import numpy as np
from sklearn.linear_model import LinearRegression
from sklearn.model_selection import train_test_split
from confluent_kafka import Producer
from analysis_service import StockAnalyzer
import joblib
import os
from datetime import datetime, timedelta

# Kafka Settings
KAFKA_BOOTSTRAP_SERVERS = 'localhost:9092'
TOPIC_NAME = 'stock_data'

# Create Kafka Producer
producer = Producer({
    'bootstrap.servers': KAFKA_BOOTSTRAP_SERVERS,
    'client.id': 'stock_producer'
})

# Alpha Vantage API Key
ALPHA_VANTAGE_API_KEY = "7ASO8FHHMLSPJ34V"

# Create models directory if it doesn't exist
os.makedirs("models", exist_ok=True)

st.set_page_config(layout="wide")
st.title("Yahoo Stock Dashboard 📈")

def train_and_predict(data, ticker):
    """Train model and make predictions"""
    try:
        # Prepare data - use previous day's close to predict next day's close
        df = data.copy()
        df['prev_close'] = df['Close'].shift(1)
        df['target'] = df['Close'].shift(-1)  # Predicting next day's close
        df = df.dropna()
        
        if len(df) < 10:
            st.warning("Not enough historical data to train model")
            return None, None

        X = df[['prev_close']]
        y = df['target']
        
        # Split data
        X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, shuffle=False)
        
        # Train model
        model = LinearRegression()
        model.fit(X_train, y_train)
        
        # Save model
        model_path = f"models/{ticker}_model.pkl"
        joblib.dump(model, model_path)
        
        # Make prediction for next day
        last_close = df['Close'].iloc[-1]
        next_day_pred = model.predict([[last_close]])[0]
        
        # Calculate model accuracy
        accuracy = model.score(X_test, y_test)
        
        return next_day_pred, accuracy
        
    except Exception as e:
        st.error(f"Prediction error: {str(e)}")
        return None, None

@st.cache_data
def get_ticker_list():
    url = f"https://www.alphavantage.co/query?function=LISTING_STATUS&apikey={ALPHA_VANTAGE_API_KEY}"
    response = requests.get(url)
    if response.status_code == 200:
        try:
            data = pd.read_csv(io.StringIO(response.text))
            return sorted(data["symbol"].dropna().astype(str).tolist()) if "symbol" in data.columns else ["AAPL", "MSFT"]
        except:
            return ["AAPL", "MSFT"]
    return ["AAPL", "MSFT"]

# Sidebar Inputs
ticker_list = get_ticker_list()
ticker_symbol = st.sidebar.selectbox("Select Ticker Symbol", ticker_list)
start_date = st.sidebar.date_input("Start date")
end_date = st.sidebar.date_input("End date")

if ticker_symbol:
    st.subheader(f"{ticker_symbol} Stock Overview")
    stockData = yf.download(ticker_symbol, start=start_date, end=end_date, auto_adjust=False)

    if stockData.empty:
        st.error(f"No data available for {ticker_symbol} between {start_date} and {end_date}.")
    else:
        # Send Data to Kafka
        stockData.reset_index(inplace=True)
        stockData['symbol'] = ticker_symbol
        data_to_send = stockData.to_dict(orient='records')
        
        try:
            for data in data_to_send:
                producer.produce(TOPIC_NAME, value=str(data).encode('utf-8'))
            producer.flush()
        except Exception as e:
            st.error(f"Error sending data to Kafka: {e}")
        
        # Display tabs
        price_tab, history_tab, chart_tab, pred_tab = st.tabs(["Price Summary", "Historical Data", "Charts", "Predictions"])
        
        with price_tab:
            st.write("Price Summary")
            st.write(stockData)
        
        with history_tab:
            st.write("Historical Data")
            st.write(stockData)
        
        with chart_tab:
            st.write("Charts")
            stockData.columns = [col[0] if isinstance(col, tuple) else col for col in stockData.columns]
            date_col = "Date"
            adj_close_col = "Adj Close"
            close_col = "Close"

            if adj_close_col in stockData.columns:
                line_chart = px.line(stockData, x=date_col, y=adj_close_col, title=f"{ticker_symbol} Adjusted Close Prices")
                st.plotly_chart(line_chart)
            else:
                st.warning(f"'{adj_close_col}' column is not available. Using 'Close' prices instead.")
                line_chart = px.line(stockData, x=date_col, y=close_col, title=f"{ticker_symbol} Close Prices")
                st.plotly_chart(line_chart)

        with pred_tab:
            st.header("Stock Price Prediction")
            
            if st.button("Predict Next Day Closing Price"):
                with st.spinner("Training model and making prediction..."):
                    # Ensure we have the right column names
                    stockData.columns = [col[0] if isinstance(col, tuple) else col for col in stockData.columns]
                    
                    prediction, accuracy = train_and_predict(stockData, ticker_symbol)
                    
                    if prediction is not None and accuracy is not None:
                        current_price = stockData['Close'].iloc[-1]
                        change = ((prediction - current_price) / current_price) * 100
                        
                        col1, col2, col3 = st.columns(3)
                        col1.metric("Current Price", f"${current_price:.2f}")
                        col2.metric("Predicted Price", f"${prediction:.2f}", f"{change:.2f}%")
                        col3.metric("Model Accuracy", f"{accuracy*100:.1f}%")
                        
                        st.info("Note: Predictions are based on historical price patterns and may not account for all market factors.")
                        
                        # Show historical vs predicted
                        history = stockData.set_index('Date')['Close']
                        last_date = history.index[-1]
                        next_date = last_date + timedelta(days=1)
                        
                        fig = px.line(history, title=f"{ticker_symbol} Price History with Prediction")
                        fig.add_scatter(x=[next_date], y=[prediction], 
                                      mode='markers', name='Prediction',
                                      marker=dict(color='red', size=10))
                        st.plotly_chart(fig)
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from sqlalchemy import create_engine
from analysis_service import StockAnalyzer
from config import POSTGRES_USER, POSTGRES_PASSWORD

# Initialize services
@st.cache_resource
def init_connection():
    return create_engine(
        f"postgresql://{POSTGRES_USER}:{POSTGRES_PASSWORD}@localhost:5432/stock_data"
    )

engine = init_connection()
analyzer = StockAnalyzer()

# Streamlit UI
st.set_page_config(layout="wide")
st.title("Stock Analytics Dashboard 📊")

def load_data():
    """Load data from PostgreSQL with standardized column names"""
    df = pd.read_sql("SELECT * FROM stock_prices ORDER BY date DESC LIMIT 1000", engine)
    if not df.empty:
        # Standardize column names
        df.columns = [col.lower() for col in df.columns]
        df['date'] = pd.to_datetime(df['date'])
    return df

df = load_data()

if not df.empty:
    tab1, tab2, tab3 = st.tabs(["Trend Analysis", "OHLC Charts", "Predictions"])
    
    with tab1:
        st.subheader("Price Trends")
        selected_stock = st.selectbox("Select Stock", df['symbol'].unique(), key='trend_stock')
        stock_df = df[df['symbol'] == selected_stock]
        fig = px.line(stock_df, x='date', y='close', title=f"{selected_stock} Closing Prices")
        st.plotly_chart(fig, use_container_width=True)
    
    with tab2:
        st.subheader("OHLC Analysis")
        selected_stock = st.selectbox("Select Stock", df['symbol'].unique(), key='ohlc_stock')
        stock_df = df[df['symbol'] == selected_stock]
        
        fig = go.Figure(go.Candlestick(
            x=stock_df['date'],
            open=stock_df['open'],
            high=stock_df['high'],
            low=stock_df['low'],
            close=stock_df['close']
        ))
        fig.update_layout(
            title=f"{selected_stock} OHLC Prices",
            xaxis_title="Date",
            yaxis_title="Price"
        )
        st.plotly_chart(fig, use_container_width=True)
    
    with tab3:
        st.header("Stock Predictions")
    selected_stock = st.selectbox("Select Stock", df['symbol'].unique(), key='pred_stock')
    
    if st.button("Generate Prediction"):
        with st.spinner("Analyzing..."):
            try:
                prediction = analyzer.predict_next_day(selected_stock)
                
                col1, col2 = st.columns(2)
                col1.metric("Current Price", f"${prediction['last_close']:.2f}")
                col2.metric(
                    "Predicted Price", 
                    f"${prediction['predicted_close']:.2f}",
                    f"{((prediction['predicted_close'] - prediction['last_close']) / prediction['last_close'] * 100):.2f}%"
                )
                
                st.progress(int(prediction['accuracy'] * 100))
                st.caption(f"Model Confidence: {prediction['accuracy']*100:.1f}%")
            
            except ValueError as e:
                st.warning(str(e))
            except Exception as e:
                st.error(f"Prediction failed: {str(e)}")

else:
    st.warning("No data found in database. Please run data ingestion first.")
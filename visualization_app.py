import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import requests
from datetime import datetime, timedelta
from analysis_service import StockAnalyzer
from config import ALPHA_VANTAGE_API_KEY

# Конфигурација на страницата
st.set_page_config(
    page_title="📊 Stock Analytics Dashboard",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Иницијализација на анализаторот
analyzer = StockAnalyzer()

# CSS стилови за подобар изглед
st.markdown("""
    <style>
    .sidebar .sidebar-content {
        background-color: #f0f2f6;
    }
    .stButton>button {
        width: 100%;
    }
    </style>
    """, unsafe_allow_html=True)

def fetch_stock_data(symbol):
    """Зема податоци од Alpha Vantage API"""
    try:
        url = f"https://www.alphavantage.co/query?function=TIME_SERIES_DAILY&symbol={symbol}&apikey={ALPHA_VANTAGE_API_KEY}"
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()
        
        if 'Time Series (Daily)' not in data:
            st.error(f"Грешка во податоците за {symbol}: {data.get('Note', 'Непозната грешка')}")
            return pd.DataFrame()
            
        time_series = data['Time Series (Daily)']
        df = pd.DataFrame.from_dict(time_series, orient='index')
        
        # Преименување на колони
        df = df.rename(columns={
            '1. open': 'open',
            '2. high': 'high',
            '3. low': 'low',
            '4. close': 'close',
            '5. volume': 'volume'
        })
        
        # Конвертирање на типови
        df.index = pd.to_datetime(df.index)
        df = df.astype({
            'open': float,
            'high': float,
            'low': float,
            'close': float,
            'volume': int
        })
        
        df['symbol'] = symbol
        return df.sort_index(ascending=True)
        
    except Exception as e:
        st.error(f"Грешка при вчитување на податоци: {str(e)}")
        return pd.DataFrame()

# Секција за sidebar
with st.sidebar:
    st.header("🔧 Контролен Панел")
    
    # Избор на акција
    symbols = ['AAPL', 'MSFT', 'GOOGL', 'AMZN', 'TSLA', 'META', 'NFLX']
    selected_symbol = st.selectbox("Избери акција:", symbols, index=0)
    
    # Опции
    days_to_show = st.slider("Број на денови за приказ:", 7, 365, 30)
    show_volume = st.checkbox("Прикажи волумен", True)
    
    # Копче за вчитување
    fetch_data = st.button("Преземи податоци", type="primary")

# Главен панел
st.title(f"📈 Анализа на акции: {selected_symbol if 'selected_symbol' in locals() else ''}")

if fetch_data and selected_symbol:
    with st.spinner(f"Вчитувам податоци за {selected_symbol}..."):
        df = fetch_stock_data(selected_symbol)
        
        if not df.empty:
            # Ограничи ги податоците според избраниот период
            df = df.tail(days_to_show)
            
            # Прикажи основни метрики
            col1, col2, col3 = st.columns(3)
            col1.metric("Тековна цена", f"${df['close'].iloc[-1]:.2f}")
            col2.metric("Промена (1 ден)", 
                        f"${df['close'].iloc[-1] - df['close'].iloc[-2]:.2f}", 
                        f"{(df['close'].iloc[-1]/df['close'].iloc[-2]-1)*100:.2f}%")
            col3.metric("Високо/Ниско", 
                       f"${df['high'].max():.2f}", 
                       f"${df['low'].min():.2f}")
            
            # Табови за различни анализи
            tab1, tab2, tab3 = st.tabs(["Тренд", "OHLC", "Прогнози"])
            
            with tab1:
                st.subheader("Ценовен тренд")
                fig = px.line(df, x=df.index, y='close', 
                             title=f"Затворени цени за {selected_symbol}")
                st.plotly_chart(fig, use_container_width=True)
                
                if show_volume:
                    st.subheader("Волумен на тргување")
                    fig2 = px.bar(df, x=df.index, y='volume')
                    st.plotly_chart(fig2, use_container_width=True)
            
            with tab2:
                st.subheader("OHLC Анализа")
                fig = go.Figure(go.Candlestick(
                    x=df.index,
                    open=df['open'],
                    high=df['high'],
                    low=df['low'],
                    close=df['close']
                ))
                fig.update_layout(title=f"OHLC график за {selected_symbol}")
                st.plotly_chart(fig, use_container_width=True)
            
            with tab3:
                st.subheader("Прогнози")
                if st.button("Направи прогноза"):
                    with st.spinner("Правам анализа..."):
                        try:
                            prediction = analyzer.predict_next_day(df)
                            
                            st.metric("Прогнозирана цена", 
                                     f"${prediction['predicted_close']:.2f}",
                                     f"{prediction['change_percent']:.2f}%")
                            
                            st.info(f"Точност на модел: {prediction['accuracy']*100:.1f}%")
                        except Exception as e:
                            st.error(f"Грешка при прогнозирање: {str(e)}")
        else:
            st.warning("Не се пронајдени податоци за избраната акција.")
else:
    st.info("Изберете акција и кликнете на 'Преземи податоци' за да започнете.")
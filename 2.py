import pandas as pd
import streamlit as st
import plotly.express as px

# Load dataset
file_path = "merge.csv"
df = pd.read_csv(file_path)

# Clean Data and Ensure Numeric Conversion
df = df.dropna(subset=['LOW_PRICE', 'CLOSE_PRIC'])
df['CLOSE_PRIC'] = pd.to_numeric(df['CLOSE_PRIC'], errors='coerce')
df['LOW_PRICE'] = pd.to_numeric(df['LOW_PRICE'], errors='coerce')

# Calculate Gain % Using Last Close Price and Historic Low Price
df_grouped = df.groupby(['TICKER', 'EXPIRY', 'TYPE', 'STRIKE PRICE'])
df_low = df_grouped['LOW_PRICE'].min().reset_index()
df_close = df_grouped['CLOSE_PRIC'].last().reset_index()
df = pd.merge(df_low, df_close, on=['TICKER', 'EXPIRY', 'TYPE', 'STRIKE PRICE'])
df['GAIN_PERCENT'] = ((df['CLOSE_PRIC'] - df['LOW_PRICE']) / df['LOW_PRICE']) * 100

# Streamlit UI
st.title("📈 Options Price Gain Tracker")

# Filters
ticker = st.sidebar.selectbox("Select Ticker", ["All"] + list(df['TICKER'].unique()))
expiry = st.sidebar.selectbox("Select Expiry Date", ["All"] + list(df['EXPIRY'].unique()))
type_filter = st.sidebar.selectbox("Select Option Type", ["All"] + list(df['TYPE'].unique()))
gain_threshold = st.sidebar.slider("Gain % Threshold", min_value=1, max_value=3000, value=500, step=50)

df_filtered = df[df['GAIN_PERCENT'] >= gain_threshold]
if ticker != "All":
    df_filtered = df_filtered[df_filtered['TICKER'] == ticker]
if expiry != "All":
    df_filtered = df_filtered[df_filtered['EXPIRY'] == expiry]
if type_filter != "All":
    df_filtered = df_filtered[df_filtered['TYPE'] == type_filter]

# Display Table
st.dataframe(df_filtered[['TICKER', 'EXPIRY', 'TYPE', 'STRIKE PRICE','CLOSE_PRIC','LOW_PRICE', 'GAIN_PERCENT']])

# Plot Chart (Clickable per Ticker)
fig = px.bar(df_filtered, x='TICKER', y='GAIN_PERCENT', color='TYPE', title="Options with High Gains", hover_data=['EXPIRY', 'STRIKE PRICE'])
st.plotly_chart(fig)

# Show Chart for Selected Ticker
ticker_selected = st.selectbox("Select Ticker for Price Chart", df_filtered['TICKER'].unique())
df_ticker = df_filtered[df_filtered['TICKER'] == ticker_selected]
fig2 = px.line(df_ticker, x='EXPIRY', y='CLOSE_PRIC', color='TYPE', title=f"Price Trends for {ticker_selected}")
st.plotly_chart(fig2)

import pandas as pd
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go

# ✅ Load dataset
file_path = "merge.csv"
df = pd.read_csv(file_path)

# ✅ Clean and Prepare Data
df = df.dropna(subset=['LOW_PRICE', 'HIGH_PRICE', 'CLOSE_PRIC', 'OPEN_PRICE', 'DATE'])
df['CLOSE_PRIC'] = pd.to_numeric(df['CLOSE_PRIC'], errors='coerce')
df['OPEN_PRICE'] = pd.to_numeric(df['OPEN_PRICE'], errors='coerce')
df['LOW_PRICE'] = pd.to_numeric(df['LOW_PRICE'], errors='coerce')
df['HIGH_PRICE'] = pd.to_numeric(df['HIGH_PRICE'], errors='coerce')
df['DATE'] = pd.to_datetime(df['DATE'], format='%d-%b-%Y', errors='coerce')

# ✅ Streamlit UI
st.title("📈 Options Price Gain Tracker with Candlestick Chart")

# ✅ Sidebar Filters
ticker = st.sidebar.selectbox("Select Ticker", ["All"] + list(df['TICKER'].unique()))
expiry = st.sidebar.selectbox("Select Expiry Date", ["All"] + list(df['EXPIRY'].unique()))
type_filter = st.sidebar.selectbox("Select Option Type", ["All"] + list(df['TYPE'].unique()))
strike_price = st.sidebar.selectbox("Select Strike Price", ["All"] + list(df['STRIKE PRICE'].unique()))
gain_threshold = st.sidebar.slider("Gain % Threshold", min_value=1, max_value=3000, value=50, step=50)

# ✅ Day range selection
days_option = st.sidebar.selectbox("Select Day Range", ["1 Day", "2 Days", "3 Days", "Custom"])

if days_option == "None":
    days = None
elif days_option == "Custom":
    custom_days = st.sidebar.number_input("Enter Custom Days", min_value=1, max_value=30, value=5)
    days = custom_days
else:
    days = int(days_option.split()[0])

# ✅ Apply Filters
df_filtered = df.copy()

if ticker != "All":
    df_filtered = df_filtered[df_filtered['TICKER'] == ticker]

if expiry != "All":
    df_filtered = df_filtered[df_filtered['EXPIRY'] == expiry]

if type_filter != "All":
    df_filtered = df_filtered[df_filtered['TYPE'] == type_filter]

if strike_price != "All":
    df_filtered = df_filtered[df_filtered['STRIKE PRICE'] == strike_price]

# ✅ Day-wise Gain Calculation Function with Single Row Per Strike Price
def calculate_daywise_gain_single_row(df, days):
    """Calculate gain % with single row per strike price."""
    
    df_sorted = df.sort_values(['TICKER', 'EXPIRY', 'STRIKE PRICE', 'DATE'])
    
    gain_data = []

    # Group by Ticker, Expiry, Type, and Strike Price
    for (ticker, expiry, type_, strike), group in df_sorted.groupby(['TICKER', 'EXPIRY', 'TYPE', 'STRIKE PRICE']):
        group = group.reset_index(drop=True)

        if days is None:
            # ✅ Use overall low price if no day filter is applied
            low_price = group['LOW_PRICE'].min()
            close_price = group['CLOSE_PRIC'].iloc[-1]  # Latest close price

        else:
            # ✅ Use low price from N days ago
            if len(group) >= days:
                low_price = group.iloc[-days]['LOW_PRICE']
            else:
                low_price = group['LOW_PRICE'].iloc[0]  # Fallback to first row if N days not available
            
            close_price = group['CLOSE_PRIC'].iloc[-1]  # Latest close price

        # ✅ Calculate gain percent
        gain_percent = ((close_price - low_price) / low_price) * 100 if low_price != 0 else 0

        gain_data.append({
            'TICKER': ticker,
            'EXPIRY': expiry,
            'TYPE': type_,
            'STRIKE PRICE': strike,
            'DATE': group['DATE'].iloc[-1],   # Latest date
            'CLOSE_PRIC': close_price,
            'LOW_PRICE': low_price,
            'GAIN_PERCENT': gain_percent
        })

    return pd.DataFrame(gain_data)

# ✅ Apply Day-wise Gain Calculation
if days is None:
    df_grouped = df_filtered.groupby(['TICKER', 'EXPIRY', 'TYPE', 'STRIKE PRICE']).agg({
        'LOW_PRICE': 'min',
        'CLOSE_PRIC': 'last',
        'DATE': 'last'
    }).reset_index()

    df_grouped['GAIN_PERCENT'] = ((df_grouped['CLOSE_PRIC'] - df_grouped['LOW_PRICE']) / df_grouped['LOW_PRICE']) * 100
    df_daywise = df_grouped
else:
    df_daywise = calculate_daywise_gain_single_row(df_filtered, days)

# ✅ Filter by Gain Threshold
df_daywise_filtered = df_daywise[df_daywise['GAIN_PERCENT'] >= gain_threshold]

# ✅ Display Table
st.dataframe(df_daywise_filtered[['TICKER', 'EXPIRY', 'TYPE', 'STRIKE PRICE', 'CLOSE_PRIC', 'LOW_PRICE', 'GAIN_PERCENT']])

# ✅ Plot Bar Chart
fig = px.bar(
    df_daywise_filtered,
    x='TICKER',
    y='GAIN_PERCENT',
    color='TYPE',
    title=f"Options with High Gains over {days} Days" if days else "Overall Gains",
    hover_data=['EXPIRY', 'STRIKE PRICE']
)
st.plotly_chart(fig)

# ✅ Candlestick Chart for Each Date of Selected Strike Price
if not df_filtered.empty and strike_price != "All":
    df_strike = df_filtered[df_filtered['STRIKE PRICE'] == strike_price]

    if not df_strike.empty:
        # ✅ Group by DATE for price flow visualization
        fig_candlestick = go.Figure(data=[go.Candlestick(
            x=df_strike['DATE'],
            open=df_strike['OPEN_PRICE'],
            high=df_strike['HIGH_PRICE'],
            low=df_strike['LOW_PRICE'],
            close=df_strike['CLOSE_PRIC'],
            name=f"{strike_price}"
        )])

        fig_candlestick.update_layout(
            title=f"Candlestick Chart for {ticker} - {strike_price} (All Dates)",
            xaxis_title="Date",
            yaxis_title="Price",
            xaxis_rangeslider_visible=False
        )
        
        st.plotly_chart(fig_candlestick)
    else:
        st.warning("No data available for the selected strike price.")
else:
    st.warning("Please select a specific strike price to view the candlestick chart.")

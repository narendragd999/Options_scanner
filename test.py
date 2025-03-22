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
st.title("📈 Options Price Gain Tracker")

# ✅ Sidebar Filters
ticker = st.sidebar.selectbox("Select Ticker", ["All"] + list(df['TICKER'].unique()))
expiry = st.sidebar.selectbox("Select Expiry Date", ["All"] + list(df['EXPIRY'].unique()))
type_filter = st.sidebar.selectbox("Select CE/PE Type", ["All"] + list(df['TYPE'].unique()))
strike_price = st.sidebar.selectbox("Select Strike Price", ["All"] + list(df['STRIKE PRICE'].unique()))
option_type = st.sidebar.selectbox("Select Option Type", ["All", "OPTSTK", "OPTIDX"])
gain_threshold = st.sidebar.slider("Gain % Threshold", min_value=1, max_value=3000, value=10, step=50)

# ✅ New Filter: Strike Price > UNDRLNG_ST
strike_greater_than_undrlng = st.sidebar.checkbox("Show only Strike Price > Underlying Value", value=False)

# ✅ Day range selection
days_option = st.sidebar.selectbox("Select Day Range", ["1 Day", "2 Days", "3 Days", "Custom"])
if days_option == "Custom":
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
if option_type != "All":
    df_filtered = df_filtered[df_filtered['Option Type'].fillna("").str.upper() == option_type]

# ✅ Function to Get the Most Recent or 1-Day Old `UNDRLNG_ST`
def get_recent_or_1day_undrlng_st(df):
    """Get most recent or 1-day-old `UNDRLNG_ST` for each strike price per ticker."""
    df = df.sort_values(['TICKER', 'STRIKE PRICE', 'DATE'], ascending=[True, True, False])
    final_data = []
    for (ticker, strike), group in df.groupby(['TICKER', 'STRIKE PRICE']):
        recent_undrlng_st = group['UNDRLNG_ST'].iloc[0] if len(group) > 0 else "N/A"
        if len(group) > 1:
            old_undrlng_st = group['UNDRLNG_ST'].iloc[1] if pd.notna(group['UNDRLNG_ST'].iloc[1]) else recent_undrlng_st
        else:
            old_undrlng_st = recent_undrlng_st
        undrlng_st_final = recent_undrlng_st if pd.notna(recent_undrlng_st) else old_undrlng_st
        final_data.append({
            'TICKER': ticker,
            'STRIKE PRICE': strike,
            'MOST_RECENT_UNDRLNG_ST': recent_undrlng_st,
            'FALLBACK_1DAY_UNDRLNG_ST': old_undrlng_st,
            'DISPLAY_UNDRLNG_ST': undrlng_st_final
        })
    return pd.DataFrame(final_data)

# ✅ Apply Function to Get `UNDRLNG_ST`
df_undrlng = get_recent_or_1day_undrlng_st(df_filtered)

# ✅ Merge with Day-wise Gain Calculation
def calculate_daywise_gain(df, days):
    """Calculate gain % with single row per strike price."""
    df_sorted = df.sort_values(['TICKER', 'EXPIRY', 'STRIKE PRICE', 'DATE'])
    gain_data = []
    for (ticker, expiry, type_, strike), group in df_sorted.groupby(['TICKER', 'EXPIRY', 'TYPE', 'STRIKE PRICE']):
        if days is None:
            low_price = group['LOW_PRICE'].min()
            close_price = group['CLOSE_PRIC'].iloc[-1]
        else:
            if len(group) >= days:
                low_price = group.iloc[-days]['LOW_PRICE']
            else:
                low_price = group['LOW_PRICE'].iloc[0]
            close_price = group['CLOSE_PRIC'].iloc[-1]
        gain_percent = int(((close_price - low_price) / low_price) * 100) if low_price != 0 else 0
        gain_data.append({
            'TICKER': ticker,
            'EXPIRY': expiry,
            'TYPE': type_,
            'STRIKE PRICE': strike,
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
    df_daywise = calculate_daywise_gain(df_filtered, days)

# ✅ Merge Gain Data with `UNDRLNG_ST`
df_final = pd.merge(df_daywise, df_undrlng, how='left', on=['TICKER', 'STRIKE PRICE'])

# ✅ Filter by Gain Threshold
df_final_filtered = df_final[df_final['GAIN_PERCENT'] >= gain_threshold]

# ✅ Apply Strike Price > UNDRLNG_ST Filter
if strike_greater_than_undrlng:
    # Convert DISPLAY_UNDRLNG_ST to numeric, coercing errors to NaN
    df_final_filtered['DISPLAY_UNDRLNG_ST'] = pd.to_numeric(df_final_filtered['DISPLAY_UNDRLNG_ST'], errors='coerce')
    # Filter where STRIKE PRICE > DISPLAY_UNDRLNG_ST (handling NaN cases)
    df_final_filtered = df_final_filtered[
        (df_final_filtered['STRIKE PRICE'] > df_final_filtered['DISPLAY_UNDRLNG_ST']) &
        (df_final_filtered['DISPLAY_UNDRLNG_ST'].notna())
    ]

# ✅ Additional Filter by Gain Percent with Text Box
gain_input = st.sidebar.text_input("Filter by Gain % Above", "50")
try:
    gain_input_value = float(gain_input)
    df_final_filtered = df_final_filtered[df_final_filtered['GAIN_PERCENT'] >= gain_input_value]
except ValueError:
    st.warning("Invalid input. Please enter a numeric value.")

# ✅ Display Table
st.dataframe(df_final_filtered[['TICKER', 'EXPIRY', 'TYPE', 'STRIKE PRICE', 'DISPLAY_UNDRLNG_ST', 'CLOSE_PRIC', 'LOW_PRICE', 'GAIN_PERCENT']])

# ✅ Plot Bar Chart
fig = px.bar(
    df_final_filtered,
    x='TICKER',
    y='GAIN_PERCENT',
    color='TYPE',
    title="Filtered Options with High Gains",
    hover_data=['EXPIRY', 'STRIKE PRICE', 'DISPLAY_UNDRLNG_ST']
)
st.plotly_chart(fig)

# ✅ Candlestick Chart for Each Date of Selected Strike Price
if not df_filtered.empty and strike_price != "All":
    df_strike = df_filtered[df_filtered['STRIKE PRICE'] == strike_price]

    if not df_strike.empty:
        fig_candlestick = go.Figure(data=[go.Candlestick(
            x=df_strike['DATE'],
            open=df_strike['OPEN_PRICE'],
            high=df_strike['HIGH_PRICE'],
            low=df_strike['LOW_PRICE'],
            close=df_strike['CLOSE_PRIC']
        )])

        st.plotly_chart(fig_candlestick)
    else:
        st.warning("No data available for the selected strike price.")
else:
    st.warning("Please select a specific strike price to view the candlestick chart.")

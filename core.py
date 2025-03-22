import os
import pandas as pd
import re
import zipfile
import shutil
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go

# Define directories
source_dir = r"E:\apps\Options\Options_scanner\zip"
destination_dir = r"E:\apps\Options\Options_scanner"
pattern = re.compile(r"^(OPTSTK|OPTIDX)([A-Z]+)(\d{2}-[A-Z]{3}-\d{4})(CE|PE)([\d\.]+)$")

# Ensure source_dir exists
if not os.path.exists(source_dir):
    os.makedirs(source_dir)

# Function from bhav.py to extract date
def extract_date(folder_name):
    """Extract date from folder or zip name and return formatted date (DD-MMM-YYYY)."""
    match = re.search(r"(\d{2})(\d{2})(\d{2})$", folder_name.split(".")[0])
    if match:
        day, month, year = match.groups()
        year = "20" + year if int(year) <= 50 else "19" + year
        month_names = {
            "01": "JAN", "02": "FEB", "03": "MAR", "04": "APR", "05": "MAY", "06": "JUN",
            "07": "JUL", "08": "AUG", "09": "SEP", "10": "OCT", "11": "NOV", "12": "DEC"
        }
        month = month_names.get(month, month)
        formatted_date = f"{day}-{month}-{year}"
        return formatted_date
    return ""

# Function to process data (bhav.py logic)
def process_data():
    merged_data = []
    for item in os.listdir(source_dir):
        item_path = os.path.join(source_dir, item)

        if item.endswith(".zip") and item.startswith("fo"):
            formatted_date = extract_date(item.split(".")[0])
            extract_path = os.path.join(source_dir, item[:-4])
            
            with zipfile.ZipFile(item_path, 'r') as zip_ref:
                zip_ref.extractall(extract_path)

            for file in os.listdir(extract_path):
                if file.startswith("op") and file.endswith(".csv"):
                    file_path = os.path.join(extract_path, file)
                    df = pd.read_csv(file_path)

                    if df.shape[1] < 14:
                        continue

                    df.drop(df.iloc[:, 6:11], axis=1, inplace=True)
                    df.drop(df.iloc[:, 7:9], axis=1, inplace=True)

                    if "PREVIOUS_S" in df.columns:
                        previous_s_index = df.columns.get_loc("PREVIOUS_S")
                        new_columns = ["Option Type", "TICKER", "EXPIRY", "TYPE", "STRIKE PRICE"]
                        for idx, col_name in enumerate(new_columns):
                            df.insert(previous_s_index + idx, col_name, "")

                        for i, row in df.iterrows():
                            match = pattern.match(str(row.iloc[0]))
                            if match:
                                df.at[i, "Option Type"] = match.group(1)
                                df.at[i, "TICKER"] = match.group(2)
                                df.at[i, "EXPIRY"] = match.group(3)
                                df.at[i, "TYPE"] = match.group(4)
                                df.at[i, "STRIKE PRICE"] = match.group(5)

                    df["DATE"] = formatted_date
                    if "CLOSE_PRIC" in df.columns:
                        df["CLOSE_PRIC"] = df["CLOSE_PRIC"].replace(0, 0.05)

                    df["STRIKE PRICE"] = pd.to_numeric(df["STRIKE PRICE"], errors='coerce')
                    df["UNDRLNG_ST"] = pd.to_numeric(df.get("UNDRLNG_ST", pd.Series()), errors='coerce')

                    if "UNDRLNG_ST" in df.columns:
                        df = df[df["STRIKE PRICE"] > df["UNDRLNG_ST"]].dropna(subset=["STRIKE PRICE", "UNDRLNG_ST"])

                    if not df.empty:
                        merged_data.append(df)

            shutil.rmtree(extract_path)

        elif os.path.isdir(item_path) and item.startswith("fo"):
            formatted_date = extract_date(item.split(".")[0])

            for file in os.listdir(item_path):
                if file.startswith("op") and file.endswith(".csv"):
                    file_path = os.path.join(item_path, file)
                    df = pd.read_csv(file_path)

                    if df.shape[1] < 14:
                        continue

                    df.drop(df.iloc[:, 6:14], axis=1, inplace=True)

                    if "PREVIOUS_S" in df.columns:
                        previous_s_index = df.columns.get_loc("PREVIOUS_S")
                        new_columns = ["Option Type", "TICKER", "EXPIRY", "TYPE", "STRIKE PRICE"]
                        for idx, col_name in enumerate(new_columns):
                            df.insert(previous_s_index + idx, col_name, "")

                        for i, row in df.iterrows():
                            match = pattern.match(str(row.iloc[0]))
                            if match:
                                df.at[i, "Option Type"] = match.group(1)
                                df.at[i, "TICKER"] = match.group(2)
                                df.at[i, "EXPIRY"] = match.group(3)
                                df.at[i, "TYPE"] = match.group(4)
                                df.at[i, "STRIKE PRICE"] = match.group(5)

                    df["DATE"] = formatted_date
                    if "CLOSE_PRIC" in df.columns:
                        df["CLOSE_PRIC"] = df["CLOSE_PRIC"].replace(0, 0.05)

                    df["STRIKE PRICE"] = pd.to_numeric(df["STRIKE PRICE"], errors='coerce')
                    df["UNDRLNG_ST"] = pd.to_numeric(df.get("UNDRLNG_ST", pd.Series()), errors='coerce')

                    if "UNDRLNG_ST" in df.columns:
                        df = df[df["STRIKE PRICE"] > df["UNDRLNG_ST"]].dropna(subset=["STRIKE PRICE", "UNDRLNG_ST"])

                    if not df.empty:
                        merged_data.append(df)

    if merged_data:
        final_df = pd.concat(merged_data, ignore_index=True)
        final_output_path = os.path.join(destination_dir, "merge.csv")
        final_df.to_csv(final_output_path, index=False)
        return True, f"Processed CSV saved at: {final_output_path}"
    return False, "No valid CSV files found for processing."

# Streamlit App (app.py logic)
def run_dashboard():
    # Load dataset
    file_path = os.path.join(destination_dir, "merge.csv")
    
    # File uploader for ZIP files
    st.sidebar.header("Upload ZIP Files")
    uploaded_files = st.sidebar.file_uploader("Upload ZIP files", type=["zip"], accept_multiple_files=True)
    
    if uploaded_files:
        for uploaded_file in uploaded_files:
            # Save uploaded ZIP file to source_dir
            zip_path = os.path.join(source_dir, uploaded_file.name)
            with open(zip_path, "wb") as f:
                f.write(uploaded_file.getbuffer())
            st.sidebar.success(f"Saved {uploaded_file.name} to {source_dir}")

    # Process Data Button
    if st.button("Process Data"):
        with st.spinner("Processing data..."):
            success, message = process_data()
            if success:
                st.success(message)
            else:
                st.error(message)

    # Check if merge.csv exists
    if not os.path.exists(file_path):
        st.warning("merge.csv not found. Please upload ZIP files and process data first.")
        return

    df = pd.read_csv(file_path)

    # Clean and Prepare Data
    df = df.dropna(subset=['LOW_PRICE', 'HIGH_PRICE', 'CLOSE_PRIC', 'OPEN_PRICE', 'DATE'])
    df['CLOSE_PRIC'] = pd.to_numeric(df['CLOSE_PRIC'], errors='coerce')
    df['OPEN_PRICE'] = pd.to_numeric(df['OPEN_PRICE'], errors='coerce')
    df['LOW_PRICE'] = pd.to_numeric(df['LOW_PRICE'], errors='coerce')
    df['HIGH_PRICE'] = pd.to_numeric(df['HIGH_PRICE'], errors='coerce')
    df['DATE'] = pd.to_datetime(df['DATE'], format='%d-%b-%Y', errors='coerce')

    # Streamlit UI
    st.title("📈 Options Price Gain Tracker")

    # Sidebar Filters
    ticker = st.sidebar.selectbox("Select Ticker", ["All"] + list(df['TICKER'].unique()))
    expiry = st.sidebar.selectbox("Select Expiry Date", ["All"] + list(df['EXPIRY'].unique()))
    type_filter = st.sidebar.selectbox("Select CE/PE Type", ["All"] + list(df['TYPE'].unique()))
    strike_price = st.sidebar.selectbox("Select Strike Price", ["All"] + list(df['STRIKE PRICE'].unique()))
    option_type = st.sidebar.selectbox("Select Option Type", ["All", "OPTSTK", "OPTIDX"])
    gain_threshold = st.sidebar.slider("Gain % Threshold", min_value=1, max_value=3000, value=10, step=50)
    strike_greater_than_undrlng = st.sidebar.checkbox("Show only Strike Price > Underlying Value", value=False)

    days_option = st.sidebar.selectbox("Select Day Range", ["1 Day", "2 Days", "3 Days", "Custom"])
    if days_option == "Custom":
        custom_days = st.sidebar.number_input("Enter Custom Days", min_value=1, max_value=30, value=5)
        days = custom_days
    else:
        days = int(days_option.split()[0])

    # Apply Filters
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

    # Function to Get the Most Recent or 1-Day Old `UNDRLNG_ST`
    def get_recent_or_1day_undrlng_st(df):
        df = df.sort_values(['TICKER', 'STRIKE PRICE', 'DATE'], ascending=[True, True, False])
        final_data = []
        for (ticker, strike), group in df.groupby(['TICKER', 'STRIKE PRICE']):
            recent_undrlng_st = group['UNDRLNG_ST'].iloc[0] if len(group) > 0 else "N/A"
            old_undrlng_st = group['UNDRLNG_ST'].iloc[1] if len(group) > 1 and pd.notna(group['UNDRLNG_ST'].iloc[1]) else recent_undrlng_st
            undrlng_st_final = recent_undrlng_st if pd.notna(recent_undrlng_st) else old_undrlng_st
            final_data.append({
                'TICKER': ticker,
                'STRIKE PRICE': strike,
                'MOST_RECENT_UNDRLNG_ST': recent_undrlng_st,
                'FALLBACK_1DAY_UNDRLNG_ST': old_undrlng_st,
                'DISPLAY_UNDRLNG_ST': undrlng_st_final
            })
        return pd.DataFrame(final_data)

    df_undrlng = get_recent_or_1day_undrlng_st(df_filtered)

    # Function to Calculate Day-wise Gain
    def calculate_daywise_gain(df, days):
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

    df_final = pd.merge(df_daywise, df_undrlng, how='left', on=['TICKER', 'STRIKE PRICE'])
    df_final_filtered = df_final[df_final['GAIN_PERCENT'] >= gain_threshold]

    if strike_greater_than_undrlng:
        df_final_filtered['DISPLAY_UNDRLNG_ST'] = pd.to_numeric(df_final_filtered['DISPLAY_UNDRLNG_ST'], errors='coerce')
        df_final_filtered = df_final_filtered[
            (df_final_filtered['STRIKE PRICE'] > df_final_filtered['DISPLAY_UNDRLNG_ST']) &
            (df_final_filtered['DISPLAY_UNDRLNG_ST'].notna())
        ]

    gain_input = st.sidebar.text_input("Filter by Gain % Above", "50")
    try:
        gain_input_value = float(gain_input)
        df_final_filtered = df_final_filtered[df_final_filtered['GAIN_PERCENT'] >= gain_input_value]
    except ValueError:
        st.warning("Invalid input. Please enter a numeric value.")

    st.dataframe(df_final_filtered[['TICKER', 'EXPIRY', 'TYPE', 'STRIKE PRICE', 'DISPLAY_UNDRLNG_ST', 'CLOSE_PRIC', 'LOW_PRICE', 'GAIN_PERCENT']])

    fig = px.bar(
        df_final_filtered,
        x='TICKER',
        y='GAIN_PERCENT',
        color='TYPE',
        title="Filtered Options with High Gains",
        hover_data=['EXPIRY', 'STRIKE PRICE', 'DISPLAY_UNDRLNG_ST']
    )
    st.plotly_chart(fig)

# Run the app
if __name__ == "__main__":
    run_dashboard()
import os
import pandas as pd
import re
import zipfile
import shutil
import streamlit as st
import plotly.express as px
from datetime import datetime, timedelta

# ✅ CONFIGURATION
source_dir = r"E:\apps\Options_scanner\zip"
output_file = os.path.join(source_dir, "merge.csv")
pattern = re.compile(r"^(OPTSTK|OPTIDX)([A-Z]+)(\d{2}-[A-Z]{3}-\d{4})(CE|PE)([\d\.]+)$")

# ✅ FUNCTION TO EXTRACT DATE FROM ZIP OR FOLDER NAME
def extract_date(folder_name):
    match = re.search(r"(\d{2})(\d{2})(\d{2})$", folder_name.split(".")[0])
    if match:
        day, month, year = match.groups()
        year = "20" + year if int(year) <= 50 else "19" + year
        month_names = {
            "01": "JAN", "02": "FEB", "03": "MAR", "04": "APR", "05": "MAY", "06": "JUN",
            "07": "JUL", "08": "AUG", "09": "SEP", "10": "OCT", "11": "NOV", "12": "DEC"
        }
        month = month_names.get(month, month)
        return f"{day}-{month}-{year}"
    return ""

# ✅ FUNCTION TO EXTRACT AND MERGE CSV FILES
def extract_and_merge():
    merged_data = []

    for item in os.listdir(source_dir):
        item_path = os.path.join(source_dir, item)

        # ✅ Handle ZIP Files
        if item.endswith(".zip") and item.startswith("fo"):
            formatted_date = extract_date(item)
            extract_path = os.path.join(source_dir, item[:-4])

            with zipfile.ZipFile(item_path, 'r') as zip_ref:
                zip_ref.extractall(extract_path)

            for file in os.listdir(extract_path):
                if file.startswith("op") and file.endswith(".csv"):
                    file_path = os.path.join(extract_path, file)
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
                    df["CLOSE_PRIC"] = df["CLOSE_PRIC"].replace(0, 0.05)
                    merged_data.append(df)

            shutil.rmtree(extract_path)

    # ✅ Save merged CSV
    if merged_data:
        final_df = pd.concat(merged_data, ignore_index=True)
        final_df.to_csv(output_file, index=False)
        print(f"✅ Merged CSV saved at: {output_file}")
    else:
        print("⚠️ No valid CSV files found for processing.")

# ✅ CHECK IF CSV EXISTS, IF NOT, EXTRACT AND MERGE
if not os.path.exists(output_file) or os.path.getmtime(output_file) < datetime.now().timestamp() - 86400:
    st.write("🔄 Extracting and merging CSV files...")
    extract_and_merge()

# ✅ LOAD THE MERGED CSV
df = pd.read_csv(output_file)

# ✅ DATA CLEANING
df = df.dropna(subset=['LOW_PRICE', 'CLOSE_PRIC', 'DATE'])
df['CLOSE_PRIC'] = pd.to_numeric(df['CLOSE_PRIC'], errors='coerce')
df['LOW_PRICE'] = pd.to_numeric(df['LOW_PRICE'], errors='coerce')
df['DATE'] = pd.to_datetime(df['DATE'], format='%d-%b-%Y', errors='coerce')

# ✅ STREAMLIT UI
st.title("📈 Options Price Gain Tracker with Day-Range Filter")

# ✅ Sidebar Filters
ticker_options = ["All"] + sorted(df['TICKER'].dropna().unique().tolist())
ticker = st.sidebar.selectbox("Select Ticker", ticker_options)

expiry_options = ["All"] + sorted(df['EXPIRY'].dropna().unique().tolist())
expiry = st.sidebar.selectbox("Select Expiry Date", expiry_options)

type_options = ["All"] + sorted(df['TYPE'].dropna().unique().tolist())
type_filter = st.sidebar.selectbox("Select Option Type", type_options)

gain_threshold = st.sidebar.slider("Gain % Threshold", min_value=1, max_value=3000, value=500, step=50)

# ✅ Day range selection
days_option = st.sidebar.selectbox("Select Day Range", ["None", "1 Day", "2 Days", "3 Days", "Weekly (7 Days)", "Custom"])

if days_option == "None":
    days = None
elif days_option == "Custom":
    custom_days = st.sidebar.number_input("Enter Custom Days", min_value=1, max_value=30, value=5)
    days = custom_days
else:
    days = int(days_option.split()[0])

# ✅ FILTERING
if days is not None:
    start_date = df['DATE'].max() - timedelta(days=days)
    df = df[df['DATE'] >= start_date]

if ticker != "All":
    df = df[df['TICKER'] == ticker]

if expiry != "All":
    df = df[df['EXPIRY'] == expiry]

if type_filter != "All":
    df = df[df['TYPE'] == type_filter]

# ✅ UNIQUE STRIKE PRICES
df_latest = df.sort_values('DATE').groupby(['TICKER', 'EXPIRY', 'TYPE', 'STRIKE PRICE']).last().reset_index()

# ✅ Calculate Gain Percentage
df_latest['GAIN_PERCENT'] = ((df_latest['CLOSE_PRIC'] - df_latest['LOW_PRICE']) / df_latest['LOW_PRICE']) * 100

# ✅ Filter by Gain Threshold
df_filtered = df_latest[df_latest['GAIN_PERCENT'] >= gain_threshold]

# ✅ Display Table
st.dataframe(df_filtered[['TICKER', 'EXPIRY', 'TYPE', 'STRIKE PRICE', 'CLOSE_PRIC', 'LOW_PRICE', 'GAIN_PERCENT']])

# ✅ Plot Chart
fig = px.bar(df_filtered, x='TICKER', y='GAIN_PERCENT', color='TYPE', hover_data=['EXPIRY', 'STRIKE PRICE'])
st.plotly_chart(fig)

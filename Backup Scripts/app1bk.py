import os
import pandas as pd
import re
import zipfile
import shutil
import streamlit as st
import plotly.express as px

# ✅ CONFIGURATION
source_dir = r"E:\apps\Options_scanner\zip"
output_file = os.path.join(source_dir, "merge.csv")

# ✅ PATTERN FOR OPTIONS PARSING
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

# ✅ DATA EXTRACTION AND MERGING
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

                # ✅ Remove unnecessary columns
                df.drop(df.iloc[:, 6:14], axis=1, inplace=True)

                # ✅ Add new columns and parse values
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
                df["CLOSE_PRIC"] = df["CLOSE_PRIC"].replace(0, 0.05)  # Replace 0 with 0.05
                merged_data.append(df)

        shutil.rmtree(extract_path)

    # ✅ Handle Folder Directories
    elif os.path.isdir(item_path) and item.startswith("fo"):
        formatted_date = extract_date(item)

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
                df["CLOSE_PRIC"] = df["CLOSE_PRIC"].replace(0, 0.05)
                merged_data.append(df)

# ✅ Save merged CSV
if merged_data:
    final_df = pd.concat(merged_data, ignore_index=True)
    final_df.to_csv(output_file, index=False)
    print(f"✅ Merged CSV saved at: {output_file}")
else:
    print("⚠️ No valid CSV files found for processing.")

# ✅ STREAMLIT APP FOR DAY-WISE GAIN TRACKER

# ✅ Load Merged Data
df = pd.read_csv(output_file)

# ✅ Clean and Prepare Data
df = df.dropna(subset=['LOW_PRICE', 'CLOSE_PRIC', 'DATE'])
df['CLOSE_PRIC'] = pd.to_numeric(df['CLOSE_PRIC'], errors='coerce')
df['LOW_PRICE'] = pd.to_numeric(df['LOW_PRICE'], errors='coerce')
df['DATE'] = pd.to_datetime(df['DATE'], format='%d-%b-%Y', errors='coerce')

# ✅ Streamlit UI
st.title("📈 Options Price Gain Tracker with Day-wise Filter")

# ✅ Sidebar Filters
ticker = st.sidebar.selectbox("Select Ticker", ["All"] + list(df['TICKER'].unique()))
expiry = st.sidebar.selectbox("Select Expiry Date", ["All"] + list(df['EXPIRY'].unique()))
type_filter = st.sidebar.selectbox("Select Option Type", ["All"] + list(df['TYPE'].unique()))
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

# ✅ Apply Filters
df_filtered = df.copy()

if ticker != "All":
    df_filtered = df_filtered[df_filtered['TICKER'] == ticker]

if expiry != "All":
    df_filtered = df_filtered[df_filtered['EXPIRY'] == expiry]

if type_filter != "All":
    df_filtered = df_filtered[df_filtered['TYPE'] == type_filter]

# ✅ Day-wise Gain Calculation
def calculate_daywise_gain_single_row(df, days):
    df_sorted = df.sort_values(['TICKER', 'EXPIRY', 'STRIKE PRICE', 'DATE'])
    
    gain_data = []

    for (ticker, expiry, type_, strike), group in df_sorted.groupby(['TICKER', 'EXPIRY', 'TYPE', 'STRIKE PRICE']):
        group = group.reset_index(drop=True)

        low_price = group['LOW_PRICE'].iloc[-days] if days and len(group) >= days else group['LOW_PRICE'].min()
        close_price = group['CLOSE_PRIC'].iloc[-1]

        gain_percent = ((close_price - low_price) / low_price) * 100 if low_price != 0 else 0

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

df_daywise = calculate_daywise_gain_single_row(df_filtered, days)
st.dataframe(df_daywise)

fig = px.bar(df_daywise, x='TICKER', y='GAIN_PERCENT', color='TYPE')
st.plotly_chart(fig)

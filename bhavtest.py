import os
import pandas as pd
import re
import zipfile
import shutil

source_dir = r"E:\apps\Options\Options_scanner\zip"
destination_dir = r"E:\apps\Options\Options_scanner"
pattern = re.compile(r"^(OPTSTK|OPTIDX)([A-Z]+)(\d{2}-[A-Z]{3}-\d{4})(CE|PE)([\d\.]+)$")

merged_data = []

def extract_date(folder_name):
    """Extract date from folder or zip name and return formatted date (DD-MMM-YYYY)."""
    match = re.search(r"(\d{2})(\d{2})(\d{2})$", folder_name.split(".")[0])  # Extract last 6 digits
    if match:
        day, month, year = match.groups()
        year = "20" + year if int(year) <= 50 else "19" + year  # Ensure correct year
        month_names = {
            "01": "JAN", "02": "FEB", "03": "MAR", "04": "APR", "05": "MAY", "06": "JUN",
            "07": "JUL", "08": "AUG", "09": "SEP", "10": "OCT", "11": "NOV", "12": "DEC"
        }
        month = month_names.get(month, month)  # Convert to short month name
        formatted_date = f"{day}-{month}-{year}"
        print(f"✅ Extracted Date: {formatted_date} from {folder_name}")
        return formatted_date
    print(f"⚠️ Date not found in {folder_name}")
    return ""

# New filter settings (you can modify these as needed)
FILTER_STRIKE_WITHIN_10_PERCENT = True  # Set to True to enable the 10% filter

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

                # Convert relevant columns to numeric for comparison
                df["STRIKE PRICE"] = pd.to_numeric(df["STRIKE PRICE"], errors='coerce')
                df["UNDRLNG_ST"] = pd.to_numeric(df.get("UNDRLNG_ST", pd.Series()), errors='coerce')

                # Filter: STRIKE PRICE > UNDRLNG_ST (mandatory)
                if "UNDRLNG_ST" in df.columns:
                    df = df[df["STRIKE PRICE"] > df["UNDRLNG_ST"]].dropna(subset=["STRIKE PRICE", "UNDRLNG_ST"])

                    # Optional Filter: STRIKE PRICE within 10% less than UNDRLNG_ST
                    if FILTER_STRIKE_WITHIN_10_PERCENT:
                        df = df[df["STRIKE PRICE"] >= df["UNDRLNG_ST"] * 0.9]  # STRIKE PRICE >= 90% of UNDRLNG_ST

                # Append only if there are valid rows after filtering
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

                # Convert relevant columns to numeric for comparison
                df["STRIKE PRICE"] = pd.to_numeric(df["STRIKE PRICE"], errors='coerce')
                df["UNDRLNG_ST"] = pd.to_numeric(df.get("UNDRLNG_ST", pd.Series()), errors='coerce')

                # Filter: STRIKE PRICE > UNDRLNG_ST (mandatory)
                if "UNDRLNG_ST" in df.columns:
                    df = df[df["STRIKE PRICE"] > df["UNDRLNG_ST"]].dropna(subset=["STRIKE PRICE", "UNDRLNG_ST"])

                    # Optional Filter: STRIKE PRICE within 10% less than UNDRLNG_ST
                    if FILTER_STRIKE_WITHIN_10_PERCENT:
                        df = df[df["STRIKE PRICE"] >= df["UNDRLNG_ST"] * 0.9]  # STRIKE PRICE >= 90% of UNDRLNG_ST

                # Append only if there are valid rows after filtering
                if not df.empty:
                    merged_data.append(df)

if merged_data:
    final_df = pd.concat(merged_data, ignore_index=True)

    required_columns = ["TICKER", "EXPIRY", "TYPE", "STRIKE PRICE"]
    missing_columns = [col for col in required_columns if col not in final_df.columns]

    if missing_columns:
        print(f"⚠️ Missing columns: {missing_columns} - Skipping grouping.")
    else:
        df_grouped = final_df.groupby(["TICKER", "EXPIRY", "TYPE", "STRIKE PRICE"])
        print("✅ Grouping successful!")

    final_output_path = os.path.join(destination_dir, "merge.csv")
    final_df.to_csv(final_output_path, index=False)
    print(f"Processed CSV saved at: {final_output_path}")
else:
    print("No valid CSV files found for processing.")
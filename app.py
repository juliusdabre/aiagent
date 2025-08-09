import streamlit as st
import pandas as pd
from io import BytesIO

st.set_page_config(page_title="AU Property Finder (No Google API)", layout="wide")

st.title("AU Property Finder – WA, Price 500k–700k (No Google API)")
st.caption("Upload your results CSV or use the included sample. Filter by price and suburb, then export CSV/Excel.")

# --- Data source ---
st.sidebar.header("Data Source")
mode = st.sidebar.radio("How do you want to load listings?", ["Use sample data", "Upload CSV"])

@st.cache_data
def load_sample():
    return pd.read_csv("sample_data.csv")

if mode == "Upload CSV":
    file = st.sidebar.file_uploader("Upload a CSV with columns: suburb, price, address, link, beds, baths, car", type=["csv"])
    if file:
        df = pd.read_csv(file)
    else:
        st.info("No file uploaded yet. Using sample data temporarily.")
        df = load_sample()
else:
    df = load_sample()

# --- Basic cleanup ---
expected_cols = ["suburb", "price", "address", "link", "beds", "baths", "car"]
missing = [c for c in expected_cols if c not in df.columns]
if missing:
    st.warning(f"Your data is missing columns: {missing}. The app will still try to work with what's available.")
if "price" in df.columns:
    df["price"] = pd.to_numeric(df["price"], errors="coerce")

# --- Sidebar filters ---
st.sidebar.header("Filters")
min_price = int(df["price"].min()) if "price" in df.columns else 0
max_price = int(df["price"].max()) if "price" in df.columns else 1000000
price_range = st.sidebar.slider("Price range (AUD)", min_value=min_price, max_value=max_price, value=(500000, 700000), step=5000)

suburbs = sorted(df["suburb"].dropna().unique()) if "suburb" in df.columns else []
selected_suburbs = st.sidebar.multiselect("Suburbs", suburbs, default=suburbs[:10] if suburbs else [])

# --- Apply filters ---
filtered = df.copy()
if "price" in filtered.columns:
    filtered = filtered[(filtered["price"] >= price_range[0]) & (filtered["price"] <= price_range[1])]
if selected_suburbs and "suburb" in filtered.columns:
    filtered = filtered[filtered["suburb"].isin(selected_suburbs)]

st.write(f"Showing **{len(filtered)}** listings")
st.dataframe(filtered, use_container_width=True)

# --- Downloads ---
csv_data = filtered.to_csv(index=False).encode("utf-8")
st.download_button("⬇️ Download CSV", data=csv_data, file_name="filtered_listings.csv", mime="text/csv")

# Excel download
excel_buf = BytesIO()
with pd.ExcelWriter(excel_buf, engine="openpyxl") as writer:
    filtered.to_excel(writer, sheet_name="Listings", index=False)
excel_buf.seek(0)
st.download_button("⬇️ Download Excel", data=excel_buf, file_name="filtered_listings.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")

st.markdown("---")
st.markdown("**Tip:** To scrape live results elsewhere, run your own script to produce a CSV with the expected columns and upload it here.")

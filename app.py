import streamlit as st
import pandas as pd
import asyncio
from datetime import datetime

from agents.scraper import find_properties

# Google Sheets libs (installed via requirements)
try:
    import gspread
    from google.oauth2.service_account import Credentials
    GS_AVAILABLE = True
except Exception:
    GS_AVAILABLE = False

st.set_page_config(page_title="AU Property Finder", layout="wide")
st.title("🏠 AU Property Finder (realestate.com.au)")

tab1, tab2 = st.tabs(["WA Finder (500k–700k quick)", "Advanced Finder"])

def export_to_gsheets(df: pd.DataFrame, spreadsheet_name: str, worksheet_name: str) -> str:
    """Export DataFrame to Google Sheets using service account in st.secrets."""
    if not GS_AVAILABLE:
        return "Google Sheets libraries not available. Check requirements."
    if "gcp_service_account" not in st.secrets:
        return "Missing service account in Streamlit secrets (gcp_service_account)."
    try:
        creds_dict = dict(st.secrets["gcp_service_account"])
        scopes = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
        credentials = Credentials.from_service_account_info(creds_dict, scopes=scopes)
        client = gspread.authorize(credentials)
        # open or create spreadsheet
        try:
            sh = client.open(spreadsheet_name)
        except gspread.SpreadsheetNotFound:
            sh = client.create(spreadsheet_name)
            # Share with service account itself by default (already owner)
        # add or replace worksheet
        if worksheet_name in [ws.title for ws in sh.worksheets()]:
            ws = sh.worksheet(worksheet_name)
            sh.del_worksheet(ws)
        ws = sh.add_worksheet(title=worksheet_name, rows=str(len(df)+10), cols=str(len(df.columns)+5))
        # write header + data
        ws.update([df.columns.tolist()] + df.fillna("").astype(str).values.tolist())
        return f"Exported to '{spreadsheet_name}' → '{worksheet_name}'."
    except Exception as e:
        return f"Export failed: {e}"

with tab1:
    st.caption("One-click WA search between $500k and $700k")
    pages = st.slider("Pages to scan", 1, 20, 5, key="wa_pages")
    if st.button("Find WA Listings", key="wa_go"):
        with st.spinner("Scanning WA… first run may take ~30–60s to fetch Chromium"):
            data = asyncio.run(find_properties(500_000, 700_000, "wa", pages))
        if not data:
            st.warning("No listings found in that range.")
        else:
            df = pd.DataFrame(data)

            # --- Suburb filter ---
            suburbs = sorted([s for s in df["suburb"].dropna().unique().tolist() if s])
            selected_suburbs = st.multiselect("Filter by suburb (optional)", suburbs)
            if selected_suburbs:
                df = df[df["suburb"].isin(selected_suburbs)]

            st.success(f"Found {len(df)} WA listings in $500k–$700k")
            st.dataframe(df, use_container_width=True)

            # Export to Google Sheets
            st.subheader("Export to Google Sheets")
            colA, colB, colC = st.columns([2,2,1])
            with colA:
                spreadsheet_name = st.text_input("Spreadsheet name", value="AU Property Finder")
            with colB:
                default_ws = f"WA_{datetime.utcnow().strftime('%Y%m%d_%H%M')}"
                worksheet_name = st.text_input("Worksheet name", value=default_ws)
            with colC:
                do_export = st.button("Export")
            if do_export:
                msg = export_to_gsheets(df, spreadsheet_name, worksheet_name)
                if "Exported" in msg:
                    st.success(msg)
                else:
                    st.error(msg)

            st.download_button("Download CSV", df.to_csv(index=False).encode(), "wa_listings.csv", "text/csv")
            st.download_button("Download JSON", df.to_json(orient="records", force_ascii=False, indent=2).encode("utf-8"), "wa_listings.json", "application/json")

with tab2:
    col1, col2, col3 = st.columns(3)
    with col1:
        state = st.selectbox("State", ["wa","nsw","vic","qld","sa","tas","act","nt"], index=0)
    with col2:
        min_price = st.number_input("Min price", 0, 5_000_000, 500_000, step=25_000)
    with col3:
        max_price = st.number_input("Max price", 0, 5_000_000, 700_000, step=25_000)
    pages2 = st.slider("Pages to scan", 1, 20, 5, key="adv_pages")

    go = st.button("Find Listings", key="adv_go")
    if go:
        if min_price > max_price:
            st.error("Min price cannot be greater than max price.")
        else:
            with st.spinner(f"Scanning {state.upper()}…"):
                data = asyncio.run(find_properties(int(min_price), int(max_price), state, pages2))
            if not data:
                st.warning("No listings found for those settings.")
            else:
                df = pd.DataFrame(data)

                # --- Suburb filter ---
                suburbs = sorted([s for s in df["suburb"].dropna().unique().tolist() if s])
                selected_suburbs = st.multiselect("Filter by suburb (optional)", suburbs, key="adv_suburbs")
                if selected_suburbs:
                    df = df[df["suburb"].isin(selected_suburbs)]

                st.success(f"Found {len(df)} listings in {state.upper()}")
                st.dataframe(df, use_container_width=True)

                # Export to Google Sheets
                st.subheader("Export to Google Sheets")
                colA, colB, colC = st.columns([2,2,1])
                with colA:
                    spreadsheet_name = st.text_input("Spreadsheet name", value="AU Property Finder", key="gs_name_adv")
                with colB:
                    default_ws = f"{state.upper()}_{datetime.utcnow().strftime('%Y%m%d_%H%M')}"
                    worksheet_name = st.text_input("Worksheet name", value=default_ws, key="gs_ws_adv")
                with colC:
                    do_export = st.button("Export", key="gs_export_adv")
                if do_export:
                    msg = export_to_gsheets(df, spreadsheet_name, worksheet_name)
                    if "Exported" in msg:
                        st.success(msg)
                    else:
                        st.error(msg)

                st.download_button("Download CSV", df.to_csv(index=False).encode(), f"{state}_listings.csv", "text/csv")
                st.download_button("Download JSON", df.to_json(orient="records", force_ascii=False, indent=2).encode("utf-8"), f"{state}_listings.json", "application/json")
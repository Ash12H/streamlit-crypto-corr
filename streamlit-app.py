import json
import streamlit as st
import requests
import pandas as pd
import plotly.express as px

# INITIALIZATION
st.title("Crypto Correlation Analysis")
st.write("This app shows the correlation between different cryptocurrencies")

if "selected_symbols" not in st.session_state:
    st.session_state.selected_symbols = []
if "selected_ids" not in st.session_state:
    st.session_state.selected_ids = []
if "all_charts" not in st.session_state:
    st.session_state.all_charts = {}


# FUNCTIONS
@st.cache_data
def setup_data():
    print("running setup_data")
    headers = {
        "accept": "application/json",
        "x_cg_demo_api_key": st.secrets["CoinGecko"],
    }
    base_url = "https://api.coingecko.com/api/v3"
    return headers, base_url


@st.cache_data
def get_coins(base_url, headers) -> pd.DataFrame:
    print("running get_coins")
    response = requests.get(f"{base_url}/coins/list", headers=headers)
    return pd.DataFrame(response.json())


@st.cache_data
def corr_charts(all_charts):
    print("running corr_charts")
    return pd.concat(all_charts.values(), axis=1).dropna(axis=0, how="any").corr()


# SETUP
headers, base_url = setup_data()
coins = get_coins(base_url, headers)

# SYMBOLS
selected_symbols = st.multiselect(
    "Select a symbol", coins["symbol"].unique(), st.session_state.selected_symbols
)
st.session_state.selected_symbols = selected_symbols

# IDS
sub_coins = coins[coins["symbol"].isin(st.session_state.selected_symbols)]
for id in st.session_state.selected_ids:
    if id not in sub_coins["id"].unique():
        st.session_state.selected_ids.remove(id)
selected_ids = st.multiselect(
    "Then select an ID", sub_coins["id"].unique(), st.session_state.selected_ids
)
st.session_state.selected_ids = selected_ids

# REQUEST CHART
for id in st.session_state.selected_ids:
    if id in st.session_state.all_charts:
        print("Already have", id)
        continue

    print("Requesting", id)
    try:
        response = requests.get(
            f"{base_url}/coins/{id}/market_chart",
            headers=headers,
            params={
                "vs_currency": "usd",
                "days": "365",
            },
        )
        response = pd.DataFrame(response.json()["prices"], columns=["time", "price"])
        response["time"] = pd.to_datetime(response["time"], unit="ms")
        st.session_state.all_charts[id] = (
            response.set_index("time")
            .rename(columns={"price": id})
            .resample("1D")
            .mean()
        )
    except Exception as e:
        print("Error", e)
        continue

# HEATMAP
if st.session_state.all_charts != {}:
    st.write(
        px.imshow(
            corr_charts(st.session_state.all_charts),
            width=800,
            height=800,
            title="Correlation between cryptocurrencies",
            color_continuous_scale="RdBu",
            text_auto=True,
            # min -1 max 1
            zmin=-1,
            zmax=1,
        )
    )
else:
    st.write("No data to show")

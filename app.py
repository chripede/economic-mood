from datetime import datetime
import streamlit as st
import plotly.graph_objects as go
import requests
import pandas as pd
import dateparser
import zoneinfo

st.set_page_config(
    layout="wide",
    page_title="Economic Numbers Mood :) :( :|",
)


@st.cache
def load_economic_calendar():
    session = requests.Session()
    session.headers.update(
        {
            "User-Agent": "Mozilla/5.0 (X11; Linux x86_64; rv:108.0) Gecko/20100101 Firefox/108.0"
        }
    )
    url = "https://economic-calendar.tradingview.com/events?from=2010-01-01T12%3A00%3A00.000Z&to=2023-01-28T14%3A00%3A00.000Z&countries=US&minImportance=1"
    r = session.get(url)
    j = r.json()

    df = pd.DataFrame(
        columns=("Title", "Date", "Actual", "Forecast", "Previous", "Unit")
    )
    for i in j["result"]:
        if dateparser.parse(i["date"]) > dateparser.parse("2023-02-01 00:00:00Z"):
            continue

        df.loc[i["id"]] = [
            i["title"],
            dateparser.parse(i["date"]),
            i["actual"],
            i["forecast"],
            i["previous"],
            i["unit"] if "unit" in i else "",
        ]

    df = df.sort_values(["Title", "Date"], ascending=[True, False])

    return df


@st.cache
def load_historical_data(ticker_name, market_date: datetime):
    df = pd.read_csv(
        f"./data/DAT_ASCII_{ticker_name}_M1_{market_date.year}.csv.gz",
        delimiter=";",
        header=None,
        names=["Date", "Open", "High", "Low", "Close", "Volume"],
    )
    del df["Volume"]
    df["Date"] = pd.to_datetime(df["Date"], format="%Y%m%d %H%M%S")
    df.set_index("Date", inplace=True)
    df.index = df.index.tz_localize("US/Eastern").tz_convert("UTC")

    return df.loc[str(market_date)]


def event_index_to_date(event_index):
    economic_calendar = load_economic_calendar()
    return economic_calendar.loc[event_index].Date.date()


economic_calendar = load_economic_calendar()

event = st.sidebar.selectbox("Select event", economic_calendar.Title.unique())

market_date_index = st.sidebar.selectbox(
    "Select date",
    economic_calendar[economic_calendar["Title"] == event].index,
    format_func=event_index_to_date,
)

market_date = economic_calendar.loc[market_date_index].Date.date()
event_df = economic_calendar.loc[market_date_index]
event_datetime = event_df.Date

st.header(event + " - " + str(market_date))
st.write(
    f"Actual: {event_df.Actual}{event_df.Unit} | Forecast: {event_df.Forecast}{event_df.Unit} | Previous: {event_df.Previous}{event_df.Unit}"
)

layout = go.Layout(
    xaxis={"title": "Date"},
    yaxis={"title": "Price"},
    height=1000,
    xaxis_rangeslider_visible=False,
    shapes=[
        dict(
            x0=event_datetime,
            x1=event_datetime,
            y0=0,
            y1=1,
            xref="x",
            yref="paper",
            line_width=20,
            line_color="White",
            opacity=0.2,
        )
    ],
    annotations=[
        dict(
            x=event_datetime,
            y=1,
            xref="x",
            yref="paper",
            showarrow=False,
            xanchor="center",
            text=event,
        )
    ],
)


def create_chart(history):
    fig = go.Figure(
        layout=layout,
        data=[
            go.Candlestick(
                x=history.index,
                open=history["Open"],
                high=history["High"],
                low=history["Low"],
                close=history["Close"],
                name="Candlestick chart",
            )
        ],
    )
    return fig


tab_dax, tab_ftse, tab_dow, tab_nasdaq = st.tabs(
    ["DAX (No Data)", "FTSE (No Data)", "DOW (No Data)", "NASDAQ"]
)

with tab_dow:
    st.warning("No good source for DOW minute data")

with tab_nasdaq:
    market = "NSXUSD"
    history = load_historical_data(
        market,
        market_date,
    )
    fig = create_chart(history)
    st.plotly_chart(fig, use_container_width=True)

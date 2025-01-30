import dash
import dash_bootstrap_components as dbc
from dash import dcc, html, Input, Output, State
import yfinance as yf
from prophet import Prophet
import pandas as pd
import plotly.graph_objs as go
import os

# Dashアプリケーションの初期化（Bootstrapテーマ適用）
app = dash.Dash(__name__, external_stylesheets=[dbc.themes.FLATLY])
app.title = "株価予測アプリ (Sheepdog Stock Prediction)"

# Flaskのサーバーインスタンスを取得（Gunicorn用）
server = app.server

# 言語オプション（日本語 / 英語）
languages = {"ja": "日本語", "en": "English"}

# 言語に対応したラベルを設定
translations = {
    "title": {"ja": "株価予測", "en": "Stock Price Prediction"},
    "ticker_label1": {"ja": "ティッカーシンボル①:", "en": "Ticker Symbol 1:"},
    "ticker_label2": {"ja": "ティッカーシンボル②:", "en": "Ticker Symbol 2:"},
    "ticker_label3": {"ja": "ティッカーシンボル③:", "en": "Ticker Symbol 3:"},
    "ticker_label4": {"ja": "ティッカーシンボル④:", "en": "Ticker Symbol 4:"},
    "start_date": {"ja": "開始日:", "en": "Start Date:"},
    "end_date": {"ja": "終了日:", "en": "End Date:"},
    "forecast_days": {"ja": "予測日数:", "en": "Forecast Days:"},
    "predict_button": {"ja": "予測を実行", "en": "Run Prediction"},
    "realtime_title": {"ja": "リアルタイム株価データ", "en": "Real-time Stock Prices"},
    "realtime_ticker": {"ja": "ティッカーシンボル:", "en": "Ticker Symbol:"},
    "realtime_button": {"ja": "データ取得", "en": "Fetch Data"}
}

# アプリケーションのレイアウト
app.layout = dbc.Container([
    dcc.Dropdown(
        id="language-selector",
        options=[{"label": name, "value": code} for code, name in languages.items()],
        value="ja",
        clearable=False,
        style={"width": "200px", "margin-bottom": "20px"}
    ),
    
    dcc.Tabs(id="tabs", value="tab1", children=[
        # タブ1: 株価予測
        dcc.Tab(label="株価予測 / Stock Prediction", value="tab1", children=[
            dbc.Row([
                dbc.Col([
                    html.H1(id="app-title", className="text-center my-4"),
                    
                    dbc.Row([
                        dbc.Col([dbc.Label(id="ticker1-label"), dbc.Input(id="ticker1", type="text", placeholder="例: AAPL", className="mb-3")]),
                        dbc.Col([dbc.Label(id="ticker2-label"), dbc.Input(id="ticker2", type="text", placeholder="例: GOOG", className="mb-3")]),
                        dbc.Col([dbc.Label(id="ticker3-label"), dbc.Input(id="ticker3", type="text", placeholder="例: MSFT", className="mb-3")]),
                        dbc.Col([dbc.Label(id="ticker4-label"), dbc.Input(id="ticker4", type="text", placeholder="例: TSLA", className="mb-3")]),
                    ]),

                    dbc.Row([
                        dbc.Col([dbc.Label(id="start-date-label"), dbc.Input(id="start_date", type="text", placeholder="YYYY-MM-DD", className="mb-3")]),
                        dbc.Col([dbc.Label(id="end-date-label"), dbc.Input(id="end_date", type="text", placeholder="YYYY-MM-DD", className="mb-3")])
                    ]),

                    html.Div([dbc.Label(id="forecast-days-label"), dbc.Input(id="forecast_days", type="number", placeholder="30", value=30, className="mb-3")]),
                    dbc.Button(id="predict_button", color="primary", className="my-3"),
                    html.Div(id="prediction-output"),
                ], width=12)
            ])
        ]),

        # タブ2: リアルタイム株価データ
        dcc.Tab(label="リアルタイム株価データ / Real-time Prices", value="tab2", children=[
            dbc.Row([
                dbc.Col([
                    html.H1(id="realtime-title", className="text-center my-4"),
                    dbc.Label(id="realtime-ticker-label"),
                    dbc.Input(id="realtime_ticker", type="text", placeholder="例: AAPL", className="mb-3"),
                    dbc.Button(id="realtime_button", color="success", className="my-3"),
                    html.Div(id="realtime-output"),
                ], width=6)
            ])
        ])
    ])
], fluid=True)


# 言語切り替えコールバック
@app.callback(
    [Output("app-title", "children"),
     Output("ticker1-label", "children"),
     Output("ticker2-label", "children"),
     Output("ticker3-label", "children"),
     Output("ticker4-label", "children"),
     Output("start-date-label", "children"),
     Output("end-date-label", "children"),
     Output("forecast-days-label", "children"),
     Output("predict_button", "children"),
     Output("realtime-title", "children"),
     Output("realtime-ticker-label", "children"),
     Output("realtime_button", "children")],
    [Input("language-selector", "value")]
)
def update_language(lang):
    return (
        translations["title"][lang],
        translations["ticker_label1"][lang],
        translations["ticker_label2"][lang],
        translations["ticker_label3"][lang],
        translations["ticker_label4"][lang],
        translations["start_date"][lang],
        translations["end_date"][lang],
        translations["forecast_days"][lang],
        translations["predict_button"][lang],
        translations["realtime_title"][lang],
        translations["realtime_ticker"][lang],
        translations["realtime_button"][lang],
    )


# ✅ **株価予測のコールバック**
@app.callback(
    Output("prediction-output", "children"),
    Input("predict_button", "n_clicks"),
    State("ticker1", "value"),
    State("ticker2", "value"),
    State("ticker3", "value"),
    State("ticker4", "value"),
    State("start_date", "value"),
    State("end_date", "value"),
    State("forecast_days", "value"),
)
def predict_stock_price(n_clicks, t1, t2, t3, t4, start_date, end_date, forecast_days):
    if n_clicks is None or n_clicks == 0:
        return ""

    tickers = [t1, t2, t3, t4]
    tickers = [t for t in tickers if t]  # 空の入力を除外
    if not tickers:
        return dbc.Alert("銘柄を入力してください。", color="danger")

    return dbc.Alert(f"予測実行: {tickers}, {start_date} 〜 {end_date}, 予測日数: {forecast_days}", color="info")


# ✅ **リアルタイム株価データ取得のコールバック**
@app.callback(
    Output("realtime-output", "children"),
    Input("realtime_button", "n_clicks"),
    State("realtime_ticker", "value"),
)
def get_realtime_data(n_clicks, ticker):
    if n_clicks is None or n_clicks == 0 or not ticker:
        return ""

    return dbc.Alert(f"リアルタイムデータ取得: {ticker}", color="info")


# Flaskサーバーでアプリを実行
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    app.run(debug=False, host="0.0.0.0", port=port)

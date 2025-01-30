import dash
import dash_bootstrap_components as dbc
from dash import dcc, html, Input, Output, State
import yfinance as yf
from prophet import Prophet
import pandas as pd
import plotly.graph_objs as go
import os

# Dashアプリの初期化
app = dash.Dash(__name__, external_stylesheets=[dbc.themes.FLATLY])
app.title = "株価予測アプリ (Sheepdog Stock Prediction)"
server = app.server  # Render / Gunicorn 用

# ✅ 日付フォーマット修正関数
def fix_date_format(date_str):
    try:
        return pd.to_datetime(date_str).strftime("%Y-%m-%d")
    except Exception:
        raise ValueError("日付フォーマットが正しくありません。YYYY-MM-DD 形式で入力してください。")

# ✅ UI レイアウト
app.layout = dbc.Container([
    dcc.Tabs(id="tabs", value="tab1", children=[

        # 📌 株価予測タブ
        dcc.Tab(label="📈 株価予測 / Stock Prediction", value="tab1", children=[
            html.H1("株価予測アプリ", className="text-center my-4"),
            
            dbc.Row([
                dbc.Col([dbc.Label("ティッカーシンボル①:"), dbc.Input(id="ticker1", type="text", placeholder="例: AAPL", className="mb-3")]),
                dbc.Col([dbc.Label("ティッカーシンボル②:"), dbc.Input(id="ticker2", type="text", placeholder="例: GOOG", className="mb-3")]),
                dbc.Col([dbc.Label("ティッカーシンボル③:"), dbc.Input(id="ticker3", type="text", placeholder="例: MSFT", className="mb-3")]),
                dbc.Col([dbc.Label("ティッカーシンボル④:"), dbc.Input(id="ticker4", type="text", placeholder="例: TSLA", className="mb-3")]),
            ]),

            dbc.Row([
                dbc.Col([dbc.Label("開始日:"), dbc.Input(id="start_date", type="text", placeholder="YYYY-MM-DD", className="mb-3")]),
                dbc.Col([dbc.Label("終了日:"), dbc.Input(id="end_date", type="text", placeholder="YYYY-MM-DD", className="mb-3")]),
                dbc.Col([dbc.Label("予測日数:"), dbc.Input(id="forecast_days", type="number", placeholder="30", value=30, className="mb-3")]),
            ]),

            dbc.Button("予測を実行", id="predict_button", color="primary", className="my-3"),
            html.Div(id="prediction-output"),
        ]),

        # 📌 リアルタイム株価データタブ
        dcc.Tab(label="💹 リアルタイム株価データ / Real-time Prices", value="tab2", children=[
            html.H1("リアルタイム株価データ", className="text-center my-4"),
            dbc.Label("ティッカーシンボル:"),
            dbc.Input(id="realtime_ticker", type="text", placeholder="例: AAPL", className="mb-3"),
            dbc.Button("データ取得", id="realtime_button", color="success", className="my-3"),
            html.Div(id="realtime-output"),
        ]),
    ])
], fluid=True)

# ✅ 株価予測
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
def predict_stock_price(n_clicks, *args):
    if not n_clicks:
        return ""

    tickers = [t for t in args[:4] if t]
    start_date, end_date, forecast_days = args[4:]

    try:
        start_date = fix_date_format(start_date)
        end_date = fix_date_format(end_date)
    except ValueError as e:
        return dbc.Alert(str(e), color="danger")

    results = []
    for ticker in tickers:
        try:
            data = yf.download(ticker, start=start_date, end=end_date)
            data = data[['Close']].reset_index()
            data.columns = ['ds', 'y']
            data = data.dropna()

            if len(data) < 2:
                raise ValueError(f"{ticker} のデータが少なすぎます。期間を変更してください。")

            # ✅ ノイズ除去（移動平均を5→7に変更）
            data['y'] = data['y'].rolling(window=7, min_periods=1).mean()

            # ✅ Prophetモデルの変動を抑制
            model = Prophet(changepoint_prior_scale=0.01)
            model.fit(data)

            future = model.make_future_dataframe(periods=int(forecast_days))
            forecast = model.predict(future)

            # 📈 予測結果のプロット
            fig = go.Figure()
            fig.add_trace(go.Scatter(x=data['ds'], y=data['y'], mode="lines", name=f"{ticker} 実績", line=dict(color="blue")))
            fig.add_trace(go.Scatter(x=forecast['ds'], y=forecast['yhat'], mode="lines", name=f"{ticker} 予測", line=dict(color="red")))

            results.append(dcc.Graph(figure=fig))
        except Exception as e:
            results.append(dbc.Alert(str(e), color="danger"))

    return results

# ✅ リアルタイム株価取得
@app.callback(
    Output("realtime-output", "children"),
    Input("realtime_button", "n_clicks"),
    State("realtime_ticker", "value"),
)
def get_realtime_stock_price(n_clicks, ticker):
    if not n_clicks:
        return ""

    try:
        data = yf.download(ticker, period="1d", interval="1d")
        if data.empty:
            raise ValueError(f"{ticker} のリアルタイムデータが取得できません。")

        latest_price = float(data["Close"].iloc[-1])
        return dbc.Alert(f"{ticker} の最新株価 (終値): {latest_price:.2f} USD", color="info")
    except Exception as e:
        return dbc.Alert(str(e), color="danger")

if __name__ == "__main__":
    app.run(debug=False, host="0.0.0.0", port=8080)

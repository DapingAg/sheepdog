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
app.title = "株価予測ダッシュボード"

# Flaskのサーバーインスタンスを取得（Gunicorn用）
server = app.server  # これを追加！

# アプリケーションのレイアウト
app.layout = dbc.Container([
    dcc.Tabs(id="tabs", value="tab1", children=[
        # タブ1: 株価予測
        dcc.Tab(label="株価予測", value="tab1", children=[
            dbc.Row([
                dbc.Col([
                    html.H1("株価予測アプリ", className="text-center my-4"),
                    html.Div([
                        dbc.Label("ティッカーシンボル (カンマ区切り, 最大4つ):"),
                        dbc.Input(id="tickers", type="text", placeholder="例: AAPL, GOOG, MSFT", className="mb-3"),
                    ]),
                    dbc.Row([
                        dbc.Col([
                            dbc.Label("開始日:"),
                            dbc.Input(id="start_date", type="text", placeholder="YYYY-MM-DD", className="mb-3"),
                        ]),
                        dbc.Col([
                            dbc.Label("終了日:"),
                            dbc.Input(id="end_date", type="text", placeholder="YYYY-MM-DD", className="mb-3"),
                        ])
                    ]),
                    html.Div([
                        dbc.Label("予測日数:"),
                        dbc.Input(id="forecast_days", type="number", placeholder="30", value=30, className="mb-3"),
                    ]),
                    dbc.Button("予測を実行", id="predict_button", color="primary", className="my-3"),
                    html.Div(id="prediction-output"),
                ], width=6)
            ])
        ]),

        # タブ2: リアルタイム株価データ
        dcc.Tab(label="リアルタイム株価データ", value="tab2", children=[
            dbc.Row([
                dbc.Col([
                    html.H1("リアルタイム株価データ", className="text-center my-4"),
                    html.Div([
                        dbc.Label("ティッカーシンボル:"),
                        dbc.Input(id="realtime_ticker", type="text", placeholder="例: AAPL", className="mb-3"),
                    ]),
                    dbc.Button("データ取得", id="realtime_button", color="success", className="my-3"),
                    html.Div(id="realtime-output"),
                ], width=6)
            ])
        ])
    ])
], fluid=True)

# 日付フォーマット修正関数
def fix_date_format(date_str):
    try:
        return pd.to_datetime(date_str).strftime("%Y-%m-%d")
    except Exception:
        raise ValueError("日付フォーマットが正しくありません。YYYY-MM-DD形式で入力してください。")

# 株価予測コールバック
@app.callback(
    Output("prediction-output", "children"),
    Input("predict_button", "n_clicks"),
    State("tickers", "value"),
    State("start_date", "value"),
    State("end_date", "value"),
    State("forecast_days", "value"),
)
def predict_stock_price(n_clicks, tickers, start_date, end_date, forecast_days):
    if n_clicks is None or n_clicks == 0:  # 初回ロード時に実行されないようにする
        return ""

    print(f"予測を実行: {tickers}, {start_date}, {end_date}, {forecast_days}")  # デバッグ用

    # 入力値が適切か確認
    if not tickers or not start_date or not end_date or not forecast_days:
        return dbc.Alert("すべての入力欄を正しく埋めてください。", color="danger")

    try:
        start_date = fix_date_format(start_date)
        end_date = fix_date_format(end_date)
    except ValueError as e:
        return dbc.Alert(str(e), color="danger")

    tickers = tickers.split(",")[:4]
    graphs = []
    for ticker in tickers:
        ticker = ticker.strip()
        try:
            print(f"{ticker} のデータを取得中...")  # デバッグ用
            data = yf.download(ticker, start=start_date, end=end_date)
            if data.empty:
                raise ValueError(f"{ticker} にデータが見つかりません。")

            data = data[['Close']].reset_index()
            data.columns = ['ds', 'y']
            data['ds'] = pd.to_datetime(data['ds'])
            data['ds'] = data['ds'].dt.tz_localize(None)

            # Prophetモデルで予測
            print(f"{ticker} の予測を実行中...")  # デバッグ用
            model = Prophet()
            model.fit(data)
            future = model.make_future_dataframe(periods=int(forecast_days))
            forecast = model.predict(future)

            # グラフ作成
            fig = go.Figure()
            fig.add_trace(go.Scatter(x=data['ds'], y=data['y'], mode="lines", name=f"{ticker} 実績"))
            fig.add_trace(go.Scatter(x=forecast['ds'], y=forecast['yhat'], mode="lines", name=f"{ticker} 予測"))
            fig.update_layout(title=f"{ticker} 株価予測", xaxis_title="Day", yaxis_title="Price")

            graphs.append(dcc.Graph(figure=fig))
        except Exception as e:
            print(f"{ticker} のエラー: {e}")  # デバッグ用
            graphs.append(dbc.Alert(f"{ticker} のエラー: {e}", color="danger"))

    return graphs

# Flaskサーバーでアプリを実行（ローカル環境用）
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))  # Render環境でのポート設定
    app.run(debug=False, host="0.0.0.0", port=port)  # `port` を適切に設定

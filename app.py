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

# Flaskサーバーでアプリを実行（ローカル環境用）
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))  # Render環境でのポート設定
    app.run(debug=False, host="0.0.0.0", port=port)  # `port` を適切に設定

"""
포스코 홀딩스 주가 대시보드 (yfinance + Streamlit)
KOSPI: 005490.KS
"""

from datetime import date, timedelta

import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import streamlit as st
import yfinance as yf

TICKER = "005490.KS"
COMPANY_KO = "포스코 홀딩스"

st.set_page_config(
    page_title=f"{COMPANY_KO} 주가",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded",
)

_ACCENT = "#0d47a1"
_UP = "#c62828"
_DOWN = "#1565c0"

st.markdown(
    f"""
    <style>
        div.block-container {{ padding-top: 1.2rem; max-width: 1400px; }}
        [data-testid="stAppViewContainer"] {{
            background: linear-gradient(165deg, #eceff1 0%, #f5f7fa 40%, #ffffff 100%);
        }}
        h1, h2, h3 {{ color: {_ACCENT} !important; }}
        div[data-testid="stMetric"] {{
            background: rgba(255, 255, 255, 0.9);
            border: 1px solid #b0bec5;
            border-radius: 12px;
            padding: 0.75rem 1rem;
        }}
    </style>
    """,
    unsafe_allow_html=True,
)


@st.cache_data(ttl=300)
def fetch_history(symbol: str, start: date, end: date) -> pd.DataFrame:
    t = yf.Ticker(symbol)
    df = t.history(start=start.isoformat(), end=(end + timedelta(days=1)).isoformat(), auto_adjust=True)
    if df.empty:
        return df
    df = df.rename_axis("Date").reset_index()
    dt = df["Date"]
    if getattr(dt.dtype, "tz", None) is not None:
        df["Date"] = dt.dt.tz_convert("Asia/Seoul").dt.tz_localize(None)
    return df


@st.cache_data(ttl=600)
def fetch_info(symbol: str) -> dict:
    return yf.Ticker(symbol).info or {}


def main():
    st.title(f"{COMPANY_KO} 주가 대시보드")
    st.caption(f"yfinance · 티커 `{TICKER}` (코스피) · 데이터 지연 가능")

    with st.sidebar:
        st.header("기간 설정")
        end_d = st.date_input(
            "종료일", value=date.today(), max_value=date.today()
        )
        lookback = st.selectbox(
            "시작 기준",
            options=[
                ("1개월", 30),
                ("3개월", 90),
                ("6개월", 180),
                ("1년", 365),
                ("3년", 365 * 3),
                ("5년", 365 * 5),
            ],
            format_func=lambda x: x[0],
            index=3,
        )
        days = lookback[1]
        start_d = end_d - timedelta(days=days)
        if start_d >= end_d:
            start_d = end_d - timedelta(days=30)
            st.warning("시작일이 종료일보다 앞서도록 조정했습니다.")

        show_ma = st.multiselect(
            "이동평균선",
            options=[5, 20, 60, 120],
            default=[20, 60],
        )
        st.divider()
        st.caption("새로고침 시 최근 데이터를 다시 불러옵니다.")

    info = fetch_info(TICKER)
    hist = fetch_history(TICKER, start_d, end_d)

    if hist.empty:
        st.error(
            "해당 기간에 주가 데이터가 없습니다. 네트워크·티커·기간을 확인하거나 잠시 후 다시 시도하세요."
        )
        st.stop()

    last = hist.iloc[-1]
    prev_close = float(hist.iloc[-2]["Close"]) if len(hist) > 1 else float(last["Close"])
    close = float(last["Close"])
    chg = close - prev_close
    chg_pct = (chg / prev_close * 100) if prev_close else 0.0
    vol = float(last["Volume"])
    high = float(last["High"])
    low = float(last["Low"])

    col1, col2, col3, col4, col5 = st.columns(5)
    col1.metric(
        "종가",
        f"{close:,.0f}원",
        f"{chg:+,.0f} ({chg_pct:+.2f}%)",
        delta_color="inverse",
    )
    col2.metric("고가(당일)", f"{high:,.0f}원")
    col3.metric("저가(당일)", f"{low:,.0f}원")
    col4.metric("거래량", f"{vol:,.0f}")
    long_name = info.get("longName") or info.get("shortName") or COMPANY_KO
    col5.metric("종목", long_name[:18] + ("…" if len(str(long_name)) > 18 else ""))

    sub = make_subplots(
        rows=2,
        cols=1,
        shared_xaxes=True,
        vertical_spacing=0.06,
        row_heights=[0.72, 0.28],
    )

    sub.add_trace(
        go.Candlestick(
            x=hist["Date"],
            open=hist["Open"],
            high=hist["High"],
            low=hist["Low"],
            close=hist["Close"],
            name="OHLC",
            increasing_line_color=_UP,
            decreasing_line_color=_DOWN,
        ),
        row=1,
        col=1,
    )

    for w in sorted(show_ma):
        ma = hist["Close"].rolling(window=w, min_periods=1).mean()
        sub.add_trace(
            go.Scatter(
                x=hist["Date"],
                y=ma,
                mode="lines",
                name=f"MA{w}",
                line=dict(width=1.2),
            ),
            row=1,
            col=1,
        )

    colors = [_UP if c >= o else _DOWN for o, c in zip(hist["Open"], hist["Close"])]
    sub.add_trace(
        go.Bar(
            x=hist["Date"],
            y=hist["Volume"],
            name="거래량",
            marker_color=colors,
            opacity=0.55,
        ),
        row=2,
        col=1,
    )

    sub.update_layout(
        height=640,
        margin=dict(l=8, r=8, t=40, b=8),
        legend=dict(
            orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1
        ),
        xaxis_rangeslider_visible=False,
        hovermode="x unified",
    )
    sub.update_yaxes(title_text="가격 (원)", row=1, col=1)
    sub.update_yaxes(title_text="거래량", row=2, col=1)

    st.plotly_chart(sub, use_container_width=True)

    with st.expander("기간 요약 통계"):
        c1, c2 = st.columns(2)
        with c1:
            st.write(
                pd.Series(
                    {
                        "기간 최고": f"{hist['High'].max():,.0f}원",
                        "기간 최저": f"{hist['Low'].min():,.0f}원",
                        "기간 종가 변동": f"{hist['Close'].iloc[0]:,.0f} → {hist['Close'].iloc[-1]:,.0f}원",
                    }
                )
            )
        with c2:
            ret = (hist["Close"].iloc[-1] / hist["Close"].iloc[0] - 1) * 100
            st.write(
                pd.Series(
                    {
                        "기간 수익률": f"{ret:+.2f}%",
                        "평균 거래량": f"{hist['Volume'].mean():,.0f}",
                        "표본 일수": len(hist),
                    }
                )
            )

    st.subheader("일별 시세 (최근)")
    display_cols = ["Date", "Open", "High", "Low", "Close", "Volume"]
    st.dataframe(
        hist[display_cols].iloc[::-1].head(60),
        use_container_width=True,
        hide_index=True,
    )


if __name__ == "__main__":
    main()

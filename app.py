"""
타이타닉 데이터 인터랙티브 대시보드 (Streamlit)
"""

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import streamlit as st

from survival_predict_ui import render_survival_prediction
from titanic_data import load_titanic

st.set_page_config(
    page_title="타이타닉 생존 분석",
    page_icon="🚢",
    layout="wide",
    initial_sidebar_state="expanded",
)

# 스타일 (대시보드 전용 · 파란색 테마)
_BLUE_SURVIVE = "#42a5f5"
_BLUE_DEATH = "#1565c0"

st.markdown(
    f"""
    <style>
        div.block-container {{
            padding-top: 1.2rem;
            max-width: 1200px;
        }}
        [data-testid="stAppViewContainer"] {{
            background: linear-gradient(165deg, #e3f2fd 0%, #f5f9ff 35%, #ffffff 100%);
        }}
        [data-testid="stHeader"] {{
            background: rgba(227, 242, 253, 0.92);
        }}
        [data-testid="stSidebar"] {{
            background: linear-gradient(180deg, #bbdefb 0%, #e3f2fd 55%, #ffffff 100%);
            border-right: 1px solid #90caf9;
        }}
        [data-testid="stSidebar"] h1,
        [data-testid="stSidebar"] h2,
        [data-testid="stSidebar"] h3,
        [data-testid="stSidebar"] .stMarkdown h1,
        [data-testid="stSidebar"] .stMarkdown h2 {{
            color: #0d47a1 !important;
        }}
        h1, h2, h3 {{
            color: #0d47a1 !important;
        }}
        hr {{
            border-color: #90caf9 !important;
        }}
        div[data-testid="stMetric"] {{
            background: rgba(255, 255, 255, 0.85);
            border: 1px solid #90caf9;
            border-radius: 12px;
            padding: 0.75rem 1rem;
            box-shadow: 0 2px 8px rgba(21, 101, 192, 0.08);
        }}
        .stMetric label p {{ font-size: 0.95rem; color: #1565c0 !important; }}
        .stMetric [data-testid="stMetricValue"] {{
            color: #0d47a1 !important;
        }}
    </style>
    """,
    unsafe_allow_html=True,
)


def main():
    df = load_titanic()

    st.title("타이타닉 생존 분석")
    tab_dashboard, tab_predict = st.tabs(["대시보드", "생존 예측"])

    # ---- 사이드바 필터 (대시보드 탭 전용)
    with st.sidebar:
        st.caption("아래 필터는 **대시보드** 탭의 차트에만 적용됩니다.")
        st.header("필터")
        sex_opts = st.multiselect(
            "성별",
            options=sorted(df["sex"].dropna().unique()),
            default=list(df["sex"].dropna().unique()),
        )
        class_opts = st.multiselect(
            "객실 등급",
            options=sorted(df["class"].dropna().unique(), key=lambda x: str(x)),
            default=list(df["class"].dropna().unique()),
        )
        town_opts = st.multiselect(
            "승선 항구",
            options=sorted(df["embark_town"].unique()),
            default=list(df["embark_town"].unique()),
        )
        age_range = st.slider(
            "나이 범위",
            float(df["age"].min()),
            float(df["age"].max()),
            (float(df["age"].min()), float(df["age"].max())),
        )

    mask = (
        df["sex"].isin(sex_opts)
        & df["class"].isin(class_opts)
        & df["embark_town"].isin(town_opts)
        & df["age"].between(age_range[0], age_range[1])
    )
    f = df.loc[mask].copy()

    with tab_dashboard:
        st.caption("Seaborn 내장 `titanic` 데이터셋 · 필터와 차트로 패턴 탐색")

    if f.empty:
        with tab_dashboard:
            st.warning("조건에 맞는 승객이 없습니다. 필터를 완화해 보세요.")
        with tab_predict:
            render_survival_prediction(form_key="predict_form_main", use_page_title=False)
        return

    with tab_dashboard:
        _render_dashboard_charts(f)

    with tab_predict:
        render_survival_prediction(form_key="predict_form_main", use_page_title=False)


def _render_dashboard_charts(f):
    # ---- KPI
    n = len(f)
    rate = f["survived"].mean()
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("필터 적용 승객 수", f"{n:,}명")
    col2.metric("생존률", f"{rate * 100:.1f}%")
    col3.metric("생존", f"{int(f['survived'].sum()):,}명")
    col4.metric("사망", f"{int((f['survived'] == 0).sum()):,}명")

    st.divider()

    row1_col1, row1_col2 = st.columns(2)

    with row1_col1:
        st.subheader("객실 등급별 생존")
        grp = (
            f.groupby(["class", "survived_label"], observed=True)
            .size()
            .reset_index(name="count")
        )
        fig1 = px.bar(
            grp,
            x="class",
            y="count",
            color="survived_label",
            barmode="group",
            color_discrete_map={"생존": _BLUE_SURVIVE, "사망": _BLUE_DEATH},
        )
        fig1.update_layout(
            xaxis_title="등급",
            yaxis_title="인원",
            legend_title="결과",
            height=400,
        )
        st.plotly_chart(fig1, use_container_width=True)

    with row1_col2:
        st.subheader("성별 · 객실 등급별 생존률")
        heat = (
            f.groupby(["sex", "class"], observed=True)["survived"]
            .mean()
            .unstack()
        )
        heat = heat.reindex(
            columns=sorted(f["class"].dropna().unique(), key=lambda x: str(x)),
            fill_value=0,
        )
        fig2 = px.imshow(
            heat.values * 100,
            x=[str(c) for c in heat.columns],
            y=[str(s) for s in heat.index],
            color_continuous_scale="Blues",
            zmin=0,
            zmax=100,
            aspect="auto",
            labels=dict(x="등급", y="성별", color="생존률 (%)"),
        )
        fig2.update_layout(height=400)
        st.plotly_chart(fig2, use_container_width=True)

    row2_col1, row2_col2 = st.columns(2)

    with row2_col1:
        st.subheader("나이 분포 (생존 vs 사망)")
        safe = f[["age", "survived_label"]].dropna()
        fig3 = px.histogram(
            safe,
            x="age",
            color="survived_label",
            barmode="overlay",
            opacity=0.65,
            nbins=30,
            color_discrete_map={"생존": _BLUE_SURVIVE, "사망": _BLUE_DEATH},
        )
        fig3.update_layout(
            xaxis_title="나이",
            yaxis_title="빈도",
            legend_title="결과",
            height=400,
        )
        st.plotly_chart(fig3, use_container_width=True)

    with row2_col2:
        st.subheader("운임 요금 vs 나이")
        fare_df = f.dropna(subset=["fare", "age"])
        fig4 = px.scatter(
            fare_df,
            x="age",
            y="fare",
            color="survived_label",
            size_max=12,
            opacity=0.7,
            color_discrete_map={"생존": _BLUE_SURVIVE, "사망": _BLUE_DEATH},
            hover_data=["class", "sex", "embark_town"],
        )
        fig4.update_layout(
            xaxis_title="나이",
            yaxis_title="운임 (fare)",
            legend_title="결과",
            height=400,
        )
        st.plotly_chart(fig4, use_container_width=True)

    st.subheader("동반 가족 규모별 생존")
    f["family"] = f["sibsp"] + f["parch"]
    fam = (
        f.groupby("family", observed=True)["survived"].agg(["mean", "count"]).reset_index()
    )
    fam = fam[fam["count"] >= 3]
    fig5 = make_subplots(specs=[[{"secondary_y": True}]])
    fig5.add_trace(
        go.Bar(
            x=fam["family"],
            y=fam["mean"] * 100,
            name="생존률 (%)",
            marker_color="#42a5f5",
        ),
        secondary_y=False,
    )
    fig5.add_trace(
        go.Scatter(
            x=fam["family"],
            y=fam["count"],
            mode="lines+markers",
            name="표본 수",
            line=dict(color="#0d47a1"),
        ),
        secondary_y=True,
    )
    fig5.update_layout(
        height=380,
        xaxis_title="동반 가족 수 (sibsp + parch)",
        yaxis_title="생존률 (%)",
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
    )
    fig5.update_yaxes(title_text="생존률 (%)", secondary_y=False)
    fig5.update_yaxes(title_text="인원 수", secondary_y=True)
    st.plotly_chart(fig5, use_container_width=True)

    with st.expander("필터 적용 데이터 미리보기"):
        st.dataframe(
            f[
                [
                    "survived",
                    "pclass",
                    "sex",
                    "age",
                    "sibsp",
                    "parch",
                    "fare",
                    "class",
                    "embark_town",
                ]
            ].head(200),
            use_container_width=True,
        )


if __name__ == "__main__":
    main()

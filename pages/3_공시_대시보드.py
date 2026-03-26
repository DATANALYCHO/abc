"""
Open DART API — 공시 검색·기업개황 대시보드
(인증키: https://opendart.fss.or.kr/ 에서 발급)
"""

from __future__ import annotations

from datetime import date, datetime, timedelta

import pandas as pd
import plotly.express as px
import streamlit as st

from dart_opendart import DartApiError, download_corp_code_zip_to_dataframe, fetch_company_overview, fetch_disclosure_list

st.set_page_config(
    page_title="Open DART 공시",
    page_icon="📋",
    layout="wide",
    initial_sidebar_state="expanded",
)

_PBLNTF_TY = {
    "": "전체",
    "A": "정기공시",
    "B": "주요사항보고",
    "C": "발행공시",
    "D": "지분공시",
    "E": "기타공시",
    "F": "외부감사관련",
    "G": "펀드공시",
    "H": "자산유동화",
    "I": "거래소공시",
    "J": "공정위공시",
}

_CORP_CLS = {
    "": "전체",
    "Y": "유가증권",
    "K": "코스닥",
    "N": "코넥스",
    "E": "기타",
}

_DETAIL_OPTIONS: dict[str, dict[str, str]] = {
    "": {"": "상세 유형 없음 (전체)"},
    "A": {
        "": "전체",
        "A001": "사업보고서",
        "A002": "반기보고서",
        "A003": "분기보고서",
        "A004": "등록법인결산서류(자본시장법이전)",
        "A005": "소액공모법인결산서류",
    },
    "B": {
        "": "전체",
        "B001": "주요사항보고서",
        "B002": "주요경영사항신고(자본시장법 이전)",
        "B003": "최대주주등과의거래신고(자본시장법 이전)",
    },
    "C": {
        "": "전체",
        "C001": "증권신고(지분증권)",
        "C002": "증권신고(채무증권)",
        "C003": "증권신고(파생결합증권)",
        "C004": "증권신고(합병등)",
        "C005": "증권신고(기타)",
    },
    "D": {
        "": "전체",
        "D001": "주식등의대량보유상황보고서",
        "D002": "임원·주요주주특정증권등소유상황보고서",
        "D003": "의결권대리행사권유",
        "D004": "공개매수",
        "D005": "임원·주요주주 특정증권등 거래계획보고서",
    },
}


def _get_api_key() -> str:
    try:
        k = st.secrets.get("DART_API_KEY", "")
        if k:
            return str(k).strip()
    except Exception:
        pass
    return ""


@st.cache_data(ttl=23 * 3600, show_spinner="고유번호 전체 목록을 받는 중입니다…")
def _cached_corp_table(api_key: str) -> pd.DataFrame:
    return download_corp_code_zip_to_dataframe(api_key)


def _fmt_yyyymmdd(d: date) -> str:
    return d.strftime("%Y%m%d")


def main() -> None:
    default_secret = _get_api_key()
    st.title("Open DART 공시 대시보드")
    st.caption("금융감독원 전자공시 Open API — 공시검색·기업개황")

    with st.sidebar:
        st.header("API 설정")
        api_key = st.text_input(
            "API 인증키 (40자리)",
            value=default_secret,
            type="password",
            help="비우면 `.streamlit/secrets.toml` 의 DART_API_KEY 사용",
            autocomplete="off",
        ).strip()
        if not api_key:
            api_key = default_secret
        if not api_key:
            st.warning("Open DART에서 발급한 인증키를 입력하거나 secrets.toml에 `DART_API_KEY`를 설정하세요.")
            st.markdown("[인증키 신청/관리](https://opendart.fss.or.kr/mng/userApiKeyListView.do)")
            return

        st.divider()
        st.subheader("고유번호 목록")
        load_corp = st.button("전체 회사 고유번호 불러오기 (캐시)", help="최초 1회 다운로드에 시간이 걸릴 수 있습니다.")
        corp_df = None
    if load_corp:
        try:
            corp_df_pre = _cached_corp_table(api_key)
            st.success(f"{len(corp_df_pre):,}건 로드됨 · 이후 동일 키는 캐시에서 빠르게 불러옵니다.")
        except DartApiError as e:
            st.error(str(e))
        except Exception as e:
            st.error(f"오류: {e}")
    st.caption("회사명 검색 시 고유번호 ZIP을 한 번 내려받습니다(캐시됨). 위 버튼으로 미리 받을 수 있습니다.")

    today = date.today()
    end_d = today
    start_d = today - timedelta(days=90)

    col_a, col_b, col_c = st.columns((1.2, 1, 1))
    with col_a:
        q_name = st.text_input("회사명 검색 (부분 일치)", placeholder="예: 삼성전자")
    with col_b:
        start_date = st.date_input("시작일", value=start_d, max_value=today)
    with col_c:
        end_date = st.date_input("종료일", value=end_d, max_value=today)

    if start_date > end_date:
        st.error("시작일이 종료일보다 늦을 수 없습니다.")
        return

    bgn = _fmt_yyyymmdd(start_date)
    end = _fmt_yyyymmdd(end_date)
    if not api_key:
        return

    corp_code_pick: str | None = None
    corp_df_loaded: pd.DataFrame | None = None
    if q_name.strip():
        try:
            corp_df_loaded = _cached_corp_table(api_key)
        except DartApiError as e:
            st.error(f"고유번호 목록을 불러오지 못했습니다: {e}")
            st.stop()
        except Exception as e:
            st.error(f"고유번호 목록 오류: {e}")
            st.stop()

    if corp_df_loaded is not None and len(corp_df_loaded) > 0 and q_name.strip():
        sub = corp_df_loaded[corp_df_loaded["corp_name"].str.contains(q_name.strip(), case=False, na=False)]
        sub = sub[sub["corp_code"].str.len() > 0]
        if sub.empty:
            st.info("검색 조건에 맞는 회사가 고유번호 목록에 없습니다.")
        else:
            sub = sub.sort_values("corp_name").head(200)
            labels = [
                f"{r['corp_name']} ({r['corp_code']}) — 종목 {r['stock_code'] or '-'}"
                for _, r in sub.iterrows()
            ]
            codes = sub["corp_code"].tolist()
            choice = st.selectbox("선택한 회사 (고유번호)", options=range(len(labels)), format_func=lambda i: labels[i])
            corp_code_pick = codes[int(choice)]
    elif q_name.strip():
        st.info("검색어에 해당하는 회사가 없습니다. 검색어를 바꾸거나 비워서 시장 전체를 조회해 보세요.")

    f1, f2, f3, f4 = st.columns(4)
    with f1:
        ty_keys = list(_PBLNTF_TY.keys())
        ty_labels = [f"{k} — {_PBLNTF_TY[k]}" if k else _PBLNTF_TY[k] for k in ty_keys]
        p_ix = st.selectbox("공시 유형", range(len(ty_keys)), format_func=lambda i: ty_labels[i])
        pblntf_ty = ty_keys[int(p_ix)]
    with f2:
        detail_map = _DETAIL_OPTIONS.get(pblntf_ty, {"": "상세 유형 없음 (전체)"})
        d_keys = list(detail_map.keys())
        d_pick = st.selectbox(
            "공시 상세",
            options=d_keys,
            format_func=lambda k: detail_map.get(k, k),
            key=f"dart_detail_{pblntf_ty or 'all'}",
        )
        pblntf_detail = str(d_pick) if d_pick else None
    with f3:
        c_keys = list(_CORP_CLS.keys())
        c_labels = [_CORP_CLS[k] for k in c_keys]
        c_ix = st.selectbox("법인 구분", range(len(c_keys)), format_func=lambda i: c_labels[i])
        corp_cls = c_keys[int(c_ix)]
    with f4:
        page_count = st.selectbox("페이지당 건수", [10, 20, 50, 100], index=3)
        page_no = st.number_input("페이지 번호", min_value=1, max_value=99999, value=1, step=1)

    if not corp_code_pick:
        delta_days = (end_date - start_date).days
        if delta_days > 93:
            st.warning("회사를 지정하지 않으면 검색 기간은 **약 3개월 이내**로 제한됩니다. 기간을 줄이거나 회사를 선택하세요.")
            return

    run = st.button("공시 검색", type="primary")
    if not run:
        st.stop()

    try:
        items, meta = fetch_disclosure_list(
            api_key,
            corp_code=corp_code_pick,
            bgn_de=bgn,
            end_de=end,
            pblntf_ty=pblntf_ty or None,
            pblntf_detail_ty=pblntf_detail or None,
            corp_cls=corp_cls or None,
            page_no=int(page_no),
            page_count=int(page_count),
        )
    except DartApiError as e:
        st.error(str(e))
        st.stop()
    except Exception as e:
        st.error(f"요청 실패: {e}")
        st.stop()

    m1, m2, m3 = st.columns(3)
    m1.metric("총 건수(검색)", f"{meta['total_count']:,}")
    m2.metric("현재 페이지", f"{meta['page_no']} / {max(meta['total_page'], 1)}")
    m3.metric("이 페이지 행 수", len(items))

    if not items:
        st.info("조건에 맞는 공시가 없습니다.")
    else:
        df = pd.DataFrame(items)
        rename = {
            "corp_name": "회사명",
            "stock_code": "종목코드",
            "corp_code": "고유번호",
            "corp_cls": "법인구분",
            "report_nm": "보고서명",
            "rcept_no": "접수번호",
            "flr_nm": "제출인",
            "rcept_dt": "접수일",
            "rm": "비고",
        }
        df = df.rename(columns={k: v for k, v in rename.items() if k in df.columns})
        if "접수번호" in df.columns:
            df["DART에서 보기"] = df["접수번호"].apply(
                lambda x: f"https://dart.fss.or.kr/dsaf001/main.do?rcpNo={x}"
            )
        show_cols = [c for c in ["회사명", "종목코드", "법인구분", "보고서명", "접수일", "제출인", "비고", "DART에서 보기"] if c in df.columns]
        st.dataframe(
            df[show_cols],
            use_container_width=True,
            hide_index=True,
            column_config={
                "DART에서 보기": st.column_config.LinkColumn("DART에서 보기", display_text="열기"),
            },
        )

        if "접수일" in df.columns:
            cnt = df.groupby("접수일", as_index=False).size().rename(columns={"size": "건수"})
            if not cnt.empty:
                fig = px.bar(cnt, x="접수일", y="건수", title="접수일별 공시 건수 (현재 페이지)")
                fig.update_layout(height=360, xaxis_tickangle=-45)
                st.plotly_chart(fig, use_container_width=True)

    if corp_code_pick:
        with st.expander("선택 회사 기업개황 (company.json)", expanded=False):
            try:
                ov = fetch_company_overview(api_key, corp_code_pick)
                st.json(ov)
            except DartApiError as e:
                st.warning(str(e))


if __name__ == "__main__":
    main()

"""
성별·탑승 클래스·나이 입력 → 생존 예측
(동일 UI는 app.py 「생존 예측」 탭에서도 사용 가능)
"""

import streamlit as st

from survival_predict_ui import render_survival_prediction

st.set_page_config(
    page_title="타이타닉 생존 예측",
    page_icon="🎯",
    layout="centered",
)

render_survival_prediction(form_key="predict_form_page", use_page_title=True)

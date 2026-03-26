"""타이타닉 생존 예측 — app.py 「생존 예측」 탭과 동일 UI."""

import streamlit as st

from survival_predict_ui import render_survival_prediction

st.set_page_config(page_title="타이타닉 생존 예측", page_icon="🎯", layout="centered")
render_survival_prediction(form_key="predict_form_page", use_page_title=True)

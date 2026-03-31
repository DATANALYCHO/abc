"""생존 예측 폼·결과 UI (메인 탭 / pages 공용)"""

import streamlit as st

from titanic_data import load_titanic
from titanic_model import predict_row, train_survival_model


@st.cache_resource
def get_survival_model():
    return train_survival_model(load_titanic())


def render_survival_prediction(*, form_key: str, use_page_title: bool = False):
    """
    form_key: 탭·페이지별로 고유해야 함.
    use_page_title: True면 st.title, False면 st.subheader.
    """
    if use_page_title:
        st.title("생존 예측")
    else:
        st.subheader("생존 예측")

    st.caption(
        "같은 데이터로 학습한 단순 모델입니다. 참고용이며 실제 의료·안전 판단에는 사용할 수 없습니다."
    )

    df = load_titanic()
    class_labels = {"일등석": "First", "이등석": "Second", "삼등석": "Third"}
    sex_labels = {"남성": "male", "여성": "female"}

    with st.form(form_key):
        sex_k = st.radio("성별", list(sex_labels.keys()), horizontal=True)
        class_k = st.selectbox("탑승 클래스", list(class_labels.keys()))
        age = st.number_input(
            "나이",
            min_value=0.0,
            max_value=100.0,
            value=30.0,
            step=1.0,
        )
        submitted = st.form_submit_button("예측하기", type="primary")

    if not submitted:
        return

    pipe = get_survival_model()
    sex = sex_labels[sex_k]
    pclass = class_labels[class_k]
    survived, p_survive, p_death = predict_row(pipe, sex, pclass, age)

    st.divider()
    if survived == 1:
        st.success(f"**예측 결과: 생존** (추정 확률 {p_survive * 100:.1f}%)")
    else:
        st.error(f"**예측 결과: 사망** (생존 추정 확률 {p_survive * 100:.1f}%)")

    st.caption(
        f"입력: {sex_k}, {class_k}, {age:g}세 · 사망 쪽 확률 {p_death * 100:.1f}%"
    )

    with st.expander("데이터셋에서 유사 조건 생존률"):
        sub = df[
            (df["sex"] == sex)
            & (df["class"] == pclass)
            & (df["age"] >= age - 5)
            & (df["age"] <= age + 5)
        ]
        if len(sub) < 3:
            sub = df[(df["sex"] == sex) & (df["class"] == pclass)]
        if len(sub) == 0:
            st.write("해당 조합 표본이 없습니다.")
        else:
            rate = sub["survived"].mean()
            st.write(
                f"표본 **{len(sub)}명** 중 생존률 약 **{rate * 100:.1f}%** (나이는 ±5세 완화 시 비교)"
            )

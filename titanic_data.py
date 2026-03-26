"""타이타닉 데이터 로드 (대시보드·예측 페이지 공용)"""

import seaborn as sns


def load_titanic():
    df = sns.load_dataset("titanic").copy()
    df["survived_label"] = df["survived"].map({0: "사망", 1: "생존"})
    df["who"] = df["who"].fillna("unknown")
    df["embark_town"] = df["embark_town"].fillna("미상")
    df["age"] = df["age"].fillna(df["age"].median())
    return df

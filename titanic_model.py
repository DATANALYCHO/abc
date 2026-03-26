"""성별·객실 등급·나이만 사용하는 생존 예측 모델"""

from sklearn.compose import ColumnTransformer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder


def train_survival_model(df):
    X = df[["sex", "class", "age"]].copy()
    y = df["survived"]
    preprocessor = ColumnTransformer(
        transformers=[
            (
                "cat",
                OneHotEncoder(
                    drop="first",
                    sparse_output=False,
                    handle_unknown="ignore",
                ),
                ["sex", "class"],
            ),
            ("num", "passthrough", ["age"]),
        ]
    )
    pipe = Pipeline(
        [
            ("prep", preprocessor),
            ("clf", LogisticRegression(max_iter=1000)),
        ]
    )
    pipe.fit(X, y)
    return pipe


def predict_row(pipe, sex: str, pclass: str, age: float):
    import pandas as pd

    x = pd.DataFrame([{"sex": sex, "class": pclass, "age": float(age)}])
    proba = pipe.predict_proba(x)[0]
    survived = int(pipe.predict(x)[0])
    return survived, float(proba[1]), float(proba[0])

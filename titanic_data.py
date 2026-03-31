"""타이타닉 데이터 로드 (대시보드·예측 페이지 공용)."""

from __future__ import annotations

from functools import lru_cache

import pandas as pd
import seaborn as sns

_SURVIVED_MAP = {0: "사망", 1: "생존"}


@lru_cache(maxsize=1)
def _titanic_prepared() -> pd.DataFrame:
    df = sns.load_dataset("titanic").copy()
    med_age = df["age"].median()
    df["survived_label"] = df["survived"].map(_SURVIVED_MAP)
    df["who"] = df["who"].fillna("unknown")
    df["embark_town"] = df["embark_town"].fillna("미상")
    df["age"] = df["age"].fillna(med_age)
    return df


def load_titanic() -> pd.DataFrame:
    """전처리된 데이터프레임 복사본(호출처에서 제자리 수정해도 캐시가 오염되지 않음)."""
    return _titanic_prepared().copy()

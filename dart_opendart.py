"""Open DART API (opendart.fss.or.kr) — 공시검색·고유번호·기업개황."""

from __future__ import annotations

import io
import zipfile
import xml.etree.ElementTree as ET
from typing import Any

import pandas as pd
import requests

BASE = "https://opendart.fss.or.kr/api"


class DartApiError(Exception):
    """Open DART API가 status != 000 인 경우."""

    def __init__(self, status: str, message: str):
        self.status = status
        self.message = message
        super().__init__(f"[{status}] {message}")


def _check_json(data: dict[str, Any]) -> None:
    status = str(data.get("status", ""))
    if status == "000":
        return
    if status == "013":
        return
    raise DartApiError(status, str(data.get("message", "")))


def fetch_disclosure_list(
    api_key: str,
    *,
    corp_code: str | None = None,
    bgn_de: str | None = None,
    end_de: str | None = None,
    pblntf_ty: str | None = None,
    pblntf_detail_ty: str | None = None,
    corp_cls: str | None = None,
    last_reprt_at: str | None = None,
    sort: str | None = None,
    sort_mth: str | None = None,
    page_no: int = 1,
    page_count: int = 100,
    timeout: int = 60,
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    """공시검색 (list.json). 반환: (목록, 메타: total_count, page_no, ...)."""
    params: dict[str, str] = {
        "crtfc_key": api_key,
        "page_no": str(page_no),
        "page_count": str(min(max(page_count, 1), 100)),
    }
    if corp_code:
        params["corp_code"] = corp_code
    if bgn_de:
        params["bgn_de"] = bgn_de
    if end_de:
        params["end_de"] = end_de
    if pblntf_ty:
        params["pblntf_ty"] = pblntf_ty
    if pblntf_detail_ty:
        params["pblntf_detail_ty"] = pblntf_detail_ty
    if corp_cls:
        params["corp_cls"] = corp_cls
    if last_reprt_at:
        params["last_reprt_at"] = last_reprt_at
    if sort:
        params["sort"] = sort
    if sort_mth:
        params["sort_mth"] = sort_mth

    r = requests.get(f"{BASE}/list.json", params=params, timeout=timeout)
    r.raise_for_status()
    data = r.json()
    _check_json(data)
    raw_list = data.get("list")
    items: list[dict[str, Any]] = raw_list if isinstance(raw_list, list) else []
    meta = {
        "total_count": int(data.get("total_count") or 0),
        "total_page": int(data.get("total_page") or 0),
        "page_no": int(data.get("page_no") or page_no),
        "page_count": int(data.get("page_count") or page_count),
    }
    return items, meta


def fetch_company_overview(api_key: str, corp_code: str, timeout: int = 30) -> dict[str, Any]:
    """기업개황 (company.json)."""
    r = requests.get(
        f"{BASE}/company.json",
        params={"crtfc_key": api_key, "corp_code": corp_code},
        timeout=timeout,
    )
    r.raise_for_status()
    data = r.json()
    _check_json(data)
    return {k: v for k, v in data.items() if k not in ("status", "message")}


def download_corp_code_zip_to_dataframe(api_key: str, timeout: int = 120) -> pd.DataFrame:
    """고유번호 전체 목록(corpCode.zip)을 내려받아 DataFrame으로 파싱."""
    r = requests.get(f"{BASE}/corpCode.xml", params={"crtfc_key": api_key}, timeout=timeout)
    r.raise_for_status()
    try:
        zf = zipfile.ZipFile(io.BytesIO(r.content))
    except zipfile.BadZipFile as e:
        raise DartApiError("zip", "고유번호 파일이 ZIP 형식이 아닙니다. API 키·응답을 확인하세요.") from e
    xml_names = [n for n in zf.namelist() if n.lower().endswith(".xml")]
    if not xml_names:
        raise DartApiError("xml", "ZIP 안에 XML 파일이 없습니다.")
    with zf.open(xml_names[0]) as f:
        tree = ET.parse(f)
    root = tree.getroot()

    def text(el: ET.Element | None, tag: str) -> str:
        if el is None:
            return ""
        node = el.find(tag)
        if node is None or node.text is None:
            return ""
        return str(node.text).strip()

    rows: list[dict[str, str]] = []
    for block in root.findall(".//list"):
        rows.append(
            {
                "corp_code": text(block, "corp_code"),
                "corp_name": text(block, "corp_name"),
                "stock_code": text(block, "stock_code"),
                "modify_date": text(block, "modify_date"),
            }
        )
    return pd.DataFrame(rows)

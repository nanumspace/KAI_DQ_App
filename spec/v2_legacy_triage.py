# -*- coding: utf-8 -*-
"""사전 v2.2 · v1 미승격 필드 분류.

배치표가 '이동/이관→코어'라고 한 v1 컬럼 중, 어떤 v2 항목도 '현 명세 대응 필드'로
지목하지 않은 것이 미승격으로 남는다. 그런데 그 수(575)는 실제 누락이 아니라 대부분
기록·연결의 문제다. 그대로 575줄을 내놓으면 팀이 검토할 수 없으므로 다섯으로 나눈다.

  키·외래키                    데이터 항목이 아니다. 볼 것 없다.
  코드·명칭 쌍의 명칭쪽          v1 은 코드와 명칭을 두 컬럼으로 받았고 v2 는 concept_id
                              하나로 받는다. 구조가 흡수한 것이라 승격 대상이 아니다.
  v2 에 이미 대응 있음          서식 필드·코어 파생 변수·값 집합 중에 같은 뜻이 이미 있다.
                              배치표에 대응 필드를 적어 넣으면 이 목록에서 빠진다.
  부분 일치                    비슷한 것이 있으나 같은지 사람이 봐야 한다.
  대응 없음                    실제 승격 후보. 이것만 임상 판단이 필요하다.

분류는 낱말 겹침으로 하는 어림이라 완벽하지 않다. 특히 '수술을 시행한 연월일'과
'수술일'처럼 같은 뜻인데 낱말이 어긋나면 '대응 없음'으로 잘못 떨어진다. 그래서
'대응 없음'은 승격해야 할 목록이 아니라 **사람이 볼 목록**으로 읽어야 한다.
"""
import re

PAIR_SUFFIX = [("_spnm", "_spcd"), ("_knnm", "_kncd"), ("_nm", "_cd")]
# 낱말 겹침을 셀 때 빼는 흔한 말 — 어느 설명에나 나와 변별력이 없다.
STOP = {"코드값", "명칭", "여부", "시행", "확인", "해당", "사용", "경우", "환자", "기록",
        "수집", "위한", "이다", "나타내는", "대한", "정보", "내용", "구분", "기타"}

BUCKETS = ["키·외래키", "코드·명칭 쌍의 명칭쪽", "v2 에 이미 대응 있음", "부분 일치", "대응 없음"]


def _nouns(text):
    return {w for w in re.findall(r"[가-힣]{2,}", text or "")} - STOP


def _head(desc):
    """설명에서 뜻을 담은 앞부분만 남긴다 ('…를 나타내는 코드값이다' 같은 꼬리를 떼낸다)."""
    d = re.sub(r"\s*(이다|입니다)\.?\s*$", "", (desc or "").strip())
    d = re.sub(r"(을|를)?\s*나타내는\s*코드값$|코드값$|명칭$|여부$", "", d).strip()
    return d


def classify(legacy_rows, v1_field_names, v1_desc, v2_labels):
    """미승격 행을 다섯 묶음으로 나눈다.

    legacy_rows   : [(목적지, 'V1TABLE.field'), …]
    v1_field_names: {v1 테이블: {필드명, …}}  — 코드·명칭 쌍을 찾는 데 쓴다
    v1_desc       : {'V1TABLE.field': 설명}
    v2_labels     : v2 가 이미 가진 한글 이름 모음(서식 필드 kor + 파생 변수 kor + 값 라벨)
    """
    pool = [(lab, _nouns(lab)) for lab in v2_labels if lab]
    out = {b: [] for b in BUCKETS}
    for dest, key in legacy_rows:
        table, _, name = key.partition(".")
        desc = v1_desc.get(key, "")
        row = dict(dest=dest, v1=key, desc=desc[:120], match="")
        if name.endswith("_id") and ("외래키" in desc or "식별자" in desc):
            out["키·외래키"].append(row); continue
        if any(name.endswith(s) and (name[: -len(s)] + c) in v1_field_names.get(table, ()) for s, c in PAIR_SUFFIX):
            out["코드·명칭 쌍의 명칭쪽"].append(row); continue
        want = _nouns(_head(desc))
        best = max(((len(want & pn), lab) for lab, pn in pool), default=(0, ""))
        if best[0] >= 2:
            row["match"] = best[1]; out["v2 에 이미 대응 있음"].append(row)
        elif best[0] == 1:
            row["match"] = best[1]; out["부분 일치"].append(row)
        else:
            out["대응 없음"].append(row)
    return out

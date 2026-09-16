# -*- coding: utf-8 -*-
"""임상 검토 묶음을 만든다 → pilot/review/*.xlsx

    uv run --with openpyxl --with pyyaml python pilot/build_review.py

두 가지를 사람이 보게 내놓는다.

1) 병리 보고서 조건부 필수 검토 (pathology_conditional_review.xlsx)
   PATHOLOGY_REPORT 의 컬럼은 생검 보고서에만, 수술 보고서에만, 또는 둘 다에 필수다.
   34개는 정했고 10개는 판단이 서지 않아 '둘 다'로 두었다. 임상 검토자가 이 10개를 정한다.
   참고로 이미 정한 34개도 같은 표에 둔다 — 그것도 틀렸을 수 있다.

2) v1 → v2 미승격 필드 검토 (legacy_fields_review.xlsx)
   v1 의 575개 컬럼이 v2 에 자리가 없다. 다섯 묶음으로 나눴고, 그중 '대응 없음'(83)과
   '부분 일치'(149)만 사람이 본다. 나머지 셋은 참고용 시트로 둔다.
   병원이 "이 항목 어디 갔나요" 물을 때 이 표로 답한다.
"""
import io
import os
import sys

import yaml
from openpyxl import Workbook
from openpyxl.styles import Alignment, Font, PatternFill
from openpyxl.utils import get_column_letter

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "spec"))
from v2_row_kinds import EXTRA_CONDITIONS, NEEDS_REVIEW, ROW_KINDS  # noqa: E402

OUT = os.path.join(ROOT, "pilot", "review")
HEAD = Font(bold=True)
FILL = PatternFill("solid", fgColor="E8EEF7")
ASK = PatternFill("solid", fgColor="FFF4D6")


def sheet(wb, title, header, rows, widths, ask_cols=()):
    ws = wb.create_sheet(title)
    ws.append(header)
    for c in ws[1]:
        c.font = HEAD
        c.fill = FILL
    for r in rows:
        ws.append(r)
    for i, w in enumerate(widths, 1):
        ws.column_dimensions[get_column_letter(i)].width = w
    for col in ask_cols:
        for row in ws.iter_rows(min_row=2, min_col=col, max_col=col):
            for c in row:
                c.fill = ASK
    for row in ws.iter_rows(min_row=2):
        for c in row:
            c.alignment = Alignment(wrap_text=True, vertical="top")
    ws.freeze_panes = "A2"
    return ws


def pathology():
    spec = yaml.safe_load(io.open(os.path.join(ROOT, "spec/v2/kai_cdm_spec_v2.yaml"), encoding="utf-8"))["tables"]
    fields = {f["name"]: f for f in spec["PATHOLOGY_REPORT"]["fields"]}
    rk = ROW_KINDS["PATHOLOGY_REPORT"]
    pending = set(NEEDS_REVIEW["PATHOLOGY_REPORT"])
    label = {"BIOPSY": "생검만", "SURGICAL": "수술만", "BOTH": "둘 다"}
    rows = []
    for name, kind in rk["applies"].items():
        f = fields.get(name, {})
        cond = EXTRA_CONDITIONS.get(("PATHOLOGY_REPORT", name))
        cond_txt = ""
        if isinstance(cond, str):
            cond_txt = f"{cond} 가 채워져 있을 때만"
        elif isinstance(cond, tuple) and len(cond) == 2:
            cond_txt = f"{cond[0]} 에 '{cond[1]}' 이 들어 있을 때만"
        elif isinstance(cond, tuple) and len(cond) == 3:
            cond_txt = f"{cond[0]} = {cond[2]} 일 때만"
        rows.append([
            "검토 요청" if name in pending else "정함",
            name, f.get("kor", ""), ", ".join(f.get("cohorts", []) or []),
            label.get(kind, kind), cond_txt,
            "", "",
        ])
    rows.sort(key=lambda r: (r[0] != "검토 요청", r[1]))
    wb = Workbook()
    wb.remove(wb.active)
    ws = sheet(wb, "조건부 필수",
               ["상태", "컬럼", "한글 이름", "코호트", "지금 설정 (어느 보고서에 필수)", "추가 조건", "검토자 판단 (생검만 / 수술만 / 둘 다 / 필수 아님)", "비고"],
               rows, [10, 42, 30, 34, 22, 36, 30, 30], ask_cols=(7, 8))
    ws.insert_rows(1)
    ws["A1"] = ("PATHOLOGY_REPORT 의 컬럼이 생검 보고서·수술 보고서 중 어느 쪽에 필수인지 정합니다. "
                "'검토 요청' 10개는 판단이 서지 않아 '둘 다'로 두었습니다 — 예컨대 림프관·혈관 침윤은 생검에서도 볼 수 있지만 수술 검체에서 확정합니다. "
                "노란 칸을 채워 주세요. '정함' 34개도 틀렸다고 보시면 고쳐 주세요.")
    ws["A1"].alignment = Alignment(wrap_text=True)
    ws.merge_cells("A1:H1")
    ws.row_dimensions[1].height = 48
    ws.freeze_panes = "A3"
    p = os.path.join(OUT, "pathology_conditional_review.xlsx")
    wb.save(p)
    return p, sum(1 for r in rows if r[0] == "검토 요청"), len(rows)


def legacy():
    d = yaml.safe_load(io.open(os.path.join(ROOT, "spec/v2/legacy_fields_v2.yaml"), encoding="utf-8"))
    tri = d["triage"]
    wb = Workbook()
    wb.remove(wb.active)
    order = ["대응 없음", "부분 일치", "v2 에 이미 대응 있음", "코드·명칭 쌍의 명칭쪽", "키·외래키"]
    counts = {}
    for b in order:
        items = tri.get(b, [])
        counts[b] = len(items)
        ask = b in ("대응 없음", "부분 일치")
        header = ["v1 컬럼", "v1 설명", "v2 에서 갈 곳(배치표)", "v2 에 비슷한 것"] + (["검토자 판단 (승격 / 대응 있음 / 버림)", "v2 대응 항목 또는 이유"] if ask else [])
        rows = [[it["v1"], it.get("desc", ""), it.get("dest", ""), it.get("match", "")] + ([""] * 2 if ask else []) for it in items]
        sheet(wb, b[:31], header, rows, [40, 60, 24, 30, 24, 30], ask_cols=(5, 6) if ask else ())
    ws = wb.create_sheet("안내", 0)
    lines = [
        "v1 → v2 미승격 필드 검토",
        "",
        "v1 명세의 컬럼 575개가 v2 에 자리가 없습니다. 다섯 묶음으로 나눴습니다.",
        "",
        "  대응 없음 (%d)            실제 승격 후보. 임상 판단이 필요합니다. ← 이 시트를 봐 주세요" % counts["대응 없음"],
        "  부분 일치 (%d)            비슷한 v2 항목이 있으나 같은지 사람이 봐야 합니다. ← 이 시트도" % counts["부분 일치"],
        "  v2 에 이미 대응 있음 (%d)  같은 뜻이 v2 에 있습니다. 참고용" % counts["v2 에 이미 대응 있음"],
        "  코드·명칭 쌍의 명칭쪽 (%d) v1 은 코드와 명칭을 두 컬럼으로, v2 는 concept_id 하나로 받습니다. 구조가 흡수한 것" % counts["코드·명칭 쌍의 명칭쪽"],
        "  키·외래키 (%d)             데이터 항목이 아닙니다" % counts["키·외래키"],
        "",
        "분류는 낱말 겹침으로 한 어림이라 완벽하지 않습니다. '수술을 시행한 연월일'과 '수술일'처럼 같은 뜻인데 낱말이 어긋나면",
        "'대응 없음'으로 잘못 떨어집니다. 그래서 '대응 없음'은 승격할 목록이 아니라 사람이 볼 목록입니다.",
        "",
        "노란 칸에 판단을 적어 주세요: 승격(v2 에 새 항목으로) / 대응 있음(v2 의 어느 항목인지) / 버림(왜).",
        "병원이 \"이 항목 어디 갔나요\" 물을 때 이 표로 답합니다.",
    ]
    for i, t in enumerate(lines, 1):
        ws.cell(row=i, column=1, value=t)
    ws.column_dimensions["A"].width = 120
    p = os.path.join(OUT, "legacy_fields_review.xlsx")
    wb.save(p)
    return p, counts


if __name__ == "__main__":
    os.makedirs(OUT, exist_ok=True)
    p1, ask, total = pathology()
    print(f"{os.path.relpath(p1, ROOT)}: 검토 요청 {ask}개 / 전체 {total}개")
    p2, counts = legacy()
    print(f"{os.path.relpath(p2, ROOT)}: " + ", ".join(f"{k} {v}" for k, v in counts.items()))

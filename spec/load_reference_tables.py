#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""참조표 만들기 — 로컬 원본에서 spec/v2/vocab/ref/ 에 코드 표를 생성한다.

왜 저장소에 표를 두지 않는가: MedDRA·SNOMED 는 재배포가 제한된 라이선스이고,
심평원 마스터는 공개 데이터지만 원본이 수십 MB다. 그래서 저장소에는 등록부
(`spec/v2_reference_tables.py` → `spec/v2/vocab/REFERENCE_TABLE.csv`)만 두고,
표의 내용은 각자 자기 원본으로 만든다. 만들어진 자리는 gitignore 되어 있다.

쓰기:
    uv run --with-requirements spec/requirements.txt python spec/load_reference_tables.py
    KAI_REF_ROOT=/경로/표준용어 python spec/load_reference_tables.py --only REF_MEDDRA_PT

원본이 없는 표는 건너뛰고 무엇이 없는지 알려준다. SNOMED 계열은 로컬 배포본 대신
용어 서버에서 ECL 로 받아야 해서 여기서는 만들지 않고 그 사실만 남긴다.
"""
import argparse
import csv
import hashlib
import io
import json
import os
import sys
import zipfile

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from v2_reference_tables import REFERENCE_TABLES, DEFAULT_REF_ROOT  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "spec", "v2", "vocab", "ref")


def _rows_meddra(R, ref_root):
    """MedDRA PT: '$' 로 나뉜 asc. 영문 판에서 코드·영문명을, 한글 판에서 한글명을 가져온다."""
    def read_pt(zpath):
        with zipfile.ZipFile(zpath) as z:
            name = next(n for n in z.namelist() if os.path.basename(n) == "pt.asc")  # hlt_pt.asc 와 헷갈리면 안 된다
            text = z.read(name).decode("utf-8", "replace")
        out = {}
        for line in text.splitlines():
            if not line.strip():
                continue
            f = line.split("$")
            if len(f) > 1 and f[0].isdigit():
                out[f[0]] = f[1]
        return out
    en = read_pt(os.path.join(ref_root, R["source"]))
    ko_path = os.path.join(ref_root, R.get("source_ko") or "")
    ko = read_pt(ko_path) if R.get("source_ko") and os.path.exists(ko_path) else {}
    return [dict(code=c, label_en=n, label_ko=ko.get(c, "")) for c, n in sorted(en.items())]


def _rows_csv(R, ref_root, encoding="utf-8"):
    """열 이름으로 코드·표기를 뽑는 일반 CSV 원본."""
    path = os.path.join(ref_root, R["source"])
    with open(path, encoding=encoding, errors="replace", newline="") as fh:
        reader = csv.DictReader(fh)
        reader.fieldnames = [(n or "").lstrip("﻿") for n in (reader.fieldnames or [])]
        for col in (R["code"], R["label"]):
            if col not in reader.fieldnames:
                raise KeyError(f"{os.path.basename(path)} 에 '{col}' 열이 없다 (있는 열: {reader.fieldnames[:8]}…)")
        seen, rows = set(), []
        for r in reader:
            code, label = (r.get(R["code"]) or "").strip(), (r.get(R["label"]) or "").strip()
            if not code or code in seen:
                continue
            seen.add(code)
            rows.append(dict(code=code, label_en="", label_ko=label))
    return rows


BUILDERS = {
    "REF_MEDDRA_PT": _rows_meddra,
    "REF_EDI_PROCEDURE": _rows_csv,
    "REF_EDI_DRUG": _rows_csv,
    "REF_KCD": _rows_csv,
    "REF_LOINC": lambda R, root: [dict(code=r["code"], label_en=r["label_ko"], label_ko="") for r in _rows_csv(R, root)],
}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--ref-root", default=os.environ.get("KAI_REF_ROOT", DEFAULT_REF_ROOT),
                    help="표준 용어 원본이 있는 뿌리 경로")
    ap.add_argument("--only", action="append", help="이 참조표만 만든다(여러 번 지정 가능)")
    ap.add_argument("--out", default=OUT)
    args = ap.parse_args()

    os.makedirs(args.out, exist_ok=True)
    manifest, made, skipped = {}, 0, []
    for ref_id, R in REFERENCE_TABLES.items():
        if args.only and ref_id not in args.only:
            continue
        if ref_id not in BUILDERS:
            skipped.append((ref_id, f"ECL({R['ecl']})로 용어 서버에서 받는다" if R.get("ecl") else "자동 생성기 없음 · " + R["obtain"]))
            continue
        src = os.path.join(args.ref_root, R["source"])
        if not os.path.exists(src):
            skipped.append((ref_id, f"원본 없음: {src}"))
            continue
        try:
            rows = BUILDERS[ref_id](R, args.ref_root)
        except Exception as e:  # 원본 형식이 바뀌면 그 표만 건너뛰고 이유를 남긴다
            skipped.append((ref_id, f"읽기 실패: {e}"))
            continue
        path = os.path.join(args.out, f"{ref_id}.csv")
        buf = io.StringIO()
        w = csv.DictWriter(buf, ["code", "label_en", "label_ko"], lineterminator="\n")
        w.writeheader()
        w.writerows(rows)
        data = buf.getvalue()
        with open(path, "w", encoding="utf-8", newline="") as fh:
            fh.write(data)
        manifest[ref_id] = dict(rows=len(rows), sha256=hashlib.sha256(data.encode()).hexdigest(),
                                vocabulary=R["vocabulary"], version=R["version"], license=R["license"],
                                source=os.path.relpath(src, args.ref_root))
        made += 1
        print(f"  {ref_id:22s} {len(rows):>8,}행  ({R['vocabulary']} {R['version']})")

    if manifest:
        mpath = os.path.join(args.out, "manifest.json")
        old = json.load(open(mpath, encoding="utf-8")) if os.path.exists(mpath) else {}
        old.update(manifest)
        json.dump(old, open(mpath, "w", encoding="utf-8"), ensure_ascii=False, indent=2, sort_keys=True)

    print(f"\n만든 표 {made}개 → {os.path.relpath(args.out, ROOT)}/ (저장소에 올라가지 않는다)")
    for ref_id, why in skipped:
        print(f"  건너뜀 {ref_id}: {why}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

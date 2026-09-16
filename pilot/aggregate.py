# -*- coding: utf-8 -*-
"""중앙용 집계: 여러 기관의 submission.json 을 모아 규칙별로 본다.

    python pilot/aggregate.py <submission.json 또는 폴더> ... [--out <폴더>]

표준 라이브러리만 쓴다. 기관 이름은 파일이 든 폴더 이름(또는 --name 으로 준 것)이다.
같은 기관·같은 코호트의 실행이 여럿이면 가장 늦은 것(generated_at)만 쓴다 — 형식 문제를 고친 뒤의
두 번째 실행이 첫 실행을 덮는다.

산출물
  rules_by_site.csv   규칙 × 기관 표. 칸은 위반 건수(통과 0, 건너뜀 '-', 오류 '!')
  rules_summary.csv   규칙마다 실패한 기관 수, 위반 합계, 검사 행 합계
  sites.csv           기관·코호트마다 규칙·위반·행 수와 정규화 건수
  summary.md          사람이 읽는 요약: 모든 기관에서 우는 규칙(규칙·명세를 의심), 한 기관에서만 우는 규칙(그 기관의 내보내기를 의심)

파일에는 환자 단위 정보가 없으므로 이 도구도 그런 것을 만들지 않는다.
"""
import argparse
import csv
import glob
import io
import json
import os
import sys
from collections import defaultdict


def find_files(paths):
    out = []
    for p in paths:
        if os.path.isdir(p):
            out.extend(sorted(glob.glob(os.path.join(p, "**", "submission.json"), recursive=True)))
        elif os.path.isfile(p):
            out.append(p)
        else:
            print(f"없음: {p}", file=sys.stderr)
    return out


def site_of(path, names):
    """기관 이름: --name 으로 주었으면 그것, 아니면 submission.json 이 든 폴더 이름."""
    if path in names:
        return names[path]
    d = os.path.basename(os.path.dirname(os.path.abspath(path)))
    # 실행 폴더(runs/<실행 ID>/)에 든 것이면 그 위 폴더 이름을 쓴다
    return d


def load(paths, names):
    latest = {}   # (site, cohort) -> submission
    for p in paths:
        with io.open(p, encoding="utf-8") as fh:
            s = json.load(fh)
        if not str(s.get("schema", "")).startswith("kai-dq-submission/"):
            print(f"건너뜀 (submission 아님): {p}", file=sys.stderr)
            continue
        s["_site"] = site_of(p, names)
        s["_path"] = p
        key = (s["_site"], s.get("cohort"))
        if key not in latest or s.get("generated_at", "") > latest[key].get("generated_at", ""):
            latest[key] = s
    return list(latest.values())


def write_csv(path, header, rows):
    with io.open(path, "w", encoding="utf-8-sig", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(header)
        w.writerows(rows)


def main():
    ap = argparse.ArgumentParser(description="여러 기관의 submission.json 을 규칙별로 집계한다")
    ap.add_argument("paths", nargs="+", help="submission.json 파일 또는 그것이 든 폴더")
    ap.add_argument("--out", default="pilot/out", help="산출물 폴더")
    ap.add_argument("--name", action="append", default=[], metavar="경로=기관",
                    help="파일 경로에 기관 이름을 붙인다 (기본은 폴더 이름)")
    a = ap.parse_args()
    names = dict(n.split("=", 1) for n in a.name)
    subs = load(find_files(a.paths), names)
    if not subs:
        print("읽을 submission.json 이 없다", file=sys.stderr)
        sys.exit(2)
    os.makedirs(a.out, exist_ok=True)

    # ---- 기관 표
    sites = sorted({(s["_site"], s["cohort"]) for s in subs})
    site_rows = []
    for s in sorted(subs, key=lambda x: (x["_site"], x["cohort"])):
        norm = s.get("normalization", {}) or {}
        norm_total = sum(sum(v.values()) for v in norm.values())
        site_rows.append([s["_site"], s["cohort"], s.get("cohort_kor", ""), s.get("app_version", ""), s.get("run_id", ""),
                          s.get("run_date", ""), s.get("rows_total", 0),
                          s["rules"]["total"], s["rules"]["failed"], s["rules"]["skipped"], s["rules"]["error"],
                          s["violations"]["total"], s["violations"]["error"], s["violations"]["warning"],
                          norm_total, "; ".join(f"{t}:{','.join(f'{k}={v}' for k, v in r.items() if v)}" for t, r in norm.items())])
    write_csv(os.path.join(a.out, "sites.csv"),
              ["기관", "코호트", "코호트(한글)", "앱버전", "실행ID", "검증일", "행수", "규칙", "실패", "건너뜀", "오류", "위반", "위반(오류)", "위반(경고)", "정규화건수", "정규화내역"],
              site_rows)

    # ---- 규칙 × 기관
    rules = {}        # rule_id -> meta
    cell = defaultdict(dict)   # rule_id -> (site, cohort) -> (status, violations, rows)
    for s in subs:
        for r in s.get("by_rule", []):
            rules.setdefault(r["rule_id"], r)
            cell[r["rule_id"]][(s["_site"], s["cohort"])] = (r["status"], r.get("violations", 0), r.get("rows_checked", 0))
    site_labels = [f"{st}·{co}" for st, co in sites]

    def show(v):
        if v is None:
            return ""
        status, n, _ = v
        return {"pass": "0", "skipped": "-", "error": "!"}.get(status, str(n))

    by_site_rows = []
    summary_rows = []
    all_fail, one_fail = [], []
    for rid in sorted(rules):
        m = rules[rid]
        cells = cell[rid]
        ran = [k for k, v in cells.items() if v[0] in ("pass", "fail")]
        failed = [k for k, v in cells.items() if v[0] == "fail"]
        viol = sum(v[1] for v in cells.values() if v[0] == "fail")
        rows = sum(v[2] for v in cells.values() if v[0] in ("pass", "fail"))
        by_site_rows.append([rid, m.get("name", ""), m.get("category", ""), m.get("severity", ""), m.get("check", ""), m.get("table", "")]
                            + [show(cells.get(k)) for k in sites])
        summary_rows.append([rid, m.get("name", ""), m.get("category", ""), m.get("severity", ""), m.get("check", ""), m.get("table", ""),
                             len(ran), len(failed), viol, rows, f"{viol / rows * 100:.2f}" if rows else ""])
        if ran and len(failed) == len(ran) and len(ran) >= 2:
            all_fail.append((rid, m, len(ran), viol))
        elif len(failed) == 1 and len(ran) >= 2:
            one_fail.append((rid, m, failed[0], cells[failed[0]][1]))
    write_csv(os.path.join(a.out, "rules_by_site.csv"),
              ["규칙ID", "이름", "분류", "심각도", "검사", "테이블"] + site_labels, by_site_rows)
    write_csv(os.path.join(a.out, "rules_summary.csv"),
              ["규칙ID", "이름", "분류", "심각도", "검사", "테이블", "실행기관수", "실패기관수", "위반합계", "검사행합계", "위반율%"], summary_rows)

    # ---- 요약
    L = [f"# 파일럿 집계 — 기관·코호트 {len(sites)}개, 규칙 {len(rules)}개", ""]
    L += ["| 기관 | 코호트 | 검증일 | 행 | 규칙 | 실패 | 위반 | 정규화 |", "|---|---|---|---|---|---|---|---|"]
    for r in site_rows:
        L.append(f"| {r[0]} | {r[2]} | {r[5]} | {r[6]:,} | {r[7]} | {r[8]} | {r[11]:,} | {r[14]:,} |")
    L += ["", "## 실행한 모든 기관에서 우는 규칙 — 규칙이나 명세를 먼저 의심한다", ""]
    if all_fail:
        L += ["| 규칙 | 심각도 | 기관 수 | 위반 합계 |", "|---|---|---|---|"]
        for rid, m, n, v in sorted(all_fail, key=lambda x: -x[3]):
            L.append(f"| {rid} {m.get('name', '')} | {m.get('severity', '')} | {n} | {v:,} |")
    else:
        L.append("(없음)")
    L += ["", "## 한 기관에서만 우는 규칙 — 그 기관의 내보내기나 관행을 먼저 의심한다", ""]
    if one_fail:
        L += ["| 규칙 | 심각도 | 기관 | 위반 |", "|---|---|---|---|"]
        for rid, m, (st, co), v in sorted(one_fail, key=lambda x: -x[3])[:60]:
            L.append(f"| {rid} {m.get('name', '')} | {m.get('severity', '')} | {st}·{co} | {v:,} |")
        if len(one_fail) > 60:
            L.append(f"| … {len(one_fail) - 60}개 더 (rules_summary.csv) | | | |")
    else:
        L.append("(없음)")
    L += ["", "## 입력 정규화 (내보내기 흔적)", ""]
    norm_any = False
    for s in subs:
        for t, r in (s.get("normalization", {}) or {}).items():
            items = ", ".join(f"{k} {v:,}" for k, v in r.items() if v)
            if items:
                L.append(f"- {s['_site']}·{s['cohort']} {t}: {items}")
                norm_any = True
    if not norm_any:
        L.append("(없음)")
    L.append("")
    with io.open(os.path.join(a.out, "summary.md"), "w", encoding="utf-8") as fh:
        fh.write("\n".join(L))
    print(f"기관·코호트 {len(sites)}개, 규칙 {len(rules)}개 → {a.out}/ (sites.csv, rules_by_site.csv, rules_summary.csv, summary.md)")
    print(f"  모든 기관에서 우는 규칙 {len(all_fail)}개, 한 기관에서만 우는 규칙 {len(one_fail)}개")


if __name__ == "__main__":
    main()

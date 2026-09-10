import { useEffect, useMemo, useState } from "react";
import type { RuleInfo } from "@shared/types";
import { checkLabel, CATEGORY_LABELS, CHECK_GUIDES } from "@shared/labels";
import { api, fmt } from "../api";
import { Card, SeverityPill, Empty } from "../components/ui";

export function RulesPage() {
  const [rules, setRules] = useState<RuleInfo[]>([]);
  const [kind, setKind] = useState("");
  const [category, setCategory] = useState("");
  const [severity, setSeverity] = useState("");
  const [check, setCheck] = useState("");
  const [table, setTable] = useState("");
  const [q, setQ] = useState("");
  const [sel, setSel] = useState<RuleInfo | null>(null);
  const [err, setErr] = useState<string | null>(null);

  useEffect(() => { api.listRules().then(setRules).catch((e) => setErr(String(e))); }, []);

  const tables = useMemo(() => [...new Set(rules.flatMap((r) => r.table.split(",")))].filter(Boolean).sort(), [rules]);
  const checks = useMemo(() => [...new Set(rules.map((r) => r.check))].sort(), [rules]);
  const list = useMemo(() => rules.filter((r) =>
    (!kind || r.kind === kind) && (!category || r.category === category) && (!severity || r.severity === severity) &&
    (!check || r.check === check) && (!table || r.table.split(",").includes(table)) &&
    (!q || `${r.id} ${r.name} ${r.desc} ${r.fields}`.toLowerCase().includes(q.toLowerCase()))), [rules, kind, category, severity, check, table, q]);

  if (err) return <div className="callout err">{err}</div>;
  return (
    <>
      <div className="page-title"><h1>검증 규칙 관리</h1><span className="sub">구조 규칙 {fmt(rules.filter((r) => r.kind === "structural").length)}개 · 교차 규칙 {fmt(rules.filter((r) => r.kind === "semantic").length)}개</span></div>
      <div className="toolbar">
        <select value={kind} onChange={(e) => setKind(e.target.value)}><option value="">전체 종류</option><option value="structural">구조 (자동 생성)</option><option value="semantic">교차 테이블 (SQL)</option></select>
        <select value={category} onChange={(e) => setCategory(e.target.value)}><option value="">전체 분류</option>{Object.entries(CATEGORY_LABELS).map(([k, v]) => <option key={k} value={k}>{v} {k}</option>)}</select>
        <select value={severity} onChange={(e) => setSeverity(e.target.value)}><option value="">전체 심각도</option><option value="error">오류</option><option value="warning">경고</option></select>
        <select value={check} onChange={(e) => setCheck(e.target.value)}><option value="">전체 검사 유형</option>{checks.map((c) => <option key={c} value={c}>{checkLabel(c)}</option>)}</select>
        <select value={table} onChange={(e) => setTable(e.target.value)}><option value="">전체 테이블</option>{tables.map((t) => <option key={t} value={t}>{t}</option>)}</select>
        <input type="text" placeholder="규칙 ID · 이름 · 설명 검색" value={q} onChange={(e) => setQ(e.target.value)} style={{ minWidth: 220 }} />
        <span className="spacer" /><span style={{ color: "var(--muted)", fontSize: 12 }}>{fmt(list.length)}개 표시</span>
      </div>
      <div className="grid" style={{ gridTemplateColumns: sel ? "1.4fr 1fr" : "1fr" }}>
        <Card className="pad0">
          <div className="tblwrap" style={{ maxHeight: "72vh" }}>
            {list.length === 0 ? <Empty>조건에 맞는 규칙이 없습니다</Empty> : (
              <table className="tbl">
                <thead><tr><th>규칙 ID</th><th>규칙명</th><th>분류</th><th>검사 유형</th><th>심각도</th><th>대상 테이블</th><th>필드</th></tr></thead>
                <tbody>
                  {list.slice(0, 600).map((r) => (
                    <tr key={r.id} className={`click ${sel?.id === r.id ? "sel" : ""}`} onClick={() => setSel(r)}>
                      <td className="mono">{r.id}</td><td>{r.name}</td><td className="nw">{CATEGORY_LABELS[r.category] ?? r.category}</td><td className="nw">{checkLabel(r.check)}</td>
                      <td><SeverityPill s={r.severity} /></td><td className="mono ellipsis" style={{ maxWidth: 200 }}>{r.table}</td><td className="mono ellipsis" style={{ maxWidth: 160 }}>{r.fields}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            )}
          </div>
          {list.length > 600 && <div className="sub" style={{ padding: 8 }}>상위 600개만 표시합니다. 조건을 좁혀 주세요.</div>}
        </Card>
        {sel && (
          <Card title={<span className="mono">{sel.id}</span>} sub={sel.name} right={<button className="btn sm" onClick={() => setSel(null)}>닫기</button>}>
            <div className="kv">
              <span className="k">종류</span><span>{sel.kind === "structural" ? "구조 규칙 (명세에서 자동 생성)" : "교차 테이블 규칙 (DuckDB SQL)"}</span>
              <span className="k">분류</span><span>{CATEGORY_LABELS[sel.category] ?? sel.category} · {sel.subcategory}</span>
              <span className="k">검사 유형</span><span>{checkLabel(sel.check)}</span>
              <span className="k">심각도</span><span><SeverityPill s={sel.severity} /></span>
              <span className="k">대상 테이블</span><span className="mono">{sel.table}</span>
              {sel.fields && <><span className="k">필드</span><span className="mono">{sel.fields}</span></>}
              <span className="k">적용 코호트</span><span>{sel.scope === "all" ? "전체" : sel.scope}</span>
              <span className="k">설명</span><span>{sel.desc || "-"}</span>
              <span className="k">조치 안내</span><span>{CHECK_GUIDES[sel.check] ?? CHECK_GUIDES.sql}</span>
            </div>
            {sel.sql && <pre className="report" style={{ marginTop: 12 }}>{sel.sql}</pre>}
            <div className="sub" style={{ marginTop: 10 }}>규칙 편집은 저장소의 <span className="mono">rules/*.yaml</span> 에서 하며, 변경 후 앱을 다시 열면 반영됩니다.</div>
          </Card>
        )}
      </div>
    </>
  );
}

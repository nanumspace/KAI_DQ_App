import { useEffect, useMemo, useState } from "react";
import type { RunRecord, RunDetail, FindingRow } from "@shared/types";
import { checkLabel, CHECK_GUIDES } from "@shared/labels";
import { api, fmt, fmtTime } from "../api";
import { Card, SeverityPill, Empty } from "../components/ui";
import type { Nav } from "../App";

const PAGE = 100;

export function FindingsPage({ nav }: { nav: Nav }) {
  const [runs, setRuns] = useState<RunRecord[]>([]);
  const [runId, setRunId] = useState(nav.runId ?? "");
  const [detail, setDetail] = useState<RunDetail | null>(null);
  const [ruleId, setRuleId] = useState("");
  const [table, setTable] = useState("");
  const [severity, setSeverity] = useState("");
  const [search, setSearch] = useState("");
  const [page, setPage] = useState(0);
  const [rows, setRows] = useState<FindingRow[]>([]);
  const [total, setTotal] = useState(0);
  const [err, setErr] = useState<string | null>(null);

  useEffect(() => {
    api.listRuns().then((rs) => { setRuns(rs); if (!runId && rs.length) setRunId(rs[0].run_id); }).catch((e) => setErr(String(e)));
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);
  useEffect(() => { if (runId) api.getRun(runId).then(setDetail).catch((e) => setErr(String(e))); else setDetail(null); setPage(0); }, [runId]);
  useEffect(() => {
    if (!runId) return;
    api.getFindings({ runId, ruleId: ruleId || undefined, table: table || undefined, severity: severity || undefined, search: search || undefined, offset: page * PAGE, limit: PAGE })
      .then((p) => { setRows(p.rows); setTotal(p.total); }).catch((e) => setErr(String(e)));
  }, [runId, ruleId, table, severity, search, page]);

  const failed = useMemo(() => (detail?.rules ?? []).filter((r) => r.status === "fail"), [detail]);
  const tables = useMemo(() => [...new Set(failed.map((r) => r.table_name))].sort(), [failed]);
  const run = detail?.run;
  const pages = Math.max(1, Math.ceil(total / PAGE));

  if (err) return <div className="callout err">{err}</div>;
  if (!runs.length) return <><div className="page-title"><h1>오류 현황 조회</h1></div><Empty>실행 기록이 없습니다. 먼저 검증을 실행하세요.</Empty></>;

  return (
    <>
      <div className="page-title"><h1>오류 현황 조회</h1>
        {run && <span className="sub">{run.cohort_kor} · {run.label} · {fmtTime(run.created_at)} · 위반 {fmt(run.violations_total)}건</span>}
      </div>
      <div className="toolbar">
        <select value={runId} onChange={(e) => { setRunId(e.target.value); setRuleId(""); setTable(""); }} style={{ minWidth: 320 }}>
          {runs.map((r) => <option key={r.run_id} value={r.run_id}>{fmtTime(r.created_at)} · {r.cohort_kor} · {r.label} · 위반 {fmt(r.violations_total)}</option>)}
        </select>
        <select value={severity} onChange={(e) => { setSeverity(e.target.value); setPage(0); }}><option value="">전체 심각도</option><option value="error">오류</option><option value="warning">경고</option></select>
        <select value={table} onChange={(e) => { setTable(e.target.value); setPage(0); }}><option value="">전체 테이블</option>{tables.map((t) => <option key={t} value={t}>{t}</option>)}</select>
        <select value={ruleId} onChange={(e) => { setRuleId(e.target.value); setPage(0); }} style={{ maxWidth: 360 }}>
          <option value="">전체 규칙 ({failed.length}개 실패)</option>
          {failed.map((r) => <option key={r.rule_id} value={r.rule_id}>{r.rule_id} {r.name} ({fmt(r.violations)})</option>)}
        </select>
        <input type="text" placeholder="상세 · 환자 ID · 행 키 검색" value={search} onChange={(e) => { setSearch(e.target.value); setPage(0); }} />
        <span className="spacer" />
        <button className="btn" onClick={() => api.exportFile(runId, "findings")}>CSV 내보내기</button>
        <button className="btn" onClick={() => nav.go("report", runId)}>보고서</button>
      </div>
      <div className="grid" style={{ gridTemplateColumns: "300px 1fr" }}>
        <Card title="실패 규칙" sub={`${failed.length}개 규칙에서 위반 발생`} className="pad0" >
          <div className="tblwrap" style={{ maxHeight: "68vh" }}>
            {failed.length === 0 ? <Empty>위반 없음</Empty> : (
              <table className="tbl">
                <thead><tr><th>규칙</th><th className="num">위반</th></tr></thead>
                <tbody>
                  {failed.map((r) => (
                    <tr key={r.rule_id} className={`click ${ruleId === r.rule_id ? "sel" : ""}`} onClick={() => { setRuleId(ruleId === r.rule_id ? "" : r.rule_id); setPage(0); }}>
                      <td><div className="mono" style={{ fontSize: 11 }}>{r.rule_id} <SeverityPill s={r.severity} /></div><div>{r.name}</div><div style={{ color: "var(--muted)", fontSize: 11 }}>{checkLabel(r.check_type)} · {r.table_name}</div></td>
                      <td className="num">{fmt(r.violations)}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            )}
          </div>
        </Card>
        <div>
          {ruleId && (() => { const r = failed.find((x) => x.rule_id === ruleId); return r ? <div className="callout warn" style={{ marginBottom: 10 }}><b>{r.rule_id} {r.name}</b> · {CHECK_GUIDES[r.check_type] ?? CHECK_GUIDES.sql}</div> : null; })()}
          <Card className="pad0">
            <div className="tblwrap" style={{ maxHeight: "62vh" }}>
              {rows.length === 0 ? <Empty>조건에 맞는 위반 행이 없습니다</Empty> : (
                <table className="tbl">
                  <thead><tr><th>#</th><th>규칙</th><th>심각도</th><th>테이블</th><th>필드</th><th>행 키</th><th>환자 ID</th><th>상세</th></tr></thead>
                  <tbody>
                    {rows.map((f) => (
                      <tr key={f.seq}><td className="num">{f.seq}</td><td className="mono" title={f.rule_name}>{f.rule_id}</td><td><SeverityPill s={f.severity} /></td>
                        <td className="mono">{f.table_name}</td><td className="mono">{f.field}</td><td className="mono">{f.row_key}</td><td className="mono">{f.person_id}</td><td className="ellipsis" title={f.detail}>{f.detail}</td></tr>
                    ))}
                  </tbody>
                </table>
              )}
            </div>
            <div className="pager" style={{ padding: "8px 12px" }}>
              <span>총 {fmt(total)}건 · {page + 1}/{pages} 쪽</span>
              <button className="btn sm" disabled={page === 0} onClick={() => setPage(page - 1)}>이전</button>
              <button className="btn sm" disabled={page + 1 >= pages} onClick={() => setPage(page + 1)}>다음</button>
            </div>
          </Card>
        </div>
      </div>
    </>
  );
}

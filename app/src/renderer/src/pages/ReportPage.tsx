import { useEffect, useMemo, useState } from "react";
import type { RunRecord, RunDetail, RunOutputs } from "@shared/types";
import { CATEGORY_LABELS, checkLabel } from "@shared/labels";
import { api, fmt, pct, fmtTime } from "../api";
import { Card, Stat, SeverityPill, StatusPill, Empty } from "../components/ui";
import { OutputList } from "./RunPage";
import type { Nav } from "../App";

export function ReportPage({ nav }: { nav: Nav }) {
  const [runs, setRuns] = useState<RunRecord[]>([]);
  const [runId, setRunId] = useState(nav.runId ?? "");
  const [d, setD] = useState<RunDetail | null>(null);
  const [outputs, setOutputs] = useState<RunOutputs | null>(null);
  const [err, setErr] = useState<string | null>(null);

  useEffect(() => {
    api.listRuns().then((rs) => { setRuns(rs); if (!runId && rs.length) setRunId(rs[0].run_id); }).catch((e) => setErr(String(e)));
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);
  useEffect(() => {
    if (!runId) return;
    api.getRun(runId).then(setD).catch((e) => setErr(String(e)));
    api.getRunOutputs(runId).then(setOutputs).catch(() => setOutputs(null));
  }, [runId]);

  const byCat = useMemo(() => {
    const m = new Map<string, { rules: number; failed: number; violations: number }>();
    for (const r of d?.rules ?? []) { const b = m.get(r.category) ?? { rules: 0, failed: 0, violations: 0 }; b.rules++; if (r.status === "fail") b.failed++; b.violations += r.violations; m.set(r.category, b); }
    return ["Conformance", "Completeness", "Plausibility"].map((c) => ({ c, ...(m.get(c) ?? { rules: 0, failed: 0, violations: 0 }) }));
  }, [d]);
  const failed = useMemo(() => (d?.rules ?? []).filter((r) => r.status === "fail").sort((a, b) => b.violations - a.violations), [d]);
  const skipped = useMemo(() => (d?.rules ?? []).filter((r) => r.status !== "fail" && r.status !== "pass"), [d]);
  const run = d?.run;

  if (err) return <div className="callout err">{err}</div>;
  if (!runs.length) return <><div className="page-title"><h1>결과 보고서</h1></div><Empty>실행 기록이 없습니다. 먼저 검증을 실행하세요.</Empty></>;

  return (
    <>
      <div className="page-title"><h1>결과 보고서</h1>{run && <span className="sub">검증 실행일 {run.run_date} · 실행 시각 {fmtTime(run.created_at)}</span>}</div>
      <div className="toolbar">
        <select value={runId} onChange={(e) => setRunId(e.target.value)} style={{ minWidth: 360 }}>
          {runs.map((r) => <option key={r.run_id} value={r.run_id}>{fmtTime(r.created_at)} · {r.cohort_kor} · {r.label}</option>)}
        </select>
        <span className="spacer" />
        <button className="btn" onClick={() => nav.go("findings", runId)}>오류 현황 조회</button>
      </div>
      {run && (
        <>
          <div className="grid c4" style={{ marginBottom: 14 }}>
            <Stat k="코호트 · 실행 이름" v={run.cohort_kor} s={run.label} />
            <Stat k="검사 행 수" v={fmt(run.rows_total)} s={`테이블 ${Object.keys(run.tables).length}개`} />
            <Stat k="위반 건수" v={fmt(run.violations_total)} s={`오류 ${fmt(run.violations_error)} · 경고 ${fmt(run.violations_warning)}`} tone={run.violations_total ? "red" : "green"} />
            <Stat k="규칙" v={`${fmt(run.rules_failed)} / ${fmt(run.rules_total)}`} s={`실패 / 실행 · 건너뜀 ${run.rules_skipped} · 오류율 ${pct(run.rows_total ? (run.violations_total / run.rows_total) * 100 : 0)}`} />
          </div>
          {outputs && <div style={{ marginBottom: 14 }}><Card title="출력물" sub="이 실행이 만든 파일. 중앙에는 제출용 집계만 보냅니다."><OutputList outputs={outputs} runId={run.run_id} /></Card></div>}
          <div className="grid c21">
            <Card title="실패 규칙" sub={`${failed.length}개 · 위반 수 내림차순`} className="pad0">
              <div className="tblwrap" style={{ maxHeight: "48vh" }}>
                {failed.length === 0 ? <Empty>모든 규칙 통과</Empty> : (
                  <table className="tbl">
                    <thead><tr><th>규칙</th><th>분류</th><th>유형</th><th>심각도</th><th>테이블</th><th className="num">위반</th><th className="num">검사 행</th></tr></thead>
                    <tbody>{failed.map((r) => (
                      <tr key={r.rule_id}><td><span className="mono">{r.rule_id}</span> {r.name}</td><td className="nw">{CATEGORY_LABELS[r.category] ?? r.category}</td><td className="nw">{checkLabel(r.check_type)}</td>
                        <td><SeverityPill s={r.severity} /></td><td className="mono">{r.table_name}</td><td className="num">{fmt(r.violations)}</td><td className="num">{fmt(r.rows_checked)}</td></tr>
                    ))}</tbody>
                  </table>
                )}
              </div>
            </Card>
            <div className="grid" style={{ alignContent: "start" }}>
              <Card title="Kahn 분류별">
                <table className="tbl">
                  <thead><tr><th>분류</th><th className="num">규칙</th><th className="num">실패</th><th className="num">위반</th></tr></thead>
                  <tbody>{byCat.map((b) => <tr key={b.c}><td className="nw">{CATEGORY_LABELS[b.c]} <span style={{ color: "var(--muted)" }}>{b.c}</span></td><td className="num">{b.rules}</td><td className="num">{b.failed}</td><td className="num">{fmt(b.violations)}</td></tr>)}</tbody>
                </table>
              </Card>
              <Card title="입력 테이블 행 수">
                <table className="tbl"><tbody>{Object.entries(run.tables).map(([t, n]) => <tr key={t}><td className="mono">{t}</td><td className="num">{fmt(n)}</td></tr>)}</tbody></table>
              </Card>
              {skipped.length > 0 && (
                <Card title="건너뜀 · 실행 오류" sub={`${skipped.length}개`}>
                  <div className="tblwrap short"><table className="tbl"><tbody>{skipped.map((r) => <tr key={r.rule_id}><td className="mono">{r.rule_id}</td><td><StatusPill s={r.status} /></td><td style={{ color: "var(--muted)" }}>{r.note}</td></tr>)}</tbody></table></div>
                </Card>
              )}
            </div>
          </div>
          <div style={{ marginTop: 14 }}>
            <Card title="보고서 원문" sub="report.md">
              <pre className="report">{d?.report || "(보고서 파일 없음)"}</pre>
            </Card>
          </div>
        </>
      )}
    </>
  );
}

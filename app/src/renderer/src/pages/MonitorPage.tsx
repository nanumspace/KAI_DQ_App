import { useEffect, useMemo, useState } from "react";
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from "recharts";
import type { RunRecord } from "@shared/types";
import { severityInfo } from "@shared/labels";
import { api, fmt, pct, fmtTime } from "../api";
import { Card, Empty, RateDot } from "../components/ui";
import type { Nav } from "../App";

export function MonitorPage({ nav }: { nav: Nav }) {
  const [runs, setRuns] = useState<RunRecord[]>([]);
  const [cohort, setCohort] = useState("");
  const [err, setErr] = useState<string | null>(null);
  const load = () => api.listRuns().then(setRuns).catch((e) => setErr(String(e)));
  useEffect(() => { load(); }, []);

  const cohorts = useMemo(() => [...new Map(runs.map((r) => [r.cohort, r.cohort_kor])).entries()], [runs]);
  const list = useMemo(() => runs.filter((r) => !cohort || r.cohort === cohort), [runs, cohort]);
  const series = useMemo(() => list.slice().reverse().map((r, i) => ({
    x: `#${i + 1}`, time: fmtTime(r.created_at), label: `${r.cohort_kor} · ${r.label}`,
    error: r.violations_error, warning: r.violations_warning,
    rate: r.rows_total ? Number(((r.violations_total / r.rows_total) * 100).toFixed(3)) : 0,
  })), [list]);

  const del = async (r: RunRecord) => {
    if (!window.confirm(`실행 기록을 삭제할까요?\n${r.cohort_kor} · ${r.label} · ${fmtTime(r.created_at)}`)) return;
    await api.deleteRun(r.run_id); load();
  };

  if (err) return <div className="callout err">{err}</div>;
  return (
    <>
      <div className="page-title"><h1>통계 모니터링</h1><span className="sub">실행 이력 {fmt(runs.length)}회</span></div>
      <div className="toolbar">
        <select value={cohort} onChange={(e) => setCohort(e.target.value)}><option value="">전체 코호트</option>{cohorts.map(([id, kor]) => <option key={id} value={id}>{kor}</option>)}</select>
      </div>
      <div className="grid c2" style={{ marginBottom: 14 }}>
        <Card title="위반 건수 추이" sub="실행 순서대로 · 오류(High) / 경고(Medium)">
          <div style={{ height: 240 }}>
            {series.length ? (
              <ResponsiveContainer>
                <LineChart data={series} margin={{ top: 8, right: 12, left: -10, bottom: 0 }}>
                  <CartesianGrid stroke="#eef1f5" /><XAxis dataKey="x" tick={{ fontSize: 10 }} /><YAxis tick={{ fontSize: 10 }} />
                  <Tooltip labelFormatter={(_, p) => `${p?.[0]?.payload?.time ?? ""} · ${p?.[0]?.payload?.label ?? ""}`} /><Legend wrapperStyle={{ fontSize: 11 }} />
                  <Line type="monotone" dataKey="error" name="오류(High)" stroke={severityInfo("error").color} />
                  <Line type="monotone" dataKey="warning" name="경고(Medium)" stroke={severityInfo("warning").color} />
                </LineChart>
              </ResponsiveContainer>
            ) : <Empty>실행 기록 없음</Empty>}
          </div>
        </Card>
        <Card title="오류율 추이 (%)" sub="위반 건수 ÷ 검사 행 수">
          <div style={{ height: 240 }}>
            {series.length ? (
              <ResponsiveContainer>
                <LineChart data={series} margin={{ top: 8, right: 12, left: -10, bottom: 0 }}>
                  <CartesianGrid stroke="#eef1f5" /><XAxis dataKey="x" tick={{ fontSize: 10 }} /><YAxis tick={{ fontSize: 10 }} unit="%" />
                  <Tooltip formatter={(v) => pct(Number(v))} labelFormatter={(_, p) => `${p?.[0]?.payload?.time ?? ""} · ${p?.[0]?.payload?.label ?? ""}`} />
                  <Line type="monotone" dataKey="rate" name="오류율" stroke="#3b6fd6" />
                </LineChart>
              </ResponsiveContainer>
            ) : <Empty>실행 기록 없음</Empty>}
          </div>
        </Card>
      </div>
      <Card title="실행 이력" className="pad0">
        <div className="tblwrap" style={{ maxHeight: "50vh" }}>
          {list.length === 0 ? <Empty>실행 기록 없음</Empty> : (
            <table className="tbl">
              <thead><tr><th>실행 시각</th><th>코호트</th><th>실행 이름</th><th>실행일</th><th className="num">검사 행</th><th className="num">규칙</th><th className="num">실패 규칙</th><th className="num">위반</th><th className="num">오류율</th><th>상태</th><th></th></tr></thead>
              <tbody>{list.map((r) => {
                const rate = r.rows_total ? (r.violations_total / r.rows_total) * 100 : 0;
                return (
                  <tr key={r.run_id}>
                    <td>{fmtTime(r.created_at)}</td><td>{r.cohort_kor}</td><td>{r.label}</td><td>{r.run_date}</td>
                    <td className="num">{fmt(r.rows_total)}</td><td className="num">{fmt(r.rules_total)}</td><td className="num">{fmt(r.rules_failed)}</td>
                    <td className="num">{fmt(r.violations_total)}</td><td className="num">{pct(rate)}</td><td><RateDot pct={rate} /></td>
                    <td style={{ whiteSpace: "nowrap" }}>
                      <button className="btn sm" onClick={() => nav.go("findings", r.run_id)}>오류</button>{" "}
                      <button className="btn sm" onClick={() => nav.go("report", r.run_id)}>보고서</button>{" "}
                      <button className="btn sm danger" onClick={() => del(r)}>삭제</button>
                    </td>
                  </tr>
                );
              })}</tbody>
            </table>
          )}
        </div>
      </Card>
    </>
  );
}

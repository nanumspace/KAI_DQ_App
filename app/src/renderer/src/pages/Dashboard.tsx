import { useEffect, useMemo, useState } from "react";
import { PieChart, Pie, Cell, Tooltip, ResponsiveContainer, LineChart, Line, XAxis, YAxis, CartesianGrid, Legend, BarChart, Bar } from "recharts";
import type { Dashboard as DashboardData, RuleInfo } from "@shared/types";
import { SEVERITIES, rateStatus, severityInfo, checkLabel } from "@shared/labels";
import { api, fmt, pct, fmtTime } from "../api";
import { Card, Stat, Empty, RateDot } from "../components/ui";
import type { Nav } from "../App";

const PALETTE = ["#2563eb", "#38bdf8", "#22c55e", "#f59e0b", "#ef4444", "#8b5cf6", "#14b8a6", "#f97316", "#64748b", "#a3e635"];

export function Dashboard({ nav }: { nav: Nav }) {
  const [d, setD] = useState<DashboardData | null>(null);
  const [rules, setRules] = useState<RuleInfo[]>([]);
  const [err, setErr] = useState<string | null>(null);

  useEffect(() => {
    api.getDashboard().then(setD).catch((e) => setErr(String(e)));
    api.listRules().then(setRules).catch(() => {});
  }, []);

  const totalViolations = useMemo(() => d?.byCheck.reduce((a, b) => a + b.count, 0) ?? 0, [d]);
  const severityRows = useMemo(() => {
    const m = new Map(d?.bySeverity.map((s) => [s.severity, s.count]) ?? []);
    return SEVERITIES.map((s) => ({ ...s, count: m.get(s.key) ?? 0 }));
  }, [d]);
  const trend = useMemo(() => (d?.trend ?? []).map((t, i) => ({ ...t, x: `${t.cohort.slice(0, 4)}#${i + 1}`, time: fmtTime(t.created_at) })), [d]);
  const latestRun = d?.latestByCohort.slice().sort((a, b) => b.created_at.localeCompare(a.created_at))[0];

  if (err) return <div className="callout err">{err}</div>;
  if (!d) return <Empty>불러오는 중…</Empty>;

  return (
    <>
      <div className="page-title">
        <h1>대시보드</h1>
        <span className="sub">코호트별 최신 실행 기준 · 실행 {d.totals.runs}회 누적</span>
      </div>

      {d.latestByCohort.length === 0 && (
        <div className="callout warn" style={{ marginBottom: 14 }}>
          아직 검증 실행 기록이 없습니다. <a href="#" onClick={(e) => { e.preventDefault(); nav.go("run"); }}>검증 실행</a>에서 코호트 CSV 디렉터리를 선택해 실행하면 이 화면이 채워집니다.
        </div>
      )}

      <div className="grid c4">
        {/* ① 오류 유형별 통계 */}
        <Card num={1} title="오류 유형별 통계" sub="오류 유형별 건수 및 비율">
          {d.byCheck.length === 0 ? <Empty>오류 없음</Empty> : (
            <div style={{ display: "grid", gridTemplateColumns: "130px minmax(0, 1fr)", gap: 6, alignItems: "center" }}>
              <div style={{ height: 150, position: "relative" }}>
                <ResponsiveContainer>
                  <PieChart>
                    <Pie data={d.byCheck} dataKey="count" nameKey="label" innerRadius={42} outerRadius={70} paddingAngle={1} stroke="none">
                      {d.byCheck.map((_, i) => <Cell key={i} fill={PALETTE[i % PALETTE.length]} />)}
                    </Pie>
                    <Tooltip formatter={(v) => fmt(Number(v))} />
                  </PieChart>
                </ResponsiveContainer>
                <div style={{ position: "absolute", inset: 0, display: "grid", placeItems: "center", pointerEvents: "none", textAlign: "center", fontSize: 11, color: "var(--muted)" }}>
                  <div>총 오류 건수<br /><b style={{ fontSize: 15, color: "var(--navy)" }}>{fmt(totalViolations)}</b></div>
                </div>
              </div>
              <div className="legend">
                {d.byCheck.slice(0, 7).map((c, i) => (
                  <div key={c.check}><span className="sw" style={{ background: PALETTE[i % PALETTE.length] }} />
                    <span style={{ flex: 1, overflow: "hidden", textOverflow: "ellipsis" }}>{c.label}</span>
                    <span style={{ color: "var(--ink-2)" }} title={`${fmt(c.count)}건`}>{totalViolations ? ((c.count / totalViolations) * 100).toFixed(1) : "0.0"}%</span></div>
                ))}
              </div>
            </div>
          )}
          <div className="sub" style={{ marginTop: 10, fontWeight: 600, color: "var(--navy)" }}>심각도별 통계</div>
          <table className="tbl">
            <thead><tr><th>심각도</th><th className="num">건수</th><th className="num">비율</th></tr></thead>
            <tbody>
              {severityRows.map((s) => (
                <tr key={s.key}><td className="nw" style={{ color: s.color, fontWeight: 600 }}>{s.label}</td><td className="num">{fmt(s.count)}</td>
                  <td className="num" style={{ color: s.color }}>{totalViolations ? ((s.count / totalViolations) * 100).toFixed(1) : "0.0"}%</td></tr>
              ))}
              <tr className="total"><td>합계</td><td className="num">{fmt(totalViolations)}</td><td className="num">100%</td></tr>
            </tbody>
          </table>
        </Card>

        {/* ② 질환별 검증 결과 */}
        <Card num={2} title="질환별 검증 결과" sub="질환별 발생 오류 현황 요약 (최신 실행)">
          {d.latestByCohort.length === 0 ? <Empty>실행 기록 없음</Empty> : (
            <table className="tbl">
              <thead><tr><th>질환명</th><th className="num">데이터 건수</th><th className="num">오류 건수</th><th className="num">오류율(%)</th><th>상태</th></tr></thead>
              <tbody>
                {d.latestByCohort.map((r) => (
                  <tr key={r.run_id} className="click" onClick={() => nav.go("findings", r.run_id)} title={`${r.label} · ${fmtTime(r.created_at)}`}>
                    <td className="nw">{r.cohort_kor}</td><td className="num">{fmt(r.rows_total)}</td><td className="num">{fmt(r.violations_total)}</td>
                    <td className="num">{pct(r.error_rate)}</td><td><RateDot pct={r.error_rate} /></td>
                  </tr>
                ))}
                <tr className="total"><td>합계</td><td className="num">{fmt(d.totals.rows)}</td><td className="num">{fmt(d.totals.violations)}</td>
                  <td className="num">{pct(d.totals.error_rate)}</td><td><RateDot pct={d.totals.error_rate} /></td></tr>
              </tbody>
            </table>
          )}
          <div className="sub" style={{ marginTop: 12 }}>오류율 기준</div>
          <div style={{ display: "flex", gap: 14, fontSize: 12 }}>
            {[["우수 (<1%)", 0.5], ["양호 (1~2%)", 1.5], ["주의 (2~5%)", 3], ["위험 (≥5%)", 6]].map(([l, v]) => (
              <span key={String(l)}><span className="dot" style={{ background: rateStatus(Number(v)).color, marginRight: 5 }} />{l}</span>
            ))}
          </div>
        </Card>

        {/* ③ 적용 검증 규칙 */}
        <Card num={3} title="적용 검증 규칙" sub={`구조 규칙 ${fmt(d.rulesCount.structural)}개 · 교차 규칙 ${fmt(d.rulesCount.semantic)}개`}
          right={<button className="btn sm" onClick={() => nav.go("rules")}>전체 보기</button>}>
          <div className="tblwrap short">
            <table className="tbl">
              <thead><tr><th>규칙 ID</th><th>규칙명</th><th>규칙 유형</th></tr></thead>
              <tbody>
                {rules.filter((r) => !["table_present", "columns"].includes(r.check)).slice(0, 8).map((r) => (
                  <tr key={r.id}><td className="mono">{r.id}</td><td className="ellipsis" style={{ maxWidth: 120 }} title={`${r.name} · ${r.table}`}>{r.name}</td><td style={{ fontSize: 12 }}>{checkLabel(r.check)}</td></tr>
                ))}
              </tbody>
            </table>
          </div>
          <div className="sub" style={{ marginTop: 10, fontWeight: 600, color: "var(--navy)" }}>규칙 유형 설명</div>
          <ul style={{ margin: 0, paddingLeft: 18, fontSize: 12, lineHeight: 1.7, color: "var(--ink-2)" }}>
            <li><b>필수값</b>: 필수 항목의 존재 여부 확인</li>
            <li><b>코드 검증</b>: 코드표·OMOP 허용집합 적용 여부</li>
            <li><b>값 범위</b>: 허용 범위 내 값인지 검증</li>
            <li><b>타입 검증</b>: 날짜·숫자 형식 일치 여부</li>
            <li><b>논리 검증</b>: 이벤트 간 논리 및 시간 순서 (교차 테이블 SQL)</li>
          </ul>
        </Card>

        {/* ④ 후속 조치 내용 */}
        <Card num={4} title="후속 조치 내용" sub="오류 유형별 조치 내용 및 가이드">
          <table className="tbl">
            <thead><tr><th>오류 구분</th><th>주요 조치 가이드</th></tr></thead>
            <tbody>
              {SEVERITIES.map((s) => (
                <tr key={s.key}><td style={{ color: s.color, fontWeight: 600, whiteSpace: "nowrap" }}>{s.label}</td><td>{s.guide}</td></tr>
              ))}
            </tbody>
          </table>
          <div className="sub" style={{ marginTop: 12, fontWeight: 600, color: "var(--navy)" }}>검증 후속 절차</div>
          <div className="steps">
            {["오류 검토", "원인 분석", "데이터 수정", "재검증 수행", "검증 완료"].map((s, i, a) => (
              <span key={s} style={{ display: "contents" }}>
                <div className="st"><b>{["⌕", "▦", "✎", "↻", "✓"][i]}</b>{s}</div>
                {i < a.length - 1 && <span className="arrow">→</span>}
              </span>
            ))}
          </div>
        </Card>
      </div>

      {/* ⑤ 검증 결과 모니터링 */}
      <div style={{ marginTop: 14 }}>
        <Card num={5} title="검증 결과 모니터링" sub="실행 이력에 따른 오류 추이">
          <div className="grid" style={{ gridTemplateColumns: "1fr 1fr 1.1fr" }}>
            <div>
              <div className="sub" style={{ fontWeight: 600, color: "var(--navy)" }}>실행별 오류 건수 추이</div>
              <div style={{ height: 210 }}>
                {trend.length ? (
                  <ResponsiveContainer>
                    <LineChart data={trend} margin={{ top: 8, right: 12, left: -10, bottom: 0 }}>
                      <CartesianGrid stroke="#eef1f5" />
                      <XAxis dataKey="x" tick={{ fontSize: 10 }} /><YAxis tick={{ fontSize: 10 }} />
                      <Tooltip labelFormatter={(_, p) => (p?.[0]?.payload?.time ?? "") + " · " + (p?.[0]?.payload?.label ?? "")} />
                      <Legend wrapperStyle={{ fontSize: 11 }} />
                      <Line type="monotone" dataKey="violations_error" name="오류(High)" stroke={severityInfo("error").color} dot={{ r: 2 }} />
                      <Line type="monotone" dataKey="violations_warning" name="경고(Medium)" stroke={severityInfo("warning").color} dot={{ r: 2 }} />
                    </LineChart>
                  </ResponsiveContainer>
                ) : <Empty>실행 기록 없음</Empty>}
              </div>
            </div>
            <div>
              <div className="sub" style={{ fontWeight: 600, color: "var(--navy)" }}>오류율 추이 (%)</div>
              <div style={{ height: 210 }}>
                {trend.length ? (
                  <ResponsiveContainer>
                    <BarChart data={trend} margin={{ top: 8, right: 12, left: -10, bottom: 0 }}>
                      <CartesianGrid stroke="#eef1f5" vertical={false} />
                      <XAxis dataKey="x" tick={{ fontSize: 10 }} /><YAxis tick={{ fontSize: 10 }} unit="%" />
                      <Tooltip formatter={(v) => pct(Number(v))} labelFormatter={(_, p) => (p?.[0]?.payload?.time ?? "")} />
                      <Bar dataKey="error_rate" name="오류율" fill="#3b6fd6" radius={[3, 3, 0, 0]} />
                    </BarChart>
                  </ResponsiveContainer>
                ) : <Empty>실행 기록 없음</Empty>}
              </div>
            </div>
            <div>
              <div className="sub" style={{ fontWeight: 600, color: "var(--navy)" }}>검증 상태 요약</div>
              <div className="grid c3" style={{ gap: 8 }}>
                <Stat k="총 검증 데이터 건수" v={fmt(d.totals.rows)} s="건" />
                <Stat k="전체 오류 건수" v={fmt(d.totals.violations)} s="건" tone="red" />
                <Stat k="전체 오류율" v={pct(d.totals.error_rate)} tone={d.totals.error_rate < 2 ? "green" : "orange"} />
              </div>
              <div style={{ display: "flex", gap: 10, marginTop: 10, alignItems: "stretch" }}>
                <div className={`callout ${latestRun ? "" : "warn"}`} style={{ flex: 1 }}>
                  {latestRun ? <>✓ 최근 검증 완료: {latestRun.cohort_kor} · {latestRun.label} · {fmtTime(latestRun.created_at)}</> : "검증 실행 기록이 없습니다."}
                </div>
                <button className="btn primary" disabled={!latestRun} onClick={() => latestRun && nav.go("report", latestRun.run_id)}>상세 보고서</button>
              </div>
            </div>
          </div>
        </Card>
      </div>
    </>
  );
}

// 검증 실행: ① 코호트와 파일 → ② 테이블 대응과 사전 점검 → ③ 실행 → ④ 결과와 출력물
import { useEffect, useMemo, useRef, useState, type DragEvent } from "react";
import type { CohortInfo, InputPlan, PreviewData, RunProgress, RunRecord, RunOutputs, SourceCandidate, TableCheck, TemplateKind } from "@shared/types";
import { api, fmt, pct } from "../api";
import { Card, Stat, Empty } from "../components/ui";
import type { Nav } from "../App";

function bytes(n: number): string { return n < 1024 * 1024 ? `${(n / 1024).toFixed(0)} KB` : `${(n / 1024 / 1024).toFixed(1)} MB`; }

const LEVEL: Record<string, { cls: string; label: string }> = { error: { cls: "error", label: "오류" }, warn: { cls: "warning", label: "주의" }, info: { cls: "gray", label: "참고" } };

export function RunPage({ nav }: { nav: Nav }) {
  const [cohorts, setCohorts] = useState<CohortInfo[]>([]);
  const [cohort, setCohort] = useState("");
  const [plan, setPlan] = useState<InputPlan | null>(null);
  const [busy, setBusy] = useState<string | null>(null); // "inspect" | "run" | "template"
  const [today, setToday] = useState("");
  const [label, setLabel] = useState("");
  const [progress, setProgress] = useState<RunProgress | null>(null);
  const [result, setResult] = useState<RunRecord | null>(null);
  const [outputs, setOutputs] = useState<RunOutputs | null>(null);
  const [preview, setPreview] = useState<{ c: SourceCandidate; data: PreviewData } | null>(null);
  const [msg, setMsg] = useState<string | null>(null);
  const [err, setErr] = useState<string | null>(null);
  const [drag, setDrag] = useState(false);
  const resultRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    api.listCohorts().then((cs) => { setCohorts(cs); if (cs.length) setCohort((c) => c || cs[0].id); }).catch((e) => setErr(String(e)));
    api.getConfig().then((c) => setToday(c.defaultToday ?? new Date().toISOString().slice(0, 10)));
    const off1 = api.onProgress((p) => setProgress(p));
    const off2 = api.onSmokePlan((p) => { setCohort(p.cohort); setPlan(p); });
    return () => { off1(); off2(); };
  }, []);

  const info = cohorts.find((c) => c.id === cohort);

  // ---------------------------------------------------------------- ① 파일
  const addPaths = async (paths: string[]) => {
    if (!paths.length || !cohort) return;
    setErr(null); setResult(null); setOutputs(null); setBusy("inspect");
    try { setPlan(await api.inspectInput(cohort, paths, plan?.cohort === cohort ? plan.candidates : [])); }
    catch (e) { setErr(String((e as Error).message ?? e)); }
    finally { setBusy(null); }
  };
  const onDrop = (e: DragEvent) => { e.preventDefault(); setDrag(false); void addPaths(api.pathsForFiles([...e.dataTransfer.files])); };
  const removeCandidate = async (id: string) => {
    if (!plan) return;
    const candidates = plan.candidates.filter((c) => c.id !== id);
    const mapping = Object.fromEntries(Object.entries(plan.mapping).filter(([, v]) => v !== id));
    setPlan(await api.checkInput(cohort, candidates, mapping));
  };
  const changeCohort = (id: string) => { setCohort(id); setPlan(null); setResult(null); setOutputs(null); setErr(null); };
  const template = async (kind: TemplateKind) => {
    setBusy("template"); setMsg(null);
    try { const p = await api.exportTemplate(cohort, kind); if (p) setMsg(`저장됨: ${p}`); }
    catch (e) { setErr(String((e as Error).message ?? e)); }
    finally { setBusy(null); }
  };

  // ---------------------------------------------------------------- ② 대응표
  const remap = async (table: string, cid: string) => {
    if (!plan) return;
    const mapping = { ...plan.mapping };
    if (cid) { for (const [t, v] of Object.entries(mapping)) if (v === cid && t !== table) delete mapping[t]; mapping[table] = cid; }
    else delete mapping[table];
    setPlan(await api.checkInput(cohort, plan.candidates, mapping));
  };
  const showPreview = async (c: SourceCandidate) => {
    try { setPreview({ c, data: await api.previewSource(c) }); } catch (e) { setErr(String((e as Error).message ?? e)); }
  };
  const unmapped = useMemo(() => plan ? plan.candidates.filter((c) => !Object.values(plan.mapping).includes(c.id)) : [], [plan]);

  // ---------------------------------------------------------------- ③ 실행
  const run = async () => {
    if (!plan) return;
    setErr(null); setResult(null); setOutputs(null); setProgress(null); setBusy("run");
    try {
      const rec = await api.runValidation({ cohort, candidates: plan.candidates, mapping: plan.mapping, today: today || undefined, label: label || undefined });
      setResult(rec); setOutputs(await api.getRunOutputs(rec.run_id));
      setTimeout(() => resultRef.current?.scrollIntoView({ behavior: "smooth" }), 50);
    } catch (e) { setErr(String((e as Error).message ?? e)); }
    finally { setBusy(null); }
  };

  const stepDone = { files: !!plan && plan.candidates.length > 0, check: !!plan?.ok, run: !!result };

  return (
    <>
      <div className="page-title"><h1>검증 실행</h1><span className="sub">입력: 코호트 테이블 CSV 또는 엑셀 → 출력: 보고서 · 위반 행 · 규칙별 결과 · 제출용 집계</span></div>
      <div className="stepbar">
        {[["1", "코호트와 파일", stepDone.files], ["2", "테이블 대응 · 사전 점검", stepDone.check], ["3", "검증 실행", stepDone.run], ["4", "결과와 출력물", stepDone.run]].map(([n, t, done]) => (
          <div key={String(n)} className={`step ${done ? "done" : ""}`}><b>{n}</b>{t}</div>
        ))}
      </div>
      {err && <div className="callout err" style={{ marginBottom: 12 }}>{err}</div>}
      {msg && <div className="callout" style={{ marginBottom: 12 }}>{msg}</div>}

      {/* ① */}
      <Card num={1} title="코호트와 입력 파일" sub="파일 하나가 테이블 하나입니다. CSV 여러 개, 또는 시트당 테이블 하나인 엑셀 파일 하나를 넣습니다.">
        <div className="grid" style={{ gridTemplateColumns: "280px 1fr 300px", gap: 16 }}>
          <div className="form">
            <label>코호트
              <select value={cohort} onChange={(e) => changeCohort(e.target.value)} disabled={busy === "run"}>
                {cohorts.map((c) => <option key={c.id} value={c.id}>{c.kor} ({c.id})</option>)}
              </select>
            </label>
            {info && <div style={{ fontSize: 12, color: "var(--muted)", lineHeight: 1.6 }}>필요 테이블 {info.tables.length}개<br />{info.tables.join(" · ")}</div>}
          </div>
          <div className={`dropzone ${drag ? "drag" : ""}`} onDragOver={(e) => { e.preventDefault(); setDrag(true); }} onDragLeave={() => setDrag(false)} onDrop={onDrop}>
            <div style={{ fontSize: 15, fontWeight: 600, color: "var(--navy)" }}>여기에 파일이나 폴더를 끌어다 놓으세요</div>
            <div style={{ color: "var(--muted)", fontSize: 12.5, margin: "6px 0 12px" }}>CSV(UTF-8 또는 EUC-KR) · 엑셀(.xlsx) · 테이블별 파일이 든 폴더</div>
            <div style={{ display: "flex", gap: 8, justifyContent: "center" }}>
              <button className="btn primary" disabled={!!busy} onClick={async () => addPaths(await api.chooseFiles())}>파일 선택</button>
              <button className="btn" disabled={!!busy} onClick={async () => { const d = await api.chooseDirectory("테이블 파일이 든 폴더 선택"); if (d) addPaths([d]); }}>폴더 선택</button>
            </div>
            {busy === "inspect" && <div style={{ marginTop: 10, fontSize: 12 }}>파일을 읽는 중…</div>}
          </div>
          <div>
            <div className="sub" style={{ fontWeight: 600, color: "var(--navy)" }}>입력 양식 내려받기</div>
            <div style={{ display: "grid", gap: 6 }}>
              <button className="btn sm" disabled={!!busy} onClick={() => template("xlsx")}>엑셀 양식 (시트당 테이블, 명세 포함)</button>
              <button className="btn sm" disabled={!!busy} onClick={() => template("csv")}>CSV 양식 묶음 (헤더만)</button>
              <button className="btn sm" disabled={!!busy} onClick={() => template("spec")}>컬럼 명세서 (xlsx)</button>
              <button className="btn sm" disabled={!!busy} onClick={() => template("sample")}>견본 데이터 (100명 가상 코호트)</button>
            </div>
            <div style={{ fontSize: 11.5, color: "var(--muted)", marginTop: 8, lineHeight: 1.5 }}>병원은 이 양식대로 내보내면 됩니다. 파일명과 컬럼명은 그대로 두고, 날짜는 YYYY-MM-DD, 빈 값은 빈 칸입니다.</div>
          </div>
        </div>
        {plan && plan.candidates.length > 0 && (
          <div style={{ marginTop: 14 }}>
            <div className="sub" style={{ fontWeight: 600, color: "var(--navy)" }}>넣은 파일 {plan.candidates.length}개</div>
            <div className="tblwrap short">
              <table className="tbl">
                <thead><tr><th>파일 / 시트</th><th>종류</th><th>인코딩</th><th className="num">행</th><th className="num">컬럼</th><th className="num">크기</th><th>대응 테이블</th><th></th></tr></thead>
                <tbody>{plan.candidates.map((c) => {
                  const t = Object.entries(plan.mapping).find(([, v]) => v === c.id)?.[0];
                  return (
                    <tr key={c.id}>
                      <td className="ellipsis" title={c.path}>{c.name}</td><td>{c.kind === "xlsx" ? "엑셀 시트" : "CSV"}</td>
                      <td>{c.error ? <span className="pill error">읽기 실패</span> : c.encoding}</td>
                      <td className="num">{c.error ? "-" : fmt(c.rows)}</td><td className="num">{c.columns.length || "-"}</td><td className="num">{bytes(c.sizeBytes)}</td>
                      <td>{t ? <span className="mono">{t}</span> : <span className="pill warning">대응 없음</span>}</td>
                      <td style={{ whiteSpace: "nowrap" }}><button className="btn sm" disabled={!!c.error} onClick={() => showPreview(c)}>미리보기</button> <button className="btn sm danger" onClick={() => removeCandidate(c.id)}>제거</button></td>
                    </tr>
                  );
                })}</tbody>
              </table>
            </div>
          </div>
        )}
      </Card>

      {/* ② */}
      {plan && plan.candidates.length > 0 && (
        <div style={{ marginTop: 14 }}>
          <Card num={2} title="테이블 대응과 사전 점검" sub="테이블마다 어느 파일을 쓸지 확인합니다. 자동 대응이 틀렸으면 직접 고르세요."
            right={<span className={`pill ${plan.ok ? "pass" : "fail"}`}>{plan.ok ? (plan.warnings ? `실행 가능 · 주의 ${plan.warnings}` : "실행 가능") : `오류 ${plan.errors} · 실행 불가`}</span>}>
            <table className="tbl">
              <thead><tr><th>테이블</th><th>파일 / 시트</th><th className="num">행</th><th>점검 결과</th></tr></thead>
              <tbody>{plan.tables.map((t: TableCheck) => (
                <tr key={t.table}>
                  <td style={{ whiteSpace: "nowrap" }}><span className="mono">{t.table}</span><div style={{ color: "var(--muted)", fontSize: 11 }}>{t.kor}{t.required ? " · 필수" : ""}</div></td>
                  <td style={{ minWidth: 260 }}>
                    <select value={t.candidateId ?? ""} onChange={(e) => remap(t.table, e.target.value)} disabled={busy === "run"} style={{ padding: "5px 8px" }}>
                      <option value="">(없음)</option>
                      {plan.candidates.filter((c) => !c.error).map((c) => <option key={c.id} value={c.id}>{c.name}</option>)}
                    </select>
                    {t.candidateId && !t.auto && <span style={{ fontSize: 11, color: "var(--muted)", marginLeft: 6 }}>직접 지정</span>}
                  </td>
                  <td className="num">{t.rows === null ? "-" : fmt(t.rows)}</td>
                  <td>
                    {t.issues.length === 0 ? <span className="pill pass">이상 없음</span> : t.issues.map((i, k) => (
                      <div key={k} style={{ marginBottom: 2 }}><span className={`pill ${LEVEL[i.level].cls}`}>{LEVEL[i.level].label}</span> <span style={{ fontSize: 12.5 }}>{i.text}</span></div>
                    ))}
                  </td>
                </tr>
              ))}</tbody>
            </table>
            {unmapped.length > 0 && <div className="callout warn" style={{ marginTop: 10 }}>대응되지 않은 파일 {unmapped.length}개: {unmapped.map((c) => c.name).join(", ")} · 필요하면 위 표에서 테이블에 지정하세요.</div>}
          </Card>
        </div>
      )}

      {/* ③ */}
      {plan && plan.candidates.length > 0 && (
        <div style={{ marginTop: 14 }}>
          <Card num={3} title="검증 실행">
            <div className="grid" style={{ gridTemplateColumns: "200px 260px 1fr", gap: 12, alignItems: "end" }}>
              <label className="lbl">검증 실행일 <span style={{ color: "var(--muted)" }}>· 미래 날짜 판정 기준</span><input type="date" value={today} onChange={(e) => setToday(e.target.value)} disabled={busy === "run"} /></label>
              <label className="lbl">실행 이름 <span style={{ color: "var(--muted)" }}>· 비우면 폴더 이름</span><input type="text" value={label} onChange={(e) => setLabel(e.target.value)} placeholder="예: 2026-09 제출본" disabled={busy === "run"} /></label>
              <div><button className="btn primary" onClick={run} disabled={!plan.ok || busy === "run"} style={{ padding: "9px 22px" }}>{busy === "run" ? "검증 중…" : "검증 실행"}</button>
                {!plan.ok && <span style={{ marginLeft: 10, color: "var(--red)", fontSize: 12.5 }}>사전 점검 오류를 먼저 해결하세요.</span>}</div>
            </div>
            {(busy === "run" || (progress && !result)) && (
              <div style={{ marginTop: 14 }}>
                <div style={{ display: "flex", justifyContent: "space-between", fontSize: 12, color: "var(--ink-2)", marginBottom: 4 }}><span>{progress?.text ?? "준비 중"}</span><span>{progress?.pct ?? 0}%</span></div>
                <div className="progress"><div style={{ width: `${progress?.pct ?? 0}%` }} /></div>
              </div>
            )}
          </Card>
        </div>
      )}

      {/* ④ */}
      {result && outputs && (
        <div style={{ marginTop: 14 }} ref={resultRef}>
          <Card num={4} title="결과와 출력물" sub={`${result.cohort_kor} · ${result.label} · 실행일 ${result.run_date}`}
            right={<div style={{ display: "flex", gap: 6 }}><button className="btn primary" onClick={() => nav.go("report", result.run_id)}>결과 보고서</button><button className="btn" onClick={() => nav.go("findings", result.run_id)}>오류 현황</button></div>}>
            <div className="grid c4" style={{ marginBottom: 14 }}>
              <Stat k="검사 행 수" v={fmt(result.rows_total)} s={`테이블 ${Object.keys(result.tables).length}개`} />
              <Stat k="실행 규칙" v={fmt(result.rules_total)} s={`실패 ${result.rules_failed} · 건너뜀 ${result.rules_skipped}`} />
              <Stat k="위반 건수" v={fmt(result.violations_total)} s={`오류 ${fmt(result.violations_error)} · 경고 ${fmt(result.violations_warning)}`} tone={result.violations_total ? "red" : "green"} />
              <Stat k="오류율" v={pct(result.rows_total ? (result.violations_total / result.rows_total) * 100 : 0)} s="위반 건수 ÷ 검사 행 수" />
            </div>
            <OutputList outputs={outputs} runId={result.run_id} />
          </Card>
        </div>
      )}

      {preview && (
        <div className="modal" onClick={() => setPreview(null)}>
          <div className="modal-body" onClick={(e) => e.stopPropagation()}>
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 8 }}>
              <div><b>{preview.c.name}</b> <span style={{ color: "var(--muted)", fontSize: 12 }}>· 앞 {preview.data.rows.length}행 / 전체 {fmt(preview.data.total)}행 · 컬럼 {preview.data.columns.length}개</span></div>
              <button className="btn sm" onClick={() => setPreview(null)}>닫기</button>
            </div>
            <div className="tblwrap" style={{ maxHeight: "70vh" }}>
              <table className="tbl mono" style={{ fontSize: 11.5 }}>
                <thead><tr>{preview.data.columns.map((c, i) => <th key={i}>{c}</th>)}</tr></thead>
                <tbody>{preview.data.rows.map((r, i) => <tr key={i}>{preview.data.columns.map((_, j) => <td key={j} className="nw">{r[j] ?? ""}</td>)}</tr>)}</tbody>
              </table>
            </div>
          </div>
        </div>
      )}
      {!plan && <Empty>코호트를 고르고 파일을 넣으면 테이블 대응표와 사전 점검 결과가 여기에 나타납니다.</Empty>}
    </>
  );
}

/** 출력물 목록 (검증 실행 ④ 와 결과 보고서에서 공용) */
export function OutputList({ outputs, runId }: { outputs: RunOutputs; runId: string }) {
  const [msg, setMsg] = useState<string | null>(null);
  const bundle = async () => { const p = await api.exportBundle(runId); if (p) setMsg(`저장됨: ${p}`); };
  return (
    <div>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 6 }}>
        <div className="sub" style={{ fontWeight: 600, color: "var(--navy)", margin: 0 }}>출력물 {outputs.files.filter((f) => f.size > 0).length}개</div>
        <div style={{ display: "flex", gap: 6 }}>
          <button className="btn primary sm" onClick={bundle}>결과 폴더로 내보내기 (전체)</button>
          <button className="btn sm" onClick={() => api.openPath(outputs.dir)}>실행 폴더 열기</button>
        </div>
      </div>
      {msg && <div className="callout" style={{ marginBottom: 8 }}>{msg}</div>}
      <table className="tbl">
        <thead><tr><th>파일</th><th>내용</th><th>외부 제출</th><th className="num">크기</th><th></th></tr></thead>
        <tbody>{outputs.files.filter((f) => f.size > 0).map((f) => (
          <tr key={f.key}>
            <td style={{ whiteSpace: "nowrap" }}><b>{f.label}</b><div className="mono" style={{ fontSize: 11, color: "var(--muted)" }}>{f.name}</div></td>
            <td>{f.desc}</td>
            <td>{f.shareable ? <span className="pill pass">가능</span> : <span className="pill error">금지 · 환자 단위 정보</span>}</td>
            <td className="num">{bytes(f.size)}</td>
            <td><button className="btn sm" onClick={() => api.exportFile(runId, f.key)}>다른 이름으로 저장</button></td>
          </tr>
        ))}</tbody>
      </table>
    </div>
  );
}

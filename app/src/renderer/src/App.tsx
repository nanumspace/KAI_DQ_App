import { useEffect, useState } from "react";
import { api } from "./api";
import { Dashboard } from "./pages/Dashboard";
import { RunPage } from "./pages/RunPage";
import { CrfPage } from "./pages/CrfPage";
import { RulesPage } from "./pages/RulesPage";
import { FindingsPage } from "./pages/FindingsPage";
import { ReportPage } from "./pages/ReportPage";
import { MonitorPage } from "./pages/MonitorPage";
import { SettingsPage } from "./pages/SettingsPage";

export type Page = "dashboard" | "run" | "crf" | "rules" | "findings" | "report" | "monitor" | "settings";

const MENU: { id: Page; label: string; icon: string }[] = [
  { id: "run", label: "검증 실행", icon: "▶" },
  { id: "crf", label: "서식 변환", icon: "⇄" },
  { id: "report", label: "결과 보고서", icon: "▤" },
  { id: "findings", label: "오류 현황 조회", icon: "⌕" },
  { id: "dashboard", label: "대시보드", icon: "⌂" },
  { id: "monitor", label: "통계 모니터링", icon: "▥" },
  { id: "rules", label: "검증 규칙 관리", icon: "☰" },
  { id: "settings", label: "설정", icon: "⚙" },
];

export interface Nav { page: Page; runId?: string; go: (page: Page, runId?: string) => void }

export function App() {
  const [page, setPage] = useState<Page>("run");
  const [runId, setRunId] = useState<string | undefined>();
  const [version, setVersion] = useState(0); // 실행 완료 시 증가 → 목록 갱신
  // 꼬리말은 지금 켜진 명세 판의 실제 규모를 적는다 (v1 과 v2 는 규칙 수가 다르다)
  const [foot, setFoot] = useState("");
  useEffect(() => {
    Promise.all([api.listRules(), api.listCohorts(), api.getConfig()])
      .then(([rs, cs, cfg]) => setFoot(`${cfg.specVersion} · 규칙 ${rs.length.toLocaleString("ko-KR")}개 · 코호트 ${cs.length}개`))
      .catch(() => setFoot(""));
  }, []);

  const go = (p: Page, r?: string) => { setPage(p); if (r !== undefined) setRunId(r); };
  useEffect(() => api.onNav((p) => setPage(p as Page)), []);
  useEffect(() => api.onProgress((p) => { if (p.stage === "done") setVersion((v) => v + 1); }), []);

  const nav: Nav = { page, runId, go };
  return (
    <div className="app">
      <aside className="sidebar">
        <div className="brand">Quality Validator<small>K-AI 코호트 데이터 품질검증</small></div>
        {MENU.map((m) => (
          <button key={m.id} className={page === m.id ? "active" : ""} onClick={() => setPage(m.id)}>
            <span className="icon">{m.icon}</span>{m.label}
          </button>
        ))}
        <div className="foot">{foot}<br />v0.2.0</div>
      </aside>
      <main className="main">
        {page === "dashboard" && <Dashboard key={version} nav={nav} />}
        {page === "run" && <RunPage nav={nav} />}
        {page === "crf" && <CrfPage />}
        {page === "rules" && <RulesPage />}
        {page === "findings" && <FindingsPage key={`${version}-${runId ?? ""}`} nav={nav} />}
        {page === "report" && <ReportPage key={`${version}-${runId ?? ""}`} nav={nav} />}
        {page === "monitor" && <MonitorPage key={version} nav={nav} />}
        {page === "settings" && <SettingsPage />}
      </main>
    </div>
  );
}

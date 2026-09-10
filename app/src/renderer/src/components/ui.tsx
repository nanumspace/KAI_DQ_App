// 작은 공용 컴포넌트
import type { ReactNode } from "react";
import { severityInfo, rateStatus } from "@shared/labels";

export function Card(props: { title?: ReactNode; num?: number; sub?: ReactNode; children: ReactNode; className?: string; right?: ReactNode }) {
  return (
    <section className={`card ${props.className ?? ""}`}>
      {props.title && (
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start" }}>
          <h2>{props.num !== undefined && <span className="num">{props.num}</span>}{props.title}</h2>
          {props.right}
        </div>
      )}
      {props.sub && <div className="sub">{props.sub}</div>}
      {props.children}
    </section>
  );
}

export function Stat(props: { k: string; v: ReactNode; s?: ReactNode; tone?: "red" | "orange" | "green" }) {
  return (
    <div className="stat">
      <div className="k">{props.k}</div>
      <div className={`v ${props.tone ?? ""}`}>{props.v}</div>
      {props.s && <div className="s">{props.s}</div>}
    </div>
  );
}

export function SeverityPill({ s }: { s: string }) {
  const info = severityInfo(s);
  return <span className={`pill ${info.key}`}>{info.short}</span>;
}

export function StatusPill({ s }: { s: string }) {
  const label: Record<string, string> = { pass: "통과", fail: "실패", skipped: "건너뜀", error: "오류" };
  return <span className={`pill ${s === "error" ? "fail" : s}`}>{label[s] ?? s}</span>;
}

export function RateDot({ pct }: { pct: number }) {
  const st = rateStatus(pct);
  return <span className="dot" style={{ background: st.color }} title={st.label} />;
}

export function Empty({ children }: { children: ReactNode }) {
  return <div className="empty">{children}</div>;
}

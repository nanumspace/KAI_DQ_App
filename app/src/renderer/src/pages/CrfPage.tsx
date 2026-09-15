// 서식 → 레코드 변환 화면.
//
// v2 에서 병원이 채우는 것은 저장 테이블이 아니라 서식이다. 이 화면은 그 서식 폴더를 받아
// 저장 레코드로 바꾸고, 그 결과 폴더를 검증에 그대로 넣을 수 있게 알려 준다.
//
// 서식이 만들지 못하는 표(환자·방문·약물·사망 등)가 있다는 점을 화면에서 분명히 말한다.
// 그것은 EHR 추출본으로 따로 받아야 하며, 모르고 넘어가면 검증에서 '테이블 없음'만 잔뜩 나온다.
import { useEffect, useState } from "react";
import type { CohortInfo, CrfConvertResult } from "@shared/types";
import { api } from "../api";
import { Card, Empty } from "../components/ui";

export function CrfPage() {
  const [cohorts, setCohorts] = useState<CohortInfo[]>([]);
  const [cohort, setCohort] = useState("");
  const [inDir, setInDir] = useState("");
  const [result, setResult] = useState<CrfConvertResult | null>(null);
  const [busy, setBusy] = useState(false);
  const [err, setErr] = useState<string | null>(null);

  // 자동 점검 모드에서는 메인이 변환 결과를 넣어 준다 (화면이 결과까지 그려지는지 보기 위해)
  useEffect(() => api.onSmokeCrf((x) => { setInDir(x.inDir); setResult(x.result); }), []);

  useEffect(() => {
    api.listCohorts().then((cs) => { setCohorts(cs); if (cs[0]) setCohort(cs[0].id); }).catch((e) => setErr(String(e)));
  }, []);

  const chooseDir = async () => {
    const d = await api.chooseDirectory("서식 CSV 가 든 폴더 선택");
    if (d) { setInDir(d); setResult(null); }
  };

  const convert = async () => {
    if (!cohort || !inDir) return;
    setBusy(true); setErr(null);
    try {
      setResult(await api.convertCrf({ cohort, inDir }));
    } catch (e) {
      setErr(String(e));
    } finally {
      setBusy(false);
    }
  };

  const formCount = result ? Object.keys(result.formsRead).length : 0;
  const rowCount = result ? Object.values(result.formsRead).reduce((a, b) => a + b, 0) : 0;
  const recCount = result ? Object.values(result.tablesWritten).reduce((a, b) => a + b, 0) : 0;

  return (
    <>
      <div className="page-title"><h1>서식 변환</h1></div>
      {err && <div className="callout err" style={{ marginBottom: 12 }}>{err}</div>}

      <Card title="서식 폴더" sub="파일 하나가 서식 하나입니다 (예: PATHOLOGY_REPORT.csv). 빈 양식은 '검증 실행' 화면에서 내려받을 수 있습니다">
        <div className="form">
          <label>코호트
            <select value={cohort} onChange={(e) => { setCohort(e.target.value); setResult(null); }}>
              {cohorts.map((c) => <option key={c.id} value={c.id}>{c.kor ?? c.id}</option>)}
            </select>
          </label>
          <label>폴더
            <div className="row">
              <input type="text" value={inDir} readOnly placeholder="서식 CSV 가 든 폴더" />
              <button className="btn" onClick={chooseDir}>선택</button>
            </div>
          </label>
          <div className="row">
            <button className="btn primary" disabled={!cohort || !inDir || busy} onClick={convert}>
              {busy ? "변환 중…" : "레코드로 바꾸기"}
            </button>
          </div>
        </div>
      </Card>

      {!result ? (
        <Card title="결과"><Empty>서식 폴더를 고르고 변환을 누르세요.</Empty></Card>
      ) : (
        <>
          <Card title="변환 결과" sub={`서식 ${formCount}개 ${rowCount}행 → 레코드 ${recCount}건`}>
            <div className="kv">
              <span className="k">저장 위치</span><code>{result.outDir}</code>
            </div>
            <p className="muted" style={{ marginTop: 8 }}>
              이 폴더를 <b>검증 실행</b> 화면에서 입력으로 고르면 됩니다.
            </p>
            <table className="table" style={{ marginTop: 12 }}>
              <thead><tr><th>저장 테이블</th><th style={{ textAlign: "right" }}>레코드</th></tr></thead>
              <tbody>
                {Object.entries(result.tablesWritten).sort().map(([t, n]) => (
                  <tr key={t}><td>{t}</td><td style={{ textAlign: "right" }}>{n.toLocaleString("ko-KR")}</td></tr>
                ))}
              </tbody>
            </table>
          </Card>

          {result.tablesFromEhr.length > 0 && (
            <Card title="서식으로는 만들 수 없는 표">
              <div className="callout">
                아래 표는 어느 서식에도 들어 있지 않습니다. 서식은 EHR 에 구조화되어 있지 않은 것을 받는 자리라,
                환자·방문·약물처럼 <b>EHR 에서 그대로 뽑는 표는 추출본으로 따로</b> 주셔야 합니다.
                이 표들을 함께 넣지 않으면 검증에서 &lsquo;테이블 없음&rsquo;으로 나옵니다.
              </div>
              <div className="chips" style={{ marginTop: 10 }}>
                {result.tablesFromEhr.map((t) => <span key={t} className="chip">{t}</span>)}
              </div>
            </Card>
          )}

          {result.missingForms.length > 0 && (
            <Card title="폴더에 없던 서식" sub="이 코호트가 채워야 하는데 파일이 없었습니다">
              <div className="chips">
                {result.missingForms.map((f) => <span key={f} className="chip">{f}</span>)}
              </div>
            </Card>
          )}

          <Card title={`확인할 점 ${result.issues.length}건`}>
            {result.issues.length === 0 ? (
              <Empty>변환 중 확인할 점이 없었습니다.</Empty>
            ) : (
              <table className="table">
                <thead><tr><th>서식</th><th>행</th><th>필드</th><th>내용</th></tr></thead>
                <tbody>
                  {result.issues.slice(0, 200).map((i, k) => (
                    <tr key={k}><td>{i.form}</td><td>{i.row}</td><td>{i.field ?? ""}</td><td>{i.message}</td></tr>
                  ))}
                </tbody>
              </table>
            )}
          </Card>
        </>
      )}
    </>
  );
}

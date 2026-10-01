# -*- coding: utf-8 -*-
"""단계 2 (v3): v3 명세(의뢰사 9/30 매뉴얼 + 10/01 검토 결정)로 가상데이터를 만드는 프레임워크.

v3 는 v1 과 같은 모양(코호트마다 질환 테이블 1개 + 핵심 OMOP 테이블)이라 v1 `Ctx` 의
난수·환자·방문·이벤트 헬퍼를 그대로 물려받는다. 달라지는 곳은 아래뿐이다.

  항암요법   ANTP_THERAPY(antp_id) 가 SACT(sact_id) 로 바뀌었다. 요법 시작/종료일과 line 번호는
             환자 여정이 끝난 뒤 `finalize_person` 이 연결 약물에서 다시 계산한다
             (시작 = MIN(약물 시작), 종료 = MAX(약물 종료), line = 시작일 순서).
  약물       DRUG_EXPOSURE.antp_id -> sact_id, note_id(SMILES 노트) 삭제.
             SMILES 는 성분별 참조표 DRUG_INGREDIENT_STRUCTURE 로 옮겨 모든 코호트에 싣는다.
  이상사례   is_serious -> is_serious_yn. drug_exposure_id/antp_id 등 연결 열이 없다.
  질환 테이블 환자당 1행(진단 방문에 매단다).

시나리오(`synth/scenarios/*_v3.py`)는 `Ctx` 대신 `CtxV3` 를 받는다.
"""
import datetime as dt
import os
import sys
import zlib
from collections import defaultdict

import numpy as np
import pandas as pd
import yaml

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from framework import (CONCEPTS, EHR, ER, FEMALE, INPATIENT, MALE, OUTPATIENT, Person, fmt)  # noqa: E402,F401
from framework import Ctx as CtxV1  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SPEC = yaml.safe_load(open(os.path.join(ROOT, "spec/v3/kai_cdm_spec_v3.yaml"), encoding="utf-8"))["tables"]
PROFILES = yaml.safe_load(open(os.path.join(ROOT, "spec/v3/cohort_profiles_v3.yaml"), encoding="utf-8"))["cohorts"]
D = dt.date

# 성분 SMILES. 항체·펩타이드(pembrolizumab, trastuzumab, bevacizumab, rituximab, brentuximab vedotin,
# insulin glargine, semaglutide, filgrastim, bleomycin)는 단일 SMILES 로 적을 수 없어 참조표에 싣지 않는다.
SMILES = {
    1503297: "CN(C)C(=N)NC(=N)N",                                              # metformin
    1397141: "N.N.Cl[Pt]Cl",                                                   # cisplatin
    1344905: "O=C1O[Pt](N)(N)OC(=O)C12CCC2",                                   # carboplatin
    1304919: "Nc1nc2[nH]cc(CCc3ccc(cc3)C(=O)NC(CCC(=O)O)C(=O)O)c2c(=O)[nH]1",  # pemetrexed
    1378382: "CC1=C2C(C(=O)C3(C(CC4C(C3C(C(C2(C)C)(CC1OC(=O)C(C(C5=CC=CC=C5)NC(=O)C6=CC=CC=C6)O)O)OC(=O)C7=CC=CC=C7)(CO4)OC(=O)C)O)C)OC(=O)C",  # paclitaxel
    1315942: "CC1=C2C(C(=O)C3(C(CC4C(C3C(C(C2(C)C)(CC1OC(=O)C(C(C5=CC=CC=C5)NC(=O)OC(C)(C)C)O)O)OC(=O)C6=CC=CC=C6)(CO4)OC(=O)C)O)C)O",  # docetaxel
    1314924: "NC1=NC(=O)N(C=C1)C1OC(CO)C(O)C1(F)F",                             # gemcitabine
    35604205: "COc1cc(N(C)CCN(C)C)c(NC(=O)C=C)cc1Nc1nccc(-c2cn(C)c3ccccc23)n1",  # osimertinib
    1338512: "COc1cccc2C(=O)c3c(O)c4CC(O)(CC(OC5CC(N)C(O)C(C)O5)c4c(O)c3C(=O)c12)C(=O)CO",  # doxorubicin
    1310317: "ClCCN(CCCl)P1(=O)NCCCO1",                                        # cyclophosphamide
    1436678: "CC/C(=C(\\c1ccccc1)c1ccc(OCCN(C)C)cc1)c1ccccc1",                 # tamoxifen
    1348265: "N#Cc1ccc(C(c2ccc(C#N)cc2)n2cncn2)cc1",                           # letrozole
    1319247: "CC(C)(C#N)c1cc(Cn2cncn2)cc(c1)C(C)(C)C#N",                       # anastrozole
    1320011: "O=C1O[Pt]2(OC1=O)NC1CCCCC1N2",                                   # oxaliplatin
    955632: "O=C1NC(=O)NC=C1F",                                                # fluorouracil
    1337620: "CCCCCOC(=O)Nc1nc(=O)n(C2OC(C)C(O)C2O)cc1F",                       # capecitabine
    1367268: "CCC1=C2CN3C(=CC4=C(C3=O)COC(=O)C4(CC)O)C2=NC5=C1C=C(C=C5)OC(=O)N6CCC(CC6)N7CCCCC7",  # irinotecan
    1308290: "CCC1(CC2CC(C3=C(CCN(C2)C1)C4=CC=CC=C4N3)(C5=C(C=C6C(=C5)C78CCN9C7C(C=CC9)(C(C(C8N6C=O)(C(=O)OC)O)OC(=O)C)CC)OC)C(=O)OC)O",  # vincristine
    1551099: "CC12CC(=O)C3C(C1CCC2(C(=O)CO)O)CCC4=CC(=O)C=CC34C",                # prednisone
    1350504: "CC1OCC2C(O1)C(C(C(O2)OC3C4C(COC4=O)C(C5=CC6=C(C=C35)OCO6)C7=CC(=C(C(=C7)OC)O)OC)O)O",  # etoposide
    1319193: "CN(C)N=NC1=C(NC=N1)C(=O)N",                                      # dacarbazine
    1597756: "CCC1=C(C)CN(C1=O)C(=O)NCCc1ccc(cc1)S(=O)(=O)NC(=O)NC1CCC(C)CC1",  # glimepiride
    1580747: "Fc1cc(F)c(F)cc1CC(N)CC(=O)N1CCn2c(nnc2C(F)(F)F)C1",              # sitagliptin
    45774435: "OCC1OC(c2ccc(Cl)c(Cc3ccc(OC4CCOC4)cc3)c2)C(O)C(O)C1O",          # empagliflozin
    1545958: "CC(C)c1c(C(=O)Nc2ccccc2)c(-c2ccccc2)c(-c2ccc(F)cc2)n1CCC(O)CC(O)CC(=O)O",  # atorvastatin
    1308216: "NCCCCC(NC(CCc1ccccc1)C(=O)O)C(=O)N1CCCC1C(=O)O",                 # lisinopril
    1584910: "CCc1ccc(CCOc2ccc(CC3SC(=O)NC3=O)cc2)nc1",                         # pioglitazone
    1518254: "CC1CC2C3CCC4=CC(=O)C=CC4(C3(C(CC2(C1(C(=O)CO)O)C)O)F)C",          # dexamethasone
    35201159: "Cc1nccn1CC1CCc2c(C1=O)c1ccccc1n2C",                             # ondansetron
}


def regimen_concept(name):
    """요법 이름에서 안정적으로 정해지는 regimen_concept_id (HemOnc 대역 35,8xx,xxx 모사)."""
    return 35800000 + zlib.crc32(name.encode("utf-8")) % 100000


class CtxV3(CtxV1):
    def __init__(self, cohort, seed=20260907, id_base=None):
        self.cohort = cohort
        self.profile = PROFILES[cohort]
        self.tables = list(self.profile["tables"])
        self.disease = [t for t in self.tables if SPEC[t]["category"] == "disease"][0]
        self.disease_pk = SPEC[self.disease]["pk"]
        self.has_sact = "SACT" in self.tables
        self.rng = np.random.default_rng(seed)
        base = id_base if id_base is not None else (list(PROFILES).index(cohort) + 1) * 100000
        self.ids = defaultdict(lambda: base)
        self.rows = {t: [] for t in self.tables}
        self.persons = []
        self.today = D(2026, 9, 1)
        self._sact = {}

    # ------------------------------------------------------------------ 약물
    def drug(self, p, start, concept, days, vid=None, sact_id=None, dose=None, freq=None, quantity=None,
             interval=None, number=None):
        d = CONCEPTS["drugs"][concept]
        vid = vid or self.visit_on(p, start)
        end = self.days(start, days - 1)
        did = self.nid("DRUG_EXPOSURE")
        dose = d["dose"] if dose is None else dose
        if interval is not None and interval > 1 and number is None:
            number = 1                       # SEM3-COM-006: 간격 > 1일이면 횟수 필수
        self.rows["DRUG_EXPOSURE"].append(dict(
            drug_exposure_id=did, visit_occurrence_id=vid, person_id=p.person_id, sact_id=sact_id,
            drug_concept_id=concept, drug_source_value=d["name"],
            drug_exposure_start_date=start, drug_exposure_end_date=end, days_supply=days,
            amount_unit_concept_id=d["unit"], amount_value=dose, quantity=quantity,
            numerator_value=None, numerator_unit_concept_id=None, denominator_value=None, denominator_unit_concept_id=None,
            frequency_per_day=freq, dosing_interval_day=interval, dosing_number=number))
        return did, end

    # ------------------------------------------------------------ 항암요법
    def sact(self, p, regimen, drug_concepts, start, cycles, intent, ecog=None, response=None,
             cycle_days=None, oral=False, inpatient_first=False, drug_days=None):
        """항암요법 1건 + 사이클별 DRUG_EXPOSURE. 반환 (sact_id, end_date, cycle_dates).

        line_of_therapy 와 요법 시작/종료일은 `finalize_person` 이 채운다.
        drug_days: {concept: 일수} 로 약물별 투여일수를 직접 정할 수 있다(기본: 정맥 1일, 경구는 사이클 길이).
        """
        assert self.has_sact
        sid = self.nid("SACT")
        cycle_dates, ends = [], []
        cd = cycle_days or max(CONCEPTS["drugs"][c]["cycle_days"] or 21 for c in drug_concepts)
        cur = start
        for cyc in range(cycles):
            if (p.death_date is not None and cur > p.death_date) or cur > self.today:
                break
            vid = self.visit(p, cur, INPATIENT, los=min(2, (self.today - cur).days)) if (inpatient_first and cyc == 0) else self.visit_on(p, cur)
            cycle_dates.append(cur)
            for c in drug_concepts:
                dc = CONCEPTS["drugs"][c]
                if drug_days and c in drug_days:
                    days = drug_days[c]
                elif oral or dc["route"] == "PO":
                    days = cd if dc["route"] == "PO" else 1
                    days = min(days, cd)
                    if dc["name"] == "prednisone": days = 5
                    if dc["name"] == "capecitabine": days = 14
                else:
                    days = 1
                last = min(self.today, p.death_date) if p.death_date is not None else self.today
                days = min(days, (last - cur).days + 1)
                _, e = self.drug(p, cur, c, days, vid=vid, sact_id=sid, freq=1 if dc["route"] == "PO" else None,
                                 interval=None if dc["route"] == "PO" else cd, number=None if dc["route"] == "PO" else 1)
                ends.append(e)
            cur = self.days(cur, cd)
        assert ends, "SACT 에는 약물이 하나 이상 있어야 한다"
        row = dict(sact_id=sid, person_id=p.person_id, regimen_concept_id=regimen_concept(regimen), regimen_source_value=regimen,
                   regimen_start_date=start, regimen_end_date=max(ends), line_of_therapy=None, number_of_cycles=len(cycle_dates),
                   therapy_intent=intent, ecog_performance_status=ecog, best_overall_response=response,
                   date_of_progression=None, recurrence_anatomic_site=None)
        self.rows["SACT"].append(row)
        self._sact[sid] = row
        return sid, max(ends), cycle_dates

    def sact_update(self, sid, **kw):
        self._sact[sid].update(kw)

    def finalize_person(self, p):
        """요법 시작/종료일을 연결 약물에서, line 번호를 시작일 순서에서 다시 계산하고 PERSON 행을 쓴다."""
        if self.has_sact:
            mine = [r for r in self.rows["SACT"] if r["person_id"] == p.person_id]
            by_sact = defaultdict(list)
            for r in self.rows["DRUG_EXPOSURE"]:
                if r["person_id"] == p.person_id and r["sact_id"] is not None:
                    by_sact[r["sact_id"]].append(r)
            for r in mine:
                drugs = by_sact[r["sact_id"]]
                r["regimen_start_date"] = min(x["drug_exposure_start_date"] for x in drugs)
                r["regimen_end_date"] = max(x["drug_exposure_end_date"] for x in drugs)
            for rn, r in enumerate(sorted(mine, key=lambda r: (r["regimen_start_date"], r["sact_id"])), 1):
                r["line_of_therapy"] = rn
                if r["date_of_progression"] is not None and r["date_of_progression"] < r["regimen_start_date"]:
                    r["date_of_progression"] = r["regimen_start_date"]
        super().finalize_person(p)

    # ------------------------------------------------------------ 이상사례
    def ae(self, p, date, concept, grade, vid=None, causality=3, serious=None, outcome=1, action=1):
        vid = vid or self.visit_on(p, date)
        aid = self.nid("ADVERSE_EVENT")
        serious = (grade >= 3) if serious is None else serious
        if grade == 5:
            outcome = 5
        self.rows["ADVERSE_EVENT"].append(dict(
            adverse_event_id=aid, person_id=p.person_id, visit_occurrence_id=vid, adverse_event_concept_id=concept,
            adverse_event_start_date=date, severity_concept_id=grade, causality_concept_id=causality,
            is_serious_yn=1 if serious else 0, seriousness_concept_id=(1 if grade == 5 else 3) if serious else None,
            outcome_concept_id=outcome, action_taken_concept_id=action))
        return aid

    # v3 전용 하한: AST/ALT 정확히 0, 크레아티닌 0.1 같은 비현실 값을 막는다 (v1/v2 CtxV1.labs 는 건드리지 않음).
    LAB_FLOOR = {3013721: 8.0, 3006923: 6.0, 3016723: 0.5}
    WBC, ANC = 3010813, 3017732

    def labs(self, p, date, concepts, vid=None, shifts=None):
        """CtxV1.labs 와 같은 시그니처. 같은 날 WBC/ANC 는 종속 추출: WBC 를 먼저 뽑고 ANC = WBC x 호중구 분획
        (분획 평균은 ANC shift 만큼 낮아짐), 따라서 항상 0.1 <= ANC <= WBC."""
        shifts = shifts or {}
        out = {}
        for c in concepts:
            nd = 2 if c in (3016723, 3004410, 3024128, 3020491) else 1
            if c == self.WBC:
                out[c] = self.lab_value(c, shifts.get(c, 0.0), lo=0.3, nd=nd)
            elif c == self.ANC and self.WBC in concepts:
                continue                                           # WBC 이후 파생
            else:
                out[c] = self.lab_value(c, shifts.get(c, 0.0), lo=self.LAB_FLOOR.get(c), nd=nd)
        if self.ANC in concepts:
            if self.WBC in out:
                frac = self.normal(0.60 + 0.05 * shifts.get(self.ANC, 0.0), 0.10, 0.05, 0.90, 3)
                out[self.ANC] = round(min(out[self.WBC], max(0.1, out[self.WBC] * frac)), 1)
            else:
                out[self.ANC] = self.lab_value(self.ANC, shifts.get(self.ANC, 0.0), lo=0.1)
        for c in concepts:                                         # 요청 순서대로 기록
            self.measure(p, date, c, out[c], vid=vid)
        return {c: out[c] for c in concepts}

    def monitor(self, p, cycle_dates, drugs, ae_p=0.45, labs=(3000963, 3010813, 3017732, 3024929, 3016723, 3013721, 3006923),
                ae_pool=((27674, 0.2), (301794, 0.2), (439777, 0.15), (4223659, 0.15), (196523, 0.1), (4166735, 0.1), (140214, 0.05), (4304213, 0.05))):
        """사이클마다 혈액·신장·간기능, 일부 사이클에 이상사례(+ 같은 날 CONDITION)."""
        concepts = [c for c, _ in ae_pool]
        probs = np.array([w for _, w in ae_pool], dtype=float)
        probs = probs / probs.sum()
        for i, d in enumerate(cycle_dates):
            vid = self.visit_on(p, d)
            shifts = {3017732: -1.5 if i > 0 else 0, 3000963: -1.0 if i > 0 else 0}
            self.labs(p, d, list(labs), vid=vid, shifts=shifts)
            if i > 0 and self.bern(ae_p):
                ae_day = self.days(d, self.randint(3, 12))
                if (p.death_date is not None and ae_day > p.death_date) or ae_day > self.today:
                    continue
                concept = self.choice(concepts, p=probs)
                lo, hi = CONCEPTS["adverse_events"][concept]["typical_grade"]
                grade = self.randint(lo, hi)
                avid = self.visit(p, ae_day, ER if grade >= 3 else OUTPATIENT)
                self.ae(p, ae_day, concept, grade, vid=avid, action=2 if grade >= 3 else 1)
                self.condition(p, ae_day, concept, vid=avid)
                if concept in (301794, 4304213):
                    self.drug(p, ae_day, 1301125, 3, vid=avid, freq=1)       # G-CSF: L03, sact_id 없음
                if concept == 27674 and self.bern(0.4):
                    self.drug(p, ae_day, 1518254, 3, vid=avid, freq=1)       # 구토 대증용 dexamethasone: 항암요법이 아니라 sact_id 없음

    # ------------------------------------------------------- 특화 테이블 행
    def disease_row(self, p, vid, **fields):
        """환자당 1행. 만들어진 행(dict)을 돌려주므로 여정 후반에 값을 고칠 수 있다."""
        row = dict(person_id=p.person_id, visit_occurrence_id=vid)
        row.update(fields)
        row[self.disease_pk] = self.nid(self.disease)
        self.rows[self.disease].append(row)
        return row

    # ---------------------------------------------------------------- write
    def reference_rows(self):
        used = sorted({r["drug_concept_id"] for r in self.rows["DRUG_EXPOSURE"]})
        return [dict(ingredient_concept_id=c, smiles=SMILES[c]) for c in used if c in SMILES]

    def write(self, out_dir):
        os.makedirs(out_dir, exist_ok=True)
        self.rows["DRUG_INGREDIENT_STRUCTURE"] = self.reference_rows()
        for t in self.tables:
            cols = [f["name"] for f in SPEC[t]["fields"]]
            rows = self.rows[t]
            df = pd.DataFrame(rows, columns=cols) if rows else pd.DataFrame(columns=cols)
            for c in cols:
                df[c] = df[c].apply(fmt)
            df.to_csv(os.path.join(out_dir, f"{t}.csv"), index=False, encoding="utf-8")
        return {t: len(self.rows[t]) for t in self.tables}

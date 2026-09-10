# -*- coding: utf-8 -*-
"""
단계 2: 가상데이터 생성 프레임워크

- 명세(spec/kai_cdm_spec.yaml)에서 테이블/컬럼을 읽어, 코호트별로 <TABLE>.csv 를 쓴다.
- 시드 기반(numpy Generator)이라 같은 시드면 같은 데이터가 나온다.
- 질환별 시나리오 모듈(synth/scenarios/<disease>.py)은 여기의 Ctx 헬퍼만 사용해 환자 여정을 기술한다.
- 규칙 카탈로그(rules/)의 모든 규칙을 "구성상" 만족하도록 헬퍼가 강제한다:
    * 모든 이벤트는 방문(visit) 안에서 발생 (SEM-COM-005/006)
    * 사망 이후 이벤트 금지 (SEM-COM-003)
    * 약물 종료일 = 시작일 + days_supply - 1 (SEM-COM-007)
    * 항암요법 시작/종료일 = 연결 약물의 MIN/MAX (SEM-COM-019)
    * 특화 테이블은 이벤트 그룹 단위 1행, 환자 불변 필드는 자동 복사 (D-01, person_invariant)
"""
import os, sys, io, datetime as dt, math
from collections import OrderedDict, defaultdict
import numpy as np
import pandas as pd
import yaml

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SPEC = yaml.safe_load(open(os.path.join(ROOT, "spec/kai_cdm_spec.yaml"), encoding="utf-8"))["tables"]
CONCEPTS = yaml.safe_load(open(os.path.join(ROOT, "spec/concepts.yaml"), encoding="utf-8"))
PROFILES = yaml.safe_load(open(os.path.join(ROOT, "spec/cohort_profiles.yaml"), encoding="utf-8"))["cohorts"]
CODELISTS = yaml.safe_load(open(os.path.join(ROOT, "spec/codelists.yaml"), encoding="utf-8"))

D = dt.date
EHR = 32817
OUTPATIENT, INPATIENT, ER = 9202, 9201, 9203
MALE, FEMALE = 8507, 8532

SMILES = {
    1503297: "CN(C)C(=N)NC(=N)N", 1397141: "N.N.Cl[Pt]Cl", 955632: "O=C1NC(=O)NC=C1F",
    1436678: "CC/C(=C(\\c1ccccc1)c1ccc(OCCN(C)C)cc1)c1ccccc1", 1337620: "CCCCCOC(=O)Nc1nc(=O)n(C2OC(C)C(O)C2O)cc1F",
    35604205: "COc1cc(N(C)CCN(C)C)c(NC(=O)C=C)cc1Nc1nccc(-c2cn(C)c3ccccc23)n1",
    1348265: "N#Cc1ccc(C(c2ccc(C#N)cc2)n2cncn2)cc1", 1320011: "O=C1O[Pt]2(OC1=O)NC1CCCCC1N2",
    1580747: "Fc1cc(F)c(F)cc1CC(N)CC(=O)N1CCn2c(nnc2C(F)(F)F)C1", 45774435: "OCC1OC(c2ccc(Cl)c(Cc3ccc(OC4CCOC4)cc3)c2)C(O)C(O)C1O",
}


class Person:
    def __init__(self, pid, gender, birth, index_date, care_site=1):
        self.person_id = pid
        self.gender = gender
        self.birth = birth
        self.index_date = index_date
        self.care_site = care_site
        self.death_date = None
        self.patient_fields = {}     # 특화 테이블 환자 불변 필드
        self.visits = []             # (vid, start, end, kind)

    @property
    def age_at_index(self):
        return self.index_date.year - self.birth.year - ((self.index_date.month, self.index_date.day) < (self.birth.month, self.birth.day))

    def age_on(self, d):
        return d.year - self.birth.year - ((d.month, d.day) < (self.birth.month, self.birth.day))


class Ctx:
    def __init__(self, cohort, seed=20260907, id_base=None):
        self.cohort = cohort
        self.profile = PROFILES[cohort]
        self.tables = self.profile["tables"]
        self.disease = [t for t in self.tables if SPEC[t]["category"] == "disease"][0]
        self.disease_pk = SPEC[self.disease]["pk"]
        self.has_antp = "ANTP_THERAPY" in self.tables
        self.rng = np.random.default_rng(seed)
        base = id_base if id_base is not None else (list(PROFILES).index(cohort) + 1) * 100000
        self.ids = defaultdict(lambda: base)
        self.rows = {t: [] for t in self.tables}
        self.persons = []
        self.drug_notes = {}
        self.today = D(2026, 9, 1)

    # ------------------------------------------------------------ utilities
    def nid(self, table):
        self.ids[table] += 1
        return self.ids[table]

    def choice(self, seq, p=None):
        idx = self.rng.choice(len(seq), p=p)
        return seq[idx]

    def rand(self, lo, hi):
        return float(self.rng.uniform(lo, hi))

    def randint(self, lo, hi):
        return int(self.rng.integers(lo, hi + 1))

    def normal(self, mean, sd, lo=None, hi=None, nd=1):
        v = float(self.rng.normal(mean, sd))
        if lo is not None: v = max(lo, v)
        if hi is not None: v = min(hi, v)
        return round(v, nd)

    def bern(self, p):
        return bool(self.rng.random() < p)

    def days(self, d, n):
        return d + dt.timedelta(days=int(n))

    def clip_before_death(self, person, d):
        return d if person.death_date is None or d <= person.death_date else None

    # -------------------------------------------------------------- person
    def person(self, gender, age_at_index, index_date, obs_years_before=None):
        pid = self.nid("PERSON")
        birth_year = index_date.year - age_at_index
        birth = D(birth_year, self.randint(1, 12), self.randint(1, 28))
        if (index_date.month, index_date.day) < (birth.month, birth.day):
            birth = D(birth_year - 1, birth.month, birth.day)
        p = Person(pid, gender, birth, index_date)
        oy = obs_years_before if obs_years_before is not None else self.randint(0, 3)
        p.obs_start = self.days(index_date, -365 * oy - self.randint(0, 300))
        self.persons.append(p)
        return p

    def finalize_person(self, p):
        self.rows["PERSON"].append(dict(
            person_id=p.person_id, gender_concept_id=p.gender, year_of_birth=p.birth.year, month_of_birth=p.birth.month,
            day_of_birth=p.birth.day, age_at_index=p.age_at_index, care_site_id=p.care_site,
            observation_period_start_date=p.obs_start, death_date=p.death_date))

    def set_death(self, p, date):
        p.death_date = date

    # --------------------------------------------------------------- visits
    def visit(self, p, start, kind=OUTPATIENT, los=0):
        """방문 생성. 입원은 los 일 만큼 (end = start + los). 입원 중첩은 호출자가 피한다."""
        assert p.death_date is None or start <= p.death_date, f"visit after death {p.person_id}"
        end = self.days(start, los) if kind == INPATIENT else start
        if p.death_date is not None and end > p.death_date:
            end = p.death_date
        vid = self.nid("VISIT_OCCURRENCE")
        self.rows["VISIT_OCCURRENCE"].append(dict(visit_occurrence_id=vid, person_id=p.person_id, visit_concept_id=kind,
                                                  visit_start_date=start, visit_end_date=end, visit_type_concept_id=EHR))
        p.visits.append((vid, start, end, kind))
        return vid

    def visit_on(self, p, date):
        """해당 날짜를 포함하는 기존 방문이 있으면 재사용, 없으면 외래 방문 생성."""
        for vid, s, e, k in p.visits:
            if s <= date <= e:
                return vid
        return self.visit(p, date, OUTPATIENT)

    def visit_dates(self, p, vid):
        for v, s, e, k in p.visits:
            if v == vid:
                return s, e
        raise KeyError(vid)

    # --------------------------------------------------------------- events
    def condition(self, p, date, concept, vid=None, type_concept=EHR):
        vid = vid or self.visit_on(p, date)
        cid = self.nid("CONDITION_OCCURRENCE")
        self.rows["CONDITION_OCCURRENCE"].append(dict(condition_occurrence_id=cid, visit_occurrence_id=vid, person_id=p.person_id,
                                                      condition_concept_id=concept, condition_start_date=date, condition_type_concept_id=type_concept))
        return cid

    def procedure(self, p, date, concept, vid=None):
        vid = vid or self.visit_on(p, date)
        pid = self.nid("PROCEDURE_OCCURRENCE")
        self.rows["PROCEDURE_OCCURRENCE"].append(dict(procedure_occurrence_id=pid, visit_occurrence_id=vid, person_id=p.person_id,
                                                      procedure_concept_id=concept, procedure_date=date, procedure_type_concept_id=EHR))
        return pid

    def measure(self, p, date, concept, value, vid=None, value_concept=None, unit=None):
        m = CONCEPTS["measurements"][concept]
        vid = vid or self.visit_on(p, date)
        mid = self.nid("MEASUREMENT")
        self.rows["MEASUREMENT"].append(dict(
            measurement_id=mid, visit_occurrence_id=vid, person_id=p.person_id, measurement_concept_id=concept, measurement_date=date,
            measurement_type_concept_id=32856, value_as_number=value, value_as_concept_id=value_concept,
            unit_concept_id=unit or m["unit"], range_low=m["normal"][0], range_high=m["normal"][1],
            unit_source_value=m["unit_label"], value_source_value=None if value is None else str(value)))
        return mid

    def lab_value(self, concept, shift=0.0, sd_scale=1.0, lo=None, hi=None, nd=1):
        m = CONCEPTS["measurements"][concept]
        g = m["gen"]
        plo, phi = m["plausible"]
        v = self.normal(g["mean"] + shift, g["sd"] * sd_scale, plo if lo is None else lo, phi if hi is None else hi, nd)
        return v

    def labs(self, p, date, concepts, vid=None, shifts=None):
        """여러 검사를 한 번에. shifts: {concept: shift}"""
        out = {}
        for c in concepts:
            nd = 2 if c in (3016723, 3004410, 3024128, 3020491) else 1
            v = self.lab_value(c, (shifts or {}).get(c, 0.0), nd=nd)
            out[c] = v
            self.measure(p, date, c, v, vid=vid)
        return out

    def observation(self, p, date, concept, vid=None, value_number=None, value_string=None, unit=None):
        vid = vid or self.visit_on(p, date)
        oid = self.nid("OBSERVATION")
        self.rows["OBSERVATION"].append(dict(observation_id=oid, visit_occurrence_id=vid, person_id=p.person_id, observation_concept_id=concept,
                                             observation_date=date, observation_type_concept_id=EHR, value_as_number=value_number,
                                             value_as_string=None if value_string is None else str(value_string)[:60], unit_concept_id=unit))
        return oid

    def note(self, p, date, text, note_type=44814637, note_class=36716164, vid=None):
        vid = vid or self.visit_on(p, date)
        nid = self.nid("NOTE")
        self.rows["NOTE"].append(dict(note_id=nid, visit_occurrence_id=vid, person_id=p.person_id, note_date=date, note_text=text,
                                      note_type_concept_id=note_type, note_class_concept_id=note_class))
        return nid

    def drug_note(self, p, concept, date, vid):
        key = (p.person_id, concept)
        if key in self.drug_notes:
            return self.drug_notes[key]
        smi = SMILES.get(concept)
        if not smi:
            return None
        nid = self.note(p, date, f"SMILES {CONCEPTS['drugs'][concept]['name']}: {smi}", note_type=32831, note_class=36716177, vid=vid)
        self.drug_notes[key] = nid
        return nid

    def drug(self, p, start, concept, days, vid=None, antp_id=None, dose=None, freq=None, quantity=None, interval=None, number=None):
        d = CONCEPTS["drugs"][concept]
        vid = vid or self.visit_on(p, start)
        end = self.days(start, days - 1)
        did = self.nid("DRUG_EXPOSURE")
        dose = d["dose"] if dose is None else dose
        row = dict(drug_exposure_id=did, visit_occurrence_id=vid, person_id=p.person_id, antp_id=antp_id,
                   note_id=self.drug_note(p, concept, start, vid), drug_concept_id=concept,
                   drug_exposure_start_date=start, drug_exposure_end_date=end, days_supply=days,
                   amount_unit_concept_id=d["unit"], amount_value=dose, quantity=quantity,
                   numerator_value=None, numerator_unit_concept_id=None, denominator_value=None, denominator_unit_concept_id=None,
                   frequency_per_day=freq, dosing_interval_day=interval, dosing_number=number)
        self.rows["DRUG_EXPOSURE"].append(row)
        return did, end

    # ------------------------------------------------------------ 항암요법
    def antp(self, p, line, regimen, drug_concepts, start, cycles, intent, category, ecog=None, response=None,
             cycle_days=None, oral=False, inpatient_first=False):
        """항암요법 에피소드 + 사이클별 DRUG_EXPOSURE. 반환 (antp_id, end_date, cycle_dates)."""
        assert self.has_antp
        aid = self.nid("ANTP_THERAPY")
        cycle_dates, ends = [], []
        cd = cycle_days or max(CONCEPTS["drugs"][c]["cycle_days"] or 21 for c in drug_concepts)
        cur = start
        for cyc in range(cycles):
            if p.death_date is not None and cur > p.death_date:
                break
            vid = self.visit(p, cur, INPATIENT, los=2) if (inpatient_first and cyc == 0) else self.visit_on(p, cur)
            cycle_dates.append(cur)
            for c in drug_concepts:
                dc = CONCEPTS["drugs"][c]
                if oral or dc["route"] == "PO":
                    days = cd if dc["route"] == "PO" else 1
                    days = min(days, cd)
                    if dc["name"] == "prednisone": days = 5
                    if dc["name"] == "capecitabine": days = 14
                else:
                    days = 1
                if p.death_date is not None and self.days(cur, days - 1) > p.death_date:
                    days = max(1, (p.death_date - cur).days + 1)
                _, e = self.drug(p, cur, c, days, vid=vid, antp_id=aid, freq=1 if dc["route"] == "PO" else None,
                                 interval=None if dc["route"] == "PO" else cd, number=None if dc["route"] == "PO" else 1)
                ends.append(e)
            cur = self.days(cur, cd)
        end = max(ends)
        self._antp_rows = getattr(self, "_antp_rows", {})
        row = dict(antp_id=aid, person_id=p.person_id, regimen_or_line_of_therapy=line, regimen=regimen, regimen_source_value=regimen,
                   antp_start_date=start, antp_end_date=end, number_of_cycles=len(cycle_dates), treatment_intent_type=intent,
                   best_overall_response_source_value=response, drug_category=category, ecog_performance_status=ecog,
                   treatment_outcome=0, days_to_progression=None, progression_or_recurrence_anatomic_site=None)
        self.rows["ANTP_THERAPY"].append(row)
        self._antp_rows[aid] = row
        return aid, end, cycle_dates

    def antp_update(self, aid, **kw):
        self._antp_rows[aid].update(kw)

    # ------------------------------------------------------------ 이상사례
    def ae(self, p, date, concept, grade, antp_id=None, vid=None, drug_exposure_id=None, causality=3, serious=None,
           outcome=1, action=1):
        vid = vid or self.visit_on(p, date)
        aid = self.nid("ADVERSE_EVENT")
        serious = (grade >= 3) if serious is None else serious
        if grade == 5:
            outcome = 5
        self.rows["ADVERSE_EVENT"].append(dict(
            adverse_event_id=aid, person_id=p.person_id, observation_id=None, condition_occurrence_id=None, measurement_id=None,
            procedure_occurrence_id=None, visit_occurrence_id=vid, drug_exposure_id=drug_exposure_id, antp_id=antp_id, note_id=None,
            adverse_event_concept_id=concept, adverse_event_type_concept_id=EHR, adverse_event_start_date=date,
            severity_concept_id=grade, causality_concept_id=causality, is_serious=1 if serious else 0,
            seriousness_concept_id=(1 if grade == 5 else 3) if serious else None, outcome_concept_id=outcome,
            action_taken_concept_id=action))
        return aid

    # ------------------------------------------------------- 특화 테이블 행
    def disease_row(self, p, vid, **fields):
        """이벤트 그룹 1개 = 1행. 환자 불변 필드(p.patient_fields)는 자동 병합."""
        row = dict(person_id=p.person_id, visit_occurrence_id=vid)
        row.update(p.patient_fields)
        row.update(fields)
        row[self.disease_pk] = self.nid(self.disease)
        self.rows[self.disease].append(row)
        return row[self.disease_pk]

    # ---------------------------------------------------------------- write
    def write(self, out_dir):
        os.makedirs(out_dir, exist_ok=True)
        for t in self.tables:
            cols = [f["name"] for f in SPEC[t]["fields"]]
            rows = self.rows[t]
            df = pd.DataFrame(rows, columns=cols) if rows else pd.DataFrame(columns=cols)
            for c in cols:
                if c in df.columns:
                    df[c] = df[c].apply(fmt)
            df.to_csv(os.path.join(out_dir, f"{t}.csv"), index=False, encoding="utf-8")
        return {t: len(self.rows[t]) for t in self.tables}


def fmt(v):
    if v is None or v is pd.NaT:
        return ""
    try:
        if not isinstance(v, (str, list, dict, tuple)) and pd.isna(v):
            return ""
    except (TypeError, ValueError):
        pass
    if isinstance(v, float):
        if math.isnan(v):
            return ""
        return f"{v:.4g}" if abs(v) < 1e-3 and v != 0 else (str(int(v)) if v.is_integer() and abs(v) < 1e15 else f"{v:.6g}")
    if isinstance(v, (np.integer,)):
        return str(int(v))
    if isinstance(v, (np.floating,)):
        return fmt(float(v))
    if isinstance(v, (dt.date, dt.datetime)):
        return v.isoformat() if isinstance(v, dt.date) and not isinstance(v, dt.datetime) else v.strftime("%Y-%m-%d %H:%M:%S")
    if isinstance(v, bool):
        return "1" if v else "0"
    return str(v)

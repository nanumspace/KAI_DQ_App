# -*- coding: utf-8 -*-
"""단계 2 (v2): v2 저장 테이블을 채우는 가상데이터 프레임워크.

v1(`synth/framework.py`)과 나란히 둔다. 병원이 쓰던 v1 경로를 끊지 않고 두 경로가
같은 환자 여정에서 같은 판정을 받는지 견주기 위해서다.

v1 과 달라지는 곳은 세 군데다.

  저장 자리    v1 은 질환마다 큰 테이블 하나(LUNG_CANCER …)를 썼다. v2 는 OMOP 14개에
              K-AI 확장 16개를 더한 구조라, 한 사건이 여러 테이블에 나뉘어 앉는다.
  환자 정보    v1 은 PERSON 한 행에 관찰기간·사망일까지 얹었다. v2 는 OMOP 그대로
              OBSERVATION_PERIOD·DEATH 를 따로 둔다.
  치료 묶음    항암요법은 EPISODE 한 행과 그에 매달린 EPISODE_EVENT 로 적는다.
              약물·이상사례는 각자 OMOP 테이블에 앉고 EPISODE_EVENT 가 이어 준다.

시드를 주면 같은 데이터가 나온다. 난수·날짜 헬퍼와 Person 은 v1 것을 그대로 쓴다.
"""
import datetime as dt
import os
import sys
from collections import defaultdict

import pandas as pd
import yaml

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from framework import EHR, FEMALE, INPATIENT, MALE, OUTPATIENT, Person, fmt  # noqa: E402,F401
from framework import Ctx as CtxV1  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SPEC = yaml.safe_load(open(os.path.join(ROOT, "spec/v2/kai_cdm_spec_v2.yaml"), encoding="utf-8"))["tables"]
PROFILES = yaml.safe_load(open(os.path.join(ROOT, "spec/v2/cohort_profiles_v2.yaml"), encoding="utf-8"))["cohorts"]

D = dt.date
# OMOP 표준 type concept — v1 과 같은 값을 쓴다.
EHR_TYPE = EHR
PERIOD_TYPE, DEATH_TYPE = 32817, 32817
# K-AI 어휘의 EPISODE 관련 씨앗 concept. vocab/CONCEPT.csv 의 key 로 찾는다.
SEED_KEYS = {"episode_disease": "EP_DISEASE", "episode_first": "EP_FIRST", "episode_recurrence": "EP_RECURRENCE",
             "episode_remission": "EP_REMISSION", "episode_regimen": "EP_REGIMEN", "episode_cycle": "EP_CYCLE",
             "field_condition": "F_CONDITION", "field_procedure": "F_PROCEDURE", "field_drug": "F_DRUG",
             "field_measurement": "F_MEASUREMENT", "field_episode": "F_EPISODE", "field_specimen": "F_SPECIMEN",
             "field_observation": "F_OBSERVATION"}


def _seed_concepts():
    """씨앗 concept_id 를 어휘에서 읽는다. 없으면 그 자리는 None 으로 두고 부른 쪽이 판단한다."""
    import csv
    path = os.path.join(ROOT, "spec/v2/vocab/CONCEPT.csv")
    by_key = {r["key"]: int(r["concept_id"]) for r in csv.DictReader(open(path, encoding="utf-8"))}
    out = {name: by_key.get(key) for name, key in SEED_KEYS.items()}
    missing = sorted(k for k, v in out.items() if v is None)
    if missing:
        raise KeyError(f"어휘에서 씨앗 concept 을 찾지 못했다: {missing} — spec/v2_omop_map.py 의 SEED_CONCEPTS 와 맞춰야 한다")
    return out, by_key


class CtxV2(CtxV1):
    """v1 Ctx 의 난수·환자·날짜 헬퍼를 물려받고, 기록하는 자리만 v2 로 바꾼다."""

    def __init__(self, cohort, seed=20260907, id_base=None):
        self.cohort = cohort
        self.profile = PROFILES[cohort]
        self.tables = list(self.profile["omop_tables"]) + list(self.profile["extension_tables"])
        self.ext_tables = list(self.profile["extension_tables"])
        import numpy as np
        self.rng = np.random.default_rng(seed)
        base = id_base if id_base is not None else (list(PROFILES).index(cohort) + 1) * 100000
        self.ids = defaultdict(lambda: base)
        self.rows = {t: [] for t in self.tables}
        self.persons = []
        self.today = D(2026, 9, 1)
        self.seeds, self.concept_by_key = _seed_concepts()
        self._cohort_definition_id = list(PROFILES).index(cohort) + 1

    # ---------------------------------------------------- 값 집합에서 concept 찾기
    def cs(self, concept_set, code):
        """값 집합의 코드를 K-AI concept_id 로 바꾼다. 없는 코드를 쓰면 바로 알려준다."""
        cid = self.concept_by_key.get(f"CS:{concept_set}:{code}")
        if cid is None:
            have = sorted(k.split(":")[2] for k in self.concept_by_key if k.startswith(f"CS:{concept_set}:"))
            raise KeyError(f"값 집합 {concept_set} 에 '{code}' 가 없다. 있는 값: {have}")
        return cid

    # ------------------------------------------------------------- 사람·기간
    def finalize_person(self, p):
        """PERSON 한 행 + 관찰기간 + (사망했으면) DEATH. v1 은 이 셋을 PERSON 에 몰아 넣었다."""
        self.rows["PERSON"].append(dict(
            person_id=p.person_id, gender_concept_id=p.gender, year_of_birth=p.birth.year,
            month_of_birth=p.birth.month, day_of_birth=p.birth.day, care_site_id=p.care_site,
            gender_source_value="M" if p.gender == MALE else "F"))
        end = p.death_date or self.today
        self.rows["OBSERVATION_PERIOD"].append(dict(
            observation_period_id=self.nid("OBSERVATION_PERIOD"), person_id=p.person_id,
            observation_period_start_date=p.obs_start, observation_period_end_date=end,
            period_type_concept_id=PERIOD_TYPE))
        if p.death_date:
            self.rows["DEATH"].append(dict(person_id=p.person_id, death_date=p.death_date,
                                           death_type_concept_id=DEATH_TYPE))
        self.rows["COHORT"].append(dict(
            cohort_definition_id=self._cohort_definition_id, subject_id=p.person_id,
            cohort_start_date=p.index_date, cohort_end_date=end))

    # ---------------------------------------------------------------- 방문
    def visit(self, p, start, kind=OUTPATIENT, los=0):
        vid = self.nid("VISIT_OCCURRENCE")
        end = self.days(start, los)
        self.rows["VISIT_OCCURRENCE"].append(dict(
            visit_occurrence_id=vid, person_id=p.person_id, visit_concept_id=kind,
            visit_start_date=start, visit_end_date=end, visit_type_concept_id=EHR_TYPE,
            visit_source_value="IP" if kind == INPATIENT else ("ER" if kind not in (OUTPATIENT, INPATIENT) else "OP")))
        p.visits.append((vid, start, end, kind))
        return vid

    # --------------------------------------------------------- OMOP 사건 행
    def condition(self, p, date, concept, vid=None, type_concept=EHR_TYPE, status=None, source=None):
        cid = self.nid("CONDITION_OCCURRENCE")
        self.rows["CONDITION_OCCURRENCE"].append(dict(
            condition_occurrence_id=cid, person_id=p.person_id, condition_concept_id=concept,
            condition_start_date=date, condition_type_concept_id=type_concept,
            condition_status_concept_id=status, visit_occurrence_id=vid, condition_source_value=source))
        return cid

    def procedure(self, p, date, concept, vid=None, source=None):
        pid = self.nid("PROCEDURE_OCCURRENCE")
        self.rows["PROCEDURE_OCCURRENCE"].append(dict(
            procedure_occurrence_id=pid, person_id=p.person_id, procedure_concept_id=concept,
            procedure_date=date, procedure_type_concept_id=EHR_TYPE, visit_occurrence_id=vid,
            procedure_source_value=source))
        return pid

    def measure(self, p, date, concept, value=None, vid=None, value_concept=None, unit=None, source=None):
        mid = self.nid("MEASUREMENT")
        self.rows["MEASUREMENT"].append(dict(
            measurement_id=mid, person_id=p.person_id, measurement_concept_id=concept,
            measurement_date=date, measurement_type_concept_id=EHR_TYPE, value_as_number=value,
            value_as_concept_id=value_concept, unit_concept_id=unit, visit_occurrence_id=vid,
            measurement_source_value=source))
        return mid

    def observation(self, p, date, concept, vid=None, value_number=None, value_concept=None,
                    value_string=None, unit=None, source=None):
        oid = self.nid("OBSERVATION")
        self.rows["OBSERVATION"].append(dict(
            observation_id=oid, person_id=p.person_id, observation_concept_id=concept,
            observation_date=date, observation_type_concept_id=EHR_TYPE, value_as_number=value_number,
            value_as_string=value_string, value_as_concept_id=value_concept, unit_concept_id=unit,
            visit_occurrence_id=vid, observation_source_value=source))
        return oid

    def drug(self, p, start, concept, days, vid=None, dose=None, quantity=None, source=None):
        did = self.nid("DRUG_EXPOSURE")
        self.rows["DRUG_EXPOSURE"].append(dict(
            drug_exposure_id=did, person_id=p.person_id, drug_concept_id=concept,
            drug_exposure_start_date=start, drug_exposure_end_date=self.days(start, days - 1),
            drug_type_concept_id=EHR_TYPE, quantity=quantity, days_supply=days, dose_unit_source_value=dose,
            visit_occurrence_id=vid, drug_source_value=source))
        return did

    def specimen(self, p, date, concept, vid=None, anatomic_site=None, source=None):
        sid = self.nid("SPECIMEN")
        self.rows["SPECIMEN"].append(dict(
            specimen_id=sid, person_id=p.person_id, specimen_concept_id=concept,
            specimen_type_concept_id=EHR_TYPE, specimen_date=date,
            anatomic_site_concept_id=anatomic_site, specimen_source_value=source))
        return sid

    def note(self, p, date, text, vid=None, note_type=44814637, note_class=36716164):
        nid_ = self.nid("NOTE")
        self.rows["NOTE"].append(dict(
            note_id=nid_, person_id=p.person_id, note_date=date, note_type_concept_id=note_type,
            note_class_concept_id=note_class, note_text=text, encoding_concept_id=32678,
            language_concept_id=4180186, visit_occurrence_id=vid))
        return nid_

    # ------------------------------------------------------ 에피소드(치료 묶음)
    def episode(self, p, start, end, concept, object_concept, number=None, parent=None):
        """항암요법 한 줄기(레지멘)나 질환 경과를 한 행으로 적는다."""
        eid = self.nid("EPISODE")
        self.rows["EPISODE"].append(dict(
            episode_id=eid, person_id=p.person_id, episode_concept_id=concept,
            episode_start_date=start, episode_end_date=end, episode_parent_id=parent,
            episode_number=number, episode_object_concept_id=object_concept,
            episode_type_concept_id=EHR_TYPE))
        return eid

    def episode_event(self, episode_id, event_id, field_concept):
        """에피소드에 사건(약물·진단 행)을 매단다. 같은 짝은 한 번만 적는다(PK 가 세 컬럼이다)."""
        key = (episode_id, event_id, field_concept)
        if key in getattr(self, "_ee_seen", set()):
            return
        self._ee_seen = getattr(self, "_ee_seen", set()) | {key}
        self.rows["EPISODE_EVENT"].append(dict(
            episode_id=episode_id, event_id=event_id, episode_event_field_concept_id=field_concept))

    # ------------------------------------------------------------ 확장 테이블
    def ext(self, table, p, vid=None, **fields):
        """K-AI 확장 테이블 한 행. 서식 하나가 대개 이 표 하나에 앉는다."""
        if table not in self.rows:
            raise KeyError(f"{self.cohort} 코호트에 {table} 이 없다 (프로필: {self.ext_tables})")
        pk = SPEC[table]["pk"]
        row = dict(person_id=p.person_id)
        if "visit_occurrence_id" in {f["name"] for f in SPEC[table]["fields"]}:
            row["visit_occurrence_id"] = vid
        row.update(fields)
        row[pk] = self.nid(table)
        self.rows[table].append(row)
        return row[pk]

    # ---------------------------------------------------------------- 쓰기
    def write(self, out_dir):
        os.makedirs(out_dir, exist_ok=True)
        counts = {}
        for t in self.tables:
            cols = [f["name"] for f in SPEC[t]["fields"]]
            rows = self.rows[t]
            unknown = {k for r in rows for k in r} - set(cols)
            if unknown:
                raise KeyError(f"{t} 에 명세에 없는 컬럼을 썼다: {sorted(unknown)}")
            df = pd.DataFrame(rows, columns=cols) if rows else pd.DataFrame(columns=cols)
            for c in cols:
                if c in df.columns:
                    df[c] = df[c].apply(fmt)
            df.to_csv(os.path.join(out_dir, f"{t}.csv"), index=False, encoding="utf-8")
            counts[t] = len(rows)
        return counts

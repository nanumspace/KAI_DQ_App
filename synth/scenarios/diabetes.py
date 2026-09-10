# -*- coding: utf-8 -*-
"""
당뇨병(제2형) 코호트 시나리오 (환자 여정 템플릿)

여정 개요
  1) 진단 외래(index): T2DM 진단 + 동반질환(고혈압/이상지질혈증/비만), HbA1c·공복혈당·지질·신기능·혈압·신체계측,
     안저검사, 흡연력 관찰, 초기 약제(metformin; HbA1c>=10 이면 metformin+insulin), 동반질환 약제(statin/ACEi)
  2) 3개월 간격 외래 추적(3~6년): 매 방문 HbA1c/공복혈당/혈압/체중/BMI, 연 1회 지질·간기능·신기능·안저검사,
     HbA1c > 8.0 이면 단계적 약제 강화(DPP-4/SU/SGLT2/TZD -> SGLT2/GLP-1 -> 기저인슐린), 매 방문 처방 갱신 + 경과기록(NOTE)
  3) 합병증: 일부 CKD, 허혈심장질환. SU/인슐린 사용자에서 저혈당 이상사례(ADVERSE_EVENT, drug_exposure_id 연결, antp_id NULL),
     grade 3 은 응급실 방문(9203). 일부 사망(사망 직전 입원).
  4) DIABETES 특화 테이블 = 핵심 테이블의 평면화 사본(결정 D-07). 환자 여정이 끝난 뒤 핵심 테이블 행을 그대로 복사해
     행을 만든다(외래 방문 1행, 검사 1행, 약물 1행, 진단 1행, 노트 1행, 처치/관찰/이상사례 키 행, 사망 1행).
     입원/응급실 방문은 DIABETES 행에서 참조하지 않는다(visit_occurrence_id NULL).
"""
from framework import *

# ---- concepts
T2DM = 201826
HTN, DLP, OBESITY, IHD, CKD, HYPO = 320128, 432867, 433736, 4185932, 46271022, 24609
METFORMIN, GLIMEPIRIDE, SITAGLIPTIN, EMPAGLIFLOZIN = 1503297, 1597756, 1580747, 45774435
INSULIN, PIOGLITAZONE, SEMAGLUTIDE = 1502905, 1584910, 1583722
ATORVASTATIN, LISINOPRIL = 1545958, 1308216
GLUCOSE_LOWERING = {METFORMIN, GLIMEPIRIDE, SITAGLIPTIN, EMPAGLIFLOZIN, INSULIN, PIOGLITAZONE, SEMAGLUTIDE}
A1C, FPG, CREA, EGFR, SBP, DBP = 3004410, 3004501, 3016723, 3049187, 3004249, 3012888
HT, WT, BMI, TG, HDL, LDL, AST, ALT = 3036277, 3025315, 3038553, 3022192, 3007070, 3028437, 3013721, 3006923
FUNDOSCOPY, SMOKING = 4179908, 4275495
NOTE_OPD, CLASS_PROGRESS = 44814645, 36716177
ROUTE_PO, ROUTE_SC = 4132161, 4142048

KCD = {T2DM: "E11.9", HTN: "I10", DLP: "E78.5", OBESITY: "E66.9", IHD: "I25.9", CKD: "N18.9", HYPO: "E16.2"}
COND_STATUS = {T2DM: (32902, "주진단")}          # 그 외는 부진단
MEAS_SRC = {A1C: "HBA1C", FPG: "FBS", CREA: "CREA", EGFR: "EGFR", SBP: "SBP", DBP: "DBP", HT: "HT", WT: "WT", BMI: "BMI",
            TG: "TG", HDL: "HDL", LDL: "LDL", AST: "AST", ALT: "ALT"}
# concept: (원내 약품코드, route concept, route source, 1일 투여횟수(None=주 1회), 용법)
DRUG_INFO = {
    METFORMIN: ("MET500", ROUTE_PO, "PO", 2, "1 tab PO bid with meals"),
    GLIMEPIRIDE: ("GLM2", ROUTE_PO, "PO", 1, "1 tab PO qd before breakfast"),
    SITAGLIPTIN: ("SIT100", ROUTE_PO, "PO", 1, "1 tab PO qd"),
    EMPAGLIFLOZIN: ("EMP10", ROUTE_PO, "PO", 1, "1 tab PO qd"),
    PIOGLITAZONE: ("PIO15", ROUTE_PO, "PO", 1, "1 tab PO qd"),
    INSULIN: ("GLA100", ROUTE_SC, "SC", 1, "20 IU SC at bedtime, titrate by FBS"),
    SEMAGLUTIDE: ("SEMA1", ROUTE_SC, "SC", None, "1 mg SC once weekly"),
    ATORVASTATIN: ("ATV20", ROUTE_PO, "PO", 1, "1 tab PO at bedtime"),
    LISINOPRIL: ("LIS10", ROUTE_PO, "PO", 1, "1 tab PO qd"),
}
DRUG_LABEL = {METFORMIN: "metformin 500 mg bid", GLIMEPIRIDE: "glimepiride 2 mg qd", SITAGLIPTIN: "sitagliptin 100 mg qd",
              EMPAGLIFLOZIN: "empagliflozin 10 mg qd", PIOGLITAZONE: "pioglitazone 15 mg qd", INSULIN: "insulin glargine 20 IU qhs",
              SEMAGLUTIDE: "semaglutide 1 mg weekly", ATORVASTATIN: "atorvastatin 20 mg qhs", LISINOPRIL: "lisinopril 10 mg qd"}


def _ts(d, h, m=0):
    """timestamp 문자열(YYYY-MM-DD HH:MM:SS). datetime 객체로 두면 NULL 이 섞인 컬럼이 pandas 에서 NaT 가 되어
    framework.fmt 가 실패하므로(NaT.strftime 미지원) 문자열로 만든다."""
    return dt.datetime(d.year, d.month, d.day, h, m, 0).strftime("%Y-%m-%d %H:%M:%S")


def generate(ctx: Ctx, n=100):
    for _ in range(n):
        start_idx = {t: len(ctx.rows[t]) for t in ctx.tables}
        gender = FEMALE if ctx.bern(0.45) else MALE
        age = int(ctx.normal(58, 11, 30, 85, 0))
        index = D(2018, 1, 1) + dt.timedelta(days=ctx.randint(0, 365 * 6 - 1))
        p = ctx.person(gender, age, index)
        # 환자 불변 필드: person / care_site / org 그룹 (anchor 없는 그룹) -> 모든 DIABETES 행에 자동 복사
        p.patient_fields = dict(
            gender_concept_id=gender, year_of_birth=p.birth.year, month_of_birth=p.birth.month, day_of_birth=p.birth.day,
            birth_datetime=_ts(p.birth, 0, 0), location_id=ctx.randint(1, 50), person_source_value=f"P{p.person_id}",
            gender_source_value="M" if gender == MALE else "F", gender_source_concept_id=0,
            care_site_id=1, care_site_name="KAI University Hospital", place_of_service_concept_id=8756,
            care_site_source_value="H001", place_of_service_source_value="Outpatient Hospital",
            medical_dept="ENDO", ward_cd="OPD", hsp_tp_cd="01", antp_id=None)
        _journey(ctx, p)
        ctx.finalize_person(p)
        _mirror(ctx, p, start_idx)


# ------------------------------------------------------------------ journey
def _journey(ctx, p):
    index = p.index_date
    male = p.gender == MALE
    ht = ctx.normal(171 if male else 158, 6, 145, 195)
    bmi = ctx.normal(26.5, 3.5, 18, 42)
    wt = round(bmi * (ht / 100) ** 2, 1)
    a1c = ctx.normal(7.6, 1.4, 5.8, 13.5)
    base_a1c = a1c
    smoker = ctx.bern(0.45 if male else 0.08)
    cur_smok = smoker and ctx.bern(0.6)
    has_htn, has_dlp = ctx.bern(0.55), ctx.bern(0.6)
    obese = bmi >= 25 and ctx.bern(0.7)
    ckd_at = ctx.randint(8, 20) if ctx.bern(0.15) else None       # 방문 번호
    ihd_at = ctx.randint(4, 20) if ctx.bern(0.10) else None
    ckd_on = False
    # 약제 강화 사다리 (환자별)
    second = ctx.choice([SITAGLIPTIN, GLIMEPIRIDE, EMPAGLIFLOZIN, PIOGLITAZONE], p=[0.4, 0.25, 0.25, 0.1])
    ladder = [second] + [d for d in (EMPAGLIFLOZIN, SEMAGLUTIDE) if d != second] + [INSULIN]
    regimen = [METFORMIN]
    if a1c >= 10.0:
        regimen.append(INSULIN); ladder.remove(INSULIN)
    if has_dlp: regimen.append(ATORVASTATIN)
    if has_htn: regimen.append(LISINOPRIL)
    last_rx = {}                                                  # concept -> 최근 drug_exposure_id
    n_visits = ctx.randint(12, 24)
    cur = index
    k = 0
    visit_dates = []
    while k < n_visits and cur <= ctx.today:
        vid = ctx.visit(p, cur, OUTPATIENT)
        visit_dates.append(cur)
        annual = (k % 4 == 0)
        new_dx = []
        if k == 0:
            ctx.condition(p, cur, T2DM, vid=vid)
            for c, flag in ((HTN, has_htn), (DLP, has_dlp), (OBESITY, obese)):
                if flag: ctx.condition(p, cur, c, vid=vid); new_dx.append(c)
            ctx.observation(p, cur, SMOKING, vid=vid, value_string="Current smoker" if cur_smok else ("Ex-smoker" if smoker else "Never smoker"))
            ctx.measure(p, cur, HT, ht, vid=vid)
        if ckd_at is not None and k == ckd_at:
            ctx.condition(p, cur, CKD, vid=vid); new_dx.append(CKD); ckd_on = True
            if METFORMIN in regimen: regimen.remove(METFORMIN)
        if ihd_at is not None and k == ihd_at:
            ctx.condition(p, cur, IHD, vid=vid); new_dx.append(IHD)
            if ATORVASTATIN not in regimen: regimen.append(ATORVASTATIN)
        # ---- 검사
        if k > 0:
            n_gl = len([d for d in regimen if d in GLUCOSE_LOWERING])
            target = base_a1c - 0.9 * n_gl + 0.03 * k
            a1c = max(5.0, min(14.0, round(a1c + 0.5 * (target - a1c) + float(ctx.rng.normal(0, 0.35)), 1)))
            wt = round(max(35.0, wt + float(ctx.rng.normal(-0.3 if any(d in regimen for d in (EMPAGLIFLOZIN, SEMAGLUTIDE)) else 0.1, 1.0))), 1)
            bmi = round(wt / (ht / 100) ** 2, 1)
        fpg = ctx.normal(a1c * 25 - 45, 15, 60, 400, 0)
        sbp = ctx.normal(138 if has_htn else 124, 12, 90, 200, 0)
        dbp = ctx.normal(84 if has_htn else 76, 8, 50, 120, 0)
        ctx.measure(p, cur, A1C, a1c, vid=vid)
        ctx.measure(p, cur, FPG, fpg, vid=vid)
        ctx.measure(p, cur, SBP, sbp, vid=vid); ctx.measure(p, cur, DBP, dbp, vid=vid)
        ctx.measure(p, cur, WT, wt, vid=vid); ctx.measure(p, cur, BMI, bmi, vid=vid)
        labs = {}
        if annual:
            shifts = {TG: 40 if has_dlp else 0, LDL: (30 if has_dlp else 0) - (25 if ATORVASTATIN in regimen else 0),
                      CREA: 0.9 if ckd_on else 0.0, EGFR: -45 if ckd_on else 0}
            labs = ctx.labs(p, cur, [TG, HDL, LDL, AST, ALT, CREA, EGFR], vid=vid, shifts=shifts)
            ctx.procedure(p, cur, FUNDOSCOPY, vid=vid)
        # ---- 약제 강화
        added = None
        if k > 0 and a1c > 8.0 and ladder and ctx.bern(0.7):
            added = ladder.pop(0); regimen.append(added)
        # ---- 처방
        days = ctx.choice([30, 60, 90]) if k == 0 else 90
        for c in regimen:
            last_rx[c] = _rx(ctx, p, cur, c, days, vid)
        # ---- 경과기록
        ctx.note(p, cur, _note_text(k, a1c, fpg, sbp, dbp, bmi, regimen, added, new_dx, labs, cur_smok, smoker),
                 note_type=NOTE_OPD, note_class=CLASS_PROGRESS, vid=vid)
        # ---- 저혈당 이상사례 (SU/인슐린 사용자)
        culprit = INSULIN if INSULIN in regimen else (GLIMEPIRIDE if GLIMEPIRIDE in regimen else None)
        if culprit and ctx.bern(0.10):
            ae_day = ctx.days(cur, ctx.randint(10, 60))
            if ae_day <= ctx.today:
                grade = ctx.choice([1, 2, 3], p=[0.5, 0.3, 0.2])
                avid = ctx.visit(p, ae_day, ER if grade >= 3 else OUTPATIENT)
                ctx.measure(p, ae_day, FPG, ctx.normal(42 if grade >= 3 else 58, 7, 25, 69, 0), vid=avid)
                ctx.ae(p, ae_day, HYPO, grade, vid=avid, drug_exposure_id=last_rx[culprit], causality=2, action=2 if grade >= 2 else 1)
                ctx.condition(p, ae_day, HYPO, vid=avid)
                ctx.note(p, ae_day, f"{'ER' if grade >= 3 else 'Unscheduled OPD'} visit for hypoglycemia (CTCAE grade {grade}) on "
                         f"{CONCEPTS['drugs'][culprit]['name']}. Glucose {ctx.rows['MEASUREMENT'][-1]['value_as_number']} mg/dL, "
                         f"{'IV dextrose given, observed and discharged' if grade >= 3 else 'oral carbohydrate, recovered'}. "
                         f"{'Dose reduced.' if grade >= 2 else 'Education on hypoglycemia reinforced.'}",
                         note_type=NOTE_OPD, note_class=CLASS_PROGRESS, vid=avid)
                if grade >= 2 and culprit == GLIMEPIRIDE and ctx.bern(0.5):
                    regimen.remove(GLIMEPIRIDE)
                    if SITAGLIPTIN not in regimen: regimen.append(SITAGLIPTIN)
        cur = ctx.days(cur, ctx.randint(84, 98)); k += 1
    # ---- 사망 (추적이 충분한 환자 중 일부, 사망 직전 입원)
    last = visit_dates[-1]
    p_death = 0.06 if (ihd_at is not None or ckd_on or p.age_on(last) >= 72) else 0.015
    if k >= 8 and ctx.bern(p_death):
        dd = ctx.days(last, ctx.randint(5, 50))
        if dd.year != last.year:
            dd = D(last.year, 12, 31)
        if dd > ctx.today:
            dd = ctx.today
        if dd > last:
            adm = ctx.days(dd, -2) if ctx.days(dd, -2) > last else dd
            ctx.set_death(p, dd)
            ctx.visit(p, adm, INPATIENT, los=(dd - adm).days)
            for r in ctx.rows["DRUG_EXPOSURE"]:
                if r["person_id"] == p.person_id and r["drug_exposure_end_date"] > dd:
                    r["drug_exposure_end_date"] = dd
                    r["days_supply"] = (dd - r["drug_exposure_start_date"]).days + 1
                    if r["dosing_number"] is not None:
                        r["dosing_number"] = max(1, r["days_supply"] // 7)
            p.cause = (4185932, "I25.9") if ihd_at is not None else ((46271022, "N18.9") if ckd_on else (4185932, "I25.9"))


def _rx(ctx, p, date, concept, days, vid):
    days = int(min(days, (ctx.today - date).days + 1))
    _, _, _, freq, _ = DRUG_INFO[concept]
    if freq is None:                                              # 주 1회 (semaglutide)
        number = max(1, days // 7)
        did, _ = ctx.drug(p, date, concept, days, vid=vid, quantity=number, interval=7, number=number)
    else:
        did, _ = ctx.drug(p, date, concept, days, vid=vid, freq=freq, quantity=days * freq)
    return did


def _note_text(k, a1c, fpg, sbp, dbp, bmi, regimen, added, new_dx, labs, cur_smok, smoker):
    names = {T2DM: "type 2 diabetes mellitus", HTN: "hypertension", DLP: "dyslipidemia", OBESITY: "obesity", CKD: "chronic kidney disease", IHD: "ischemic heart disease"}
    meds = ", ".join(DRUG_LABEL[c] for c in regimen)
    if k == 0:
        smk = "current smoker" if cur_smok else ("ex-smoker" if smoker else "never smoker")
        s = (f"Endocrinology initial visit. Newly diagnosed type 2 diabetes mellitus. HbA1c {a1c}%, FBS {fpg} mg/dL, BP {sbp}/{dbp} mmHg, BMI {bmi} kg/m2, {smk}. "
             + (f"Comorbidity: {', '.join(names[c] for c in new_dx)}. " if new_dx else ""))
    else:
        ctrl = "at goal" if a1c < 7.0 else ("suboptimal" if a1c <= 8.0 else "poor")
        s = f"Endocrinology follow-up (visit {k + 1}). T2DM, glycemic control {ctrl}: HbA1c {a1c}%, FBS {fpg} mg/dL. BP {sbp}/{dbp} mmHg, BMI {bmi} kg/m2. "
        if new_dx: s += f"New diagnosis: {', '.join(names[c] for c in new_dx)}. "
    if labs:
        s += f"Labs: LDL {labs[LDL]}, HDL {labs[HDL]}, TG {labs[TG]} mg/dL; AST/ALT {labs[AST]}/{labs[ALT]} U/L; Cr {labs[CREA]} mg/dL, eGFR {labs[EGFR]}. Fundoscopy done. "
    s += f"Plan: {'start ' + DRUG_LABEL[added] + '; ' if added else ''}continue {meds}. Lifestyle counseling, f/u 3 months."
    return s


# ------------------------------------------------------------- DIABETES rows
def _mirror(ctx, p, start_idx):
    """환자 여정이 만든 핵심 테이블 행을 DIABETES 행으로 복사 (외래 방문만 참조)."""
    kind = {vid: kd for vid, s, e, kd in p.visits}
    link = lambda vid: vid if kind.get(vid) == OUTPATIENT else None
    rows = lambda t: ctx.rows[t][start_idx[t]:]
    provider = ctx.randint(1, 30)
    prev = None
    for r in sorted(rows("VISIT_OCCURRENCE"), key=lambda r: (r["visit_start_date"], r["visit_occurrence_id"])):
        if r["visit_concept_id"] != OUTPATIENT:
            continue
        s = r["visit_start_date"]
        ctx.disease_row(p, r["visit_occurrence_id"], visit_concept_id=OUTPATIENT, visit_start_date=s, visit_start_datetime=_ts(s, 9, 0),
                        visit_end_date=r["visit_end_date"], visit_end_datetime=_ts(r["visit_end_date"], 11, 30), visit_type_concept_id=EHR,
                        visit_source_value="O", visit_source_concept_id=0, provider_id=provider, preceding_visit_occurrence_id=prev)
        prev = r["visit_occurrence_id"]
    for r in rows("CONDITION_OCCURRENCE"):
        c = r["condition_concept_id"]; d = r["condition_start_date"]
        status, status_src = COND_STATUS.get(c, (32908, "부진단"))
        ctx.disease_row(p, link(r["visit_occurrence_id"]), condition_occurrence_id=r["condition_occurrence_id"], condition_concept_id=c,
                        condition_start_date=d, condition_start_datetime=_ts(d, 9, 30), condition_type_concept_id=r["condition_type_concept_id"],
                        condition_status_concept_id=status, condition_status_source_value=status_src,
                        condition_source_value=KCD.get(c), condition_source_concept_id=0)
    for r in rows("MEASUREMENT"):
        d = r["measurement_date"]; c = r["measurement_concept_id"]
        ctx.disease_row(p, link(r["visit_occurrence_id"]), measurement_id=r["measurement_id"], measurement_concept_id=c, measurement_date=d,
                        measurement_datetime=_ts(d, 9, 15), measurement_time="09:15", measurement_type_concept_id=r["measurement_type_concept_id"],
                        operator_concept_id=4172703, value_as_number=r["value_as_number"], value_as_concept_id=r["value_as_concept_id"],
                        unit_concept_id=r["unit_concept_id"], range_low=r["range_low"], range_high=r["range_high"],
                        measurement_source_value=MEAS_SRC.get(c, str(c)), measurement_source_concept_id=0,
                        unit_source_value=r["unit_source_value"], value_source_value=r["value_source_value"])
    for r in rows("DRUG_EXPOSURE"):
        c = r["drug_concept_id"]; s = r["drug_exposure_start_date"]; e = r["drug_exposure_end_date"]
        src, route, route_src, freq, sig = DRUG_INFO[c]
        ctx.disease_row(p, link(r["visit_occurrence_id"]), drug_exposure_id=r["drug_exposure_id"], drug_concept_id=c,
                        drug_exposure_start_date=s, drug_exposure_start_datetime=_ts(s, 10, 0), drug_exposure_end_date=e,
                        drug_exposure_end_datetime=_ts(e, 23, 59), verbatim_end_date=e, drug_type_concept_id=EHR, refills=0,
                        amount_value=r["amount_value"], amount_unit_concept_id=r["amount_unit_concept_id"], quantity=r["quantity"],
                        days_supply=r["days_supply"], sig=sig, route_concept_id=route, drug_source_value=src, drug_source_concept_id=0,
                        route_source_value=route_src, dose_unit_source_value=CONCEPTS["drugs"][c]["dose_unit_label"],
                        drug_note_mapping=(f"SMILES note_id={r['note_id']}" if r["note_id"] else None), note_id=r["note_id"])
    for r in rows("NOTE"):
        ctx.disease_row(p, link(r["visit_occurrence_id"]), note_id=r["note_id"], note_date=r["note_date"],
                        note_type_concept_id=r["note_type_concept_id"], note_text=r["note_text"])
    for r in rows("PROCEDURE_OCCURRENCE"):
        ctx.disease_row(p, link(r["visit_occurrence_id"]), procedure_occurrence_id=r["procedure_occurrence_id"])
    for r in rows("OBSERVATION"):
        ctx.disease_row(p, link(r["visit_occurrence_id"]), observation_id=r["observation_id"])
    for r in rows("ADVERSE_EVENT"):
        ctx.disease_row(p, link(r["visit_occurrence_id"]), adverse_event_id=r["adverse_event_id"], drug_exposure_id=r["drug_exposure_id"])
    if p.death_date is not None:
        cause, cause_src = getattr(p, "cause", (4185932, "I25.9"))
        ctx.disease_row(p, None, death_date=p.death_date, death_datetime=_ts(p.death_date, 6, 40), death_type_concept_id=EHR,
                        cause_concept_id=cause, cause_source_value=cause_src, cause_source_concept_id=0)

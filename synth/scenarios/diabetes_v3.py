# -*- coding: utf-8 -*-
"""
당뇨병(제2형) 코호트 시나리오 (v3)

v1 `diabetes.py` 의 환자 여정을 v3 테이블로 옮겼다. DIABETES 특화 테이블은 환자당 1행(진단 외래 방문)이며
condition_start_date = 진단일(index), condition_end_date 는 진행 중이면 비운다(관해 사례 일부만 채움).

여정: 진단 외래(T2DM + 동반질환, 검사, 안저검사, 초기 약제) → 3개월 간격 추적 3~6년(HbA1c 에 따른 단계적 약제 강화,
연 1회 지질·간기능·신기능, 합병증 CKD/IHD, SU/인슐린 저혈당 이상사례, 일부 사망).
이 코호트에는 SACT 가 없으므로 DRUG_EXPOSURE.sact_id 는 항상 비어 있다.
"""
from framework_v3 import *

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

FREQ = {METFORMIN: 2, GLIMEPIRIDE: 1, SITAGLIPTIN: 1, EMPAGLIFLOZIN: 1, PIOGLITAZONE: 1, INSULIN: 1, SEMAGLUTIDE: None,
        ATORVASTATIN: 1, LISINOPRIL: 1}   # None = 주 1회
DRUG_LABEL = {METFORMIN: "metformin 500 mg bid", GLIMEPIRIDE: "glimepiride 2 mg qd", SITAGLIPTIN: "sitagliptin 100 mg qd",
              EMPAGLIFLOZIN: "empagliflozin 10 mg qd", PIOGLITAZONE: "pioglitazone 15 mg qd", INSULIN: "insulin glargine 20 IU qhs",
              SEMAGLUTIDE: "semaglutide 1 mg weekly", ATORVASTATIN: "atorvastatin 20 mg qhs", LISINOPRIL: "lisinopril 10 mg qd"}


def generate(ctx: CtxV3, n=100):
    for _ in range(n):
        gender = FEMALE if ctx.bern(0.45) else MALE
        age = int(ctx.normal(58, 11, 30, 85, 0))
        index = D(2018, 1, 1) + dt.timedelta(days=ctx.randint(0, 365 * 6 - 1))
        p = ctx.person(gender, age, index)
        _journey(ctx, p)
        ctx.finalize_person(p)


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
    second = ctx.choice([SITAGLIPTIN, GLIMEPIRIDE, EMPAGLIFLOZIN, PIOGLITAZONE], p=[0.4, 0.25, 0.25, 0.1])
    ladder = [second] + [d for d in (EMPAGLIFLOZIN, SEMAGLUTIDE) if d != second] + [INSULIN]
    regimen = [METFORMIN]
    if a1c >= 10.0:
        regimen.append(INSULIN); ladder.remove(INSULIN)
    if has_dlp: regimen.append(ATORVASTATIN)
    if has_htn: regimen.append(LISINOPRIL)
    n_visits = ctx.randint(12, 24)
    cur = index
    k = 0
    visit_dates = []
    row = None
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
            row = ctx.disease_row(p, vid, condition_start_date=index, condition_end_date=None)
        if ckd_at is not None and k == ckd_at:
            ctx.condition(p, cur, CKD, vid=vid); new_dx.append(CKD); ckd_on = True
            if METFORMIN in regimen: regimen.remove(METFORMIN)
        if ihd_at is not None and k == ihd_at:
            ctx.condition(p, cur, IHD, vid=vid); new_dx.append(IHD)
            if ATORVASTATIN not in regimen: regimen.append(ATORVASTATIN)
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
        added = None
        if k > 0 and a1c > 8.0 and ladder and ctx.bern(0.7):
            added = ladder.pop(0); regimen.append(added)
        days = ctx.choice([30, 60, 90]) if k == 0 else 90
        for c in regimen:
            _rx(ctx, p, cur, c, days, vid)
        ctx.note(p, cur, _note_text(k, a1c, fpg, sbp, dbp, bmi, regimen, added, new_dx, labs, cur_smok, smoker),
                 note_type=NOTE_OPD, note_class=CLASS_PROGRESS, vid=vid)
        # 저혈당 이상사례 (SU/인슐린 사용자)
        culprit = INSULIN if INSULIN in regimen else (GLIMEPIRIDE if GLIMEPIRIDE in regimen else None)
        if culprit and ctx.bern(0.10):
            ae_day = ctx.days(cur, ctx.randint(10, 60))
            if ae_day <= ctx.today:
                grade = ctx.choice([1, 2, 3], p=[0.5, 0.3, 0.2])
                avid = ctx.visit(p, ae_day, ER if grade >= 3 else OUTPATIENT)
                ctx.measure(p, ae_day, FPG, ctx.normal(42 if grade >= 3 else 58, 7, 25, 69, 0), vid=avid)
                ctx.ae(p, ae_day, HYPO, grade, vid=avid, causality=2, action=2 if grade >= 2 else 1)
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
    last = visit_dates[-1]
    # ---- 관해 (소수; 마지막 방문 이후가 아니라 추적 중 한 방문일을 종료일로)
    if len(visit_dates) >= 8 and ctx.bern(0.04):
        row["condition_end_date"] = visit_dates[ctx.randint(len(visit_dates) // 2, len(visit_dates) - 1)]
    # ---- 사망 (추적이 충분한 환자 중 일부, 사망 직전 입원)
    p_death = 0.06 if (ihd_at is not None or ckd_on or p.age_on(last) >= 72) else 0.015
    if k >= 8 and ctx.bern(p_death):
        dd = ctx.days(last, ctx.randint(5, 50))
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
                        r["quantity"] = r["dosing_number"]
                    elif r["quantity"] is not None:
                        r["quantity"] = r["days_supply"] * (r["frequency_per_day"] or 1)


def _rx(ctx, p, date, concept, days, vid):
    days = int(min(days, (ctx.today - date).days + 1))
    freq = FREQ[concept]
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

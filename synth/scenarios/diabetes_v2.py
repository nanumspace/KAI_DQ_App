# -*- coding: utf-8 -*-
"""당뇨병(제2형) 코호트 시나리오 (v2 저장 구조).

v1 과 여정은 같다. 달라지는 것은 적는 자리다.

  v1 의 DIABETES 특화 테이블은 코어 테이블의 평면화 사본이었다(결정 D-07). v2 는 그것을 두지 않는다.
  대신 DIABETES_BASELINE(CGM·인슐린펌프)과 DIABETES_EVENT(합병증)처럼 EHR 에서 그대로 뽑히지 않는
  것만 확장 테이블로 받고, 나머지는 OMOP 테이블에 그대로 앉는다.

여정
  1) 진단 외래: T2DM 진단과 동반질환, HbA1c·공복혈당·지질·신기능·혈압·신체계측, 안저검사, 흡연 관찰, 첫 약제
  2) 3개월 간격 외래(3~6년): 매번 HbA1c·혈압·체중, 해마다 지질·신기능·안저. HbA1c 가 높으면 약을 더한다
  3) 합병증 평가(해마다): 신장·망막·신경·발. DIABETES_EVENT 한 행
  4) 저혈당 이상사례, 일부 사망
"""
import datetime as dt

from framework_v2 import D, FEMALE, INPATIENT, MALE, OUTPATIENT, CtxV2

T2DM, HTN, DLP, OBESITY, IHD, CKD, HYPO = 201826, 320128, 432867, 433736, 4185932, 46271022, 24609
METFORMIN, GLIMEPIRIDE, SITAGLIPTIN, EMPAGLIFLOZIN = 1503297, 1597756, 1580747, 45774435
INSULIN, SEMAGLUTIDE, ATORVASTATIN, LISINOPRIL = 1502905, 1583722, 1545958, 1308216
A1C, FPG, CREA, EGFR, SBP, DBP = 3004410, 3004501, 3016723, 3049187, 3004249, 3012888
HT, WT, BMI, TG, HDL, LDL = 3036277, 3025315, 3038553, 3022192, 3007070, 3028437
FUNDOSCOPY, SMOKING = 4179908, 4275495
LADDER = [SITAGLIPTIN, EMPAGLIFLOZIN, SEMAGLUTIDE, INSULIN]

NOTE_TXT = ("외래 경과기록. HbA1c {a1c}%, 공복혈당 {fpg} mg/dL, 혈압 {sbp}/{dbp} mmHg, 체중 {wt} kg. "
            "현재 약제: {drugs}. 계획: {plan}")


def generate(ctx: CtxV2, n=100):
    for _ in range(n):
        gender = FEMALE if ctx.bern(0.45) else MALE
        age = int(ctx.normal(58, 11, 25, 88, 0))
        index = D(2019, 1, 1) + dt.timedelta(days=ctx.randint(0, 365 * 4))
        p = ctx.person(gender, age, index)
        a1c = ctx.normal(8.6, 1.6, 6.5, 14.0)
        cgm = ctx.bern(0.15)
        pump = cgm and ctx.bern(0.2)
        # 사망은 여정을 적기 전에 정한다. 뒤에서 정하면 앞서 적은 사건이 사망일 뒤에 남는다.
        if ctx.bern(0.06):
            d = ctx.days(index, ctx.randint(500, 365 * 6))
            if d <= ctx.today:
                ctx.set_death(p, d)

        # ---- 1) 진단 외래
        vid = ctx.visit(p, index, OUTPATIENT)
        dx = ctx.condition(p, index, T2DM, vid=vid, source="E11.9")
        ep = ctx.episode(p, index, None, ctx.seeds["episode_disease"], T2DM)
        ctx.episode_event(ep, dx, ctx.seeds["field_condition"])
        for c, src, prob in ((HTN, "I10", 0.55), (DLP, "E78.5", 0.6), (OBESITY, "E66.9", 0.35)):
            if ctx.bern(prob):
                ctx.condition(p, index, c, vid=vid, source=src)

        ht = ctx.normal(170 if gender == MALE else 157, 6, 145, 190)
        wt = ctx.normal(74 if gender == MALE else 64, 12, 40, 130)
        bmi = round(wt / (ht / 100) ** 2, 1)
        sbp, dbp = ctx.normal(132, 14, 95, 190, 0), ctx.normal(80, 9, 55, 115, 0)
        for concept, val in ((A1C, a1c), (FPG, ctx.normal(160, 40, 80, 350, 0)), (HT, ht), (WT, wt), (BMI, bmi),
                             (SBP, sbp), (DBP, dbp), (CREA, ctx.normal(0.9, 0.25, 0.4, 3.0, 2)),
                             (EGFR, ctx.normal(88, 20, 12, 130, 0)), (TG, ctx.normal(170, 70, 50, 500, 0)),
                             (HDL, ctx.normal(47, 11, 20, 90, 0)), (LDL, ctx.normal(115, 32, 40, 240, 0))):
            ctx.measure(p, index, concept, val, vid=vid)
        ctx.procedure(p, index, FUNDOSCOPY, vid=vid, source="FUNDUS")
        ctx.observation(p, index, SMOKING, vid=vid,
                        value_string="Current smoker" if ctx.bern(0.22) else "Never smoker")

        # 등록 서식으로만 받는 것 — CGM·인슐린펌프 사용
        ctx.ext("DIABETES_BASELINE", p, vid=vid, record_date=index,
                cgm_use_yn=1 if cgm else 0, insulin_pump_yn=1 if pump else 0)
        if ctx.bern(0.3):       # 1형 감별을 위한 항체검사
            ctx.ext("BIOMARKER", p, vid=vid, test_date=index,
                    gad_antibody_result_concept_id=ctx.cs("BIOMARKER_RESULT", "음성"),
                    gad_antibody_result_source_value="negative")

        drugs = [METFORMIN] + ([INSULIN] if a1c >= 10 else [])
        for d in drugs:
            ctx.drug(p, index, d, days=90, vid=vid, source="초기 약제")
        if ctx.bern(0.5):
            ctx.drug(p, index, ATORVASTATIN, days=90, vid=vid, source="이상지질혈증")
        if ctx.bern(0.4):
            ctx.drug(p, index, LISINOPRIL, days=90, vid=vid, source="고혈압")

        # ---- 2) 3개월 간격 추적
        years = ctx.randint(3, 6)
        cur_a1c = a1c
        for k in range(1, years * 4 + 1):
            day = ctx.days(index, 91 * k)
            if day > ctx.today or (p.death_date and day > p.death_date):
                break
            v = ctx.visit(p, day, OUTPATIENT)
            cur_a1c = round(max(5.6, min(14.0, cur_a1c - ctx.rand(-0.4, 0.7))), 1)
            wt = round(max(40.0, wt + ctx.rand(-1.5, 1.2)), 1)
            sbp = ctx.normal(130, 12, 95, 185, 0)
            dbp = ctx.normal(79, 8, 55, 110, 0)
            fpg = ctx.normal(140, 35, 70, 320, 0)
            for concept, val in ((A1C, cur_a1c), (FPG, fpg), (WT, wt),
                                 (BMI, round(wt / (ht / 100) ** 2, 1)), (SBP, sbp), (DBP, dbp)):
                ctx.measure(p, day, concept, val, vid=v)
            if k % 4 == 0:                     # 해마다
                for concept, val in ((CREA, ctx.normal(1.0, 0.3, 0.4, 4.0, 2)), (EGFR, ctx.normal(80, 22, 10, 130, 0)),
                                     (TG, ctx.normal(165, 65, 50, 480, 0)), (HDL, ctx.normal(48, 11, 20, 90, 0)),
                                     (LDL, ctx.normal(105, 30, 40, 230, 0))):
                    ctx.measure(p, day, concept, val, vid=v)
                ctx.procedure(p, day, FUNDOSCOPY, vid=v, source="FUNDUS")
                _complication_row(ctx, p, v, day, cur_a1c, years)
            if cur_a1c > 8.0 and len(drugs) < 5:
                nxt = next((d for d in LADDER if d not in drugs), None)
                if nxt:
                    drugs.append(nxt)
            for d in drugs:
                did = ctx.drug(p, day, d, days=91, vid=v, source="지속 처방")
                if d in (GLIMEPIRIDE, INSULIN) and ctx.bern(0.05):     # 저혈약제의 저혈당
                    hd = ctx.days(day, ctx.randint(5, 80))
                    if hd <= ctx.today and not (p.death_date and hd > p.death_date):
                        hv = ctx.visit_on(p, hd)
                        hyp = ctx.condition(p, hd, HYPO, vid=hv, source="E16.2")
                        ctx.episode_event(ep, hyp, ctx.seeds["field_condition"])
                        ctx.episode_event(ep, did, ctx.seeds["field_drug"])
            ctx.note(p, day, NOTE_TXT.format(a1c=cur_a1c, fpg=fpg, sbp=sbp, dbp=dbp, wt=wt,
                                             drugs=len(drugs), plan="약제 유지" if cur_a1c <= 7.5 else "약제 강화"),
                     vid=v)

        ctx.finalize_person(p)


def _complication_row(ctx, p, vid, day, a1c, years):
    """해마다 합병증을 훑는다. v1 에는 없던 자리로, v2 가 등록 서식으로 새로 받는 항목이다."""
    severe = a1c > 9.0
    ckd = ctx.choice(["G1", "G2", "G3a", "G3b", "G4"], p=[0.45, 0.3, 0.13, 0.08, 0.04])
    dr = ctx.choice(["없음", "경증_NPDR", "중등도_NPDR", "중증_NPDR", "PDR"], p=[0.55, 0.2, 0.12, 0.08, 0.05])
    foot = ctx.bern(0.06 if severe else 0.02)
    ctx.ext("DIABETES_EVENT", p, vid=vid, event_date=day,
            hba1c_target_met_yn=1 if a1c <= 7.0 else 0,
            severe_hypoglycemia_count=ctx.randint(0, 2) if severe else 0,
            hypoglycemia_unawareness_yn=1 if ctx.bern(0.07) else 0,
            ckd_stage_concept_id=ctx.cs("CKD_STAGE", ckd), ckd_stage_source_value=ckd,
            dka_yn=1 if ctx.bern(0.02) else 0,
            retinopathy_severity_concept_id=ctx.cs("DR_SEVERITY", dr), retinopathy_severity_source_value=dr,
            macular_edema_yn=1 if ctx.bern(0.05) else 0,
            peripheral_neuropathy_yn=1 if ctx.bern(0.25 if severe else 0.12) else 0,
            foot_ulcer_yn=1 if foot else 0,
            cardiac_autonomic_neuropathy_yn=1 if ctx.bern(0.05) else 0,
            charcot_foot_yn=1 if (foot and ctx.bern(0.1)) else 0)

# -*- coding: utf-8 -*-
"""
대사이상지방간(MASLD) 코호트 시나리오 (v3)

v1 `masld.py` 의 환자 여정을 v3 테이블로 옮겼다. MASLD 특화 테이블은 환자당 1행(진단 외래 방문)이고
섬유화 지표만 담는다(fib4/apri/bard/safe/liverrisk). 점수는 진단일 같은 날 기록한 AST/ALT/혈소판/BMI/당뇨 여부와
진단 시점 나이로 산출한 값이다.

여정: 진단 외래(초음파, 동반질환, 신체계측, 혈액검사, 생활습관) → 1개월 FibroScan(일부 간생검) → 6개월 간격 추적 2~5년
(체중 변화, 검사, 일부 F3→F4 진행, 간경변 환자 일부 간이식, 일부 사망).
이 코호트에는 SACT 가 없으므로 DRUG_EXPOSURE.sact_id 는 항상 비어 있다. 이상사례는 semaglutide 오심, statin 간독성.
저혈당은 이 코호트의 당뇨약(metformin/empagliflozin/pioglitazone/semaglutide)만으로는 근거가 없고 인슐린·SU 를 쓰지 않으므로 만들지 않는다.
동일 약제 처방은 다음 처방 시작 전날까지로 맞춰(공백/겹침 없음) 겹치지 않는다.

점수 산식
  FIB-4 = age x AST / (PLT x sqrt(ALT))                APRI = (AST/40) / PLT x 100
  BARD  = 2 (AST/ALT >= 0.8) + 1 (BMI >= 28) + 1 (당뇨)
  SAFE  = 2.97 age + 5.99 min(BMI,40) + 62.85 DM + 154.85 ln(AST) - 58.23 ln(ALT) + 195.48 ln(globulin g/dL)
          - 141.61 ln(PLT) - 75       (글로불린은 MEASUREMENT 개념이 없어 알부민과 독립으로 생성한 값을 쓴다)
  LiverRisk 는 외부 계산기 값이라 재현할 수 없어 FIB-4/APRI/연령/당뇨 기반의 근사 점수(0~30)를 쓴다.
"""
import math

from framework_v3 import *

# ---- concepts
FATTY, NAFLD = 4058680, 46273476
T2DM, HTN, HLD, OBESITY, CIRRHOSIS = 201826, 320128, 432867, 433736, 4112343
METFORMIN, EMPA, PIO, SEMA, STATIN, ACEI = 1503297, 45774435, 1584910, 1583722, 1545958, 1308216
AST, ALT, PLT, HBA1C, GLU, TG, HDL, LDL = 3013721, 3006923, 3024929, 3004410, 3004501, 3022192, 3007070, 3028437
BMI_C, HT_C, WT_C, SBP, DBP, ALB, BILI, CR = 3038553, 3036277, 3025315, 3004249, 3012888, 3020491, 3024128, 3016723
US, TE, BIOPSY, LT = 4180938, 4260906, 4287806, 4321806
NAUSEA, HEPATOTOX = 27674, 4055224
OBS_LIFESTYLE, OBS_SMOKING = 4083515, 4275495
NOTE_RAD, CLASS_RAD = 44814637, 36716164
NOTE_PATH, CLASS_PATH = 44814640, 36716165
NOTE_DSCH, CLASS_DSCH = 44814641, 36716213
NOTE_OPD, CLASS_PROG = 44814645, 36716177

# 섬유화 단계별 검사 프로파일 (AST, ALT, 혈소판 평균) 및 FibroScan kPa 범위
LAB_PROFILE = {0: (30, 45, 240), 1: (36, 55, 225), 2: (45, 60, 200), 3: (58, 62, 160), 4: (75, 55, 105)}
KPA = {0: (3.5, 5.4), 1: (5.5, 7.0), 2: (7.1, 9.5), 3: (9.6, 12.5), 4: (12.6, 35.0)}
STEATOSIS = [("mild", "경도"), ("moderate", "중등도"), ("severe", "고도")]

US_REPORT = ("Abdomen ultrasonography. Liver: diffusely increased parenchymal echogenicity with {atten}, "
             "compatible with {grade} hepatic steatosis. Liver contour {contour}. Spleen {spleen}. No focal hepatic lesion. "
             "Gallbladder and bile ducts unremarkable. Impression: {grade_ko} 지방간{cirr}.")
TE_REPORT = ("Transient elastography (FibroScan). Liver stiffness measurement {kpa} kPa (IQR/median {iqr}%, {n} valid measurements), "
             "CAP {cap} dB/m. Interpretation: fibrosis stage F{stage}, steatosis S{sgrade}.")
PATH_REPORT = ("Liver, percutaneous needle biopsy: Metabolic dysfunction-associated steatohepatitis. Steatosis grade {sg} ({pct}%), "
               "lobular inflammation {li}, hepatocellular ballooning {bal}; NAS {nas}/8. Fibrosis stage F{stage} (Kleiner). "
               "Portal tracts: {portal}. Iron stain negative.")
DSCH_REPORT = ("Discharge summary. Admitted for {kind} liver transplantation for decompensated MASLD cirrhosis (MELD {meld}). "
               "Procedure {date}, uneventful graft reperfusion. Postoperative course: {course}. Discharged on POD 14 with "
               "immunosuppression and outpatient follow-up.")


# ============================================================== helpers
def _ok(ctx, p, d):
    return d <= ctx.today and (p.death_date is None or d <= p.death_date)


def _anthro(ctx, p, date, vid, ht, wt, htn):
    bmi = round(wt / (ht / 100) ** 2, 1)
    ctx.measure(p, date, HT_C, ht, vid=vid); ctx.measure(p, date, WT_C, wt, vid=vid); ctx.measure(p, date, BMI_C, bmi, vid=vid)
    sbp = ctx.normal(136 if htn else 122, 11, 90, 200, 0); dbp = ctx.normal(84 if htn else 76, 8, 50, 120, 0)
    ctx.measure(p, date, SBP, sbp, vid=vid); ctx.measure(p, date, DBP, dbp, vid=vid)
    return bmi, sbp


def _lab_values(ctx, stage, dm, statin, full=True):
    a, l, t = LAB_PROFILE[stage]
    v = {AST: ctx.normal(a, a * 0.25, 8, 400), ALT: ctx.normal(l, l * 0.3, 8, 400), PLT: ctx.normal(t, t * 0.15, 40, 500),
         HBA1C: ctx.normal(7.1 if dm else 5.6, 0.9 if dm else 0.35, 4.3, 13, 2), GLU: ctx.normal(145 if dm else 97, 30 if dm else 10, 60, 400, 0),
         TG: ctx.normal(175, 60, 50, 800, 0), HDL: ctx.normal(44, 9, 22, 100, 0), LDL: ctx.normal(92 if statin else 122, 28, 40, 300, 0),
         CR: ctx.normal(0.9, 0.2, 0.4, 3.0, 2)}
    if full:
        v[ALB] = ctx.normal(3.3 if stage == 4 else 4.2, 0.35, 2.0, 5.5, 2)
        v[BILI] = ctx.normal(1.6 if stage == 4 else 0.7, 0.5 if stage == 4 else 0.25, 0.2, 12, 2)
    return v


def _record(ctx, p, date, vid, vals):
    for c, v in vals.items():
        ctx.measure(p, date, c, v, vid=vid)


def _scores(ctx, age, vals, bmi, dm):
    """특화 테이블 점수 (모두 소수 둘째 자리 반올림, 명세 범위 안으로 제한)."""
    ast, alt, plt = vals[AST], vals[ALT], vals[PLT]
    fib4 = round(age * ast / (plt * math.sqrt(alt)), 2)
    apri = round((ast / 40.0) / plt * 100.0, 2)
    bard = (2 if ast / alt >= 0.8 else 0) + (1 if bmi >= 28 else 0) + (1 if dm else 0)
    globulin = ctx.normal(2.8, 0.35, 1.8, 4.2, 2)
    safe = (2.97 * age + 5.99 * min(bmi, 40) + 62.85 * (1 if dm else 0) + 154.85 * math.log(ast) - 58.23 * math.log(alt)
            + 195.48 * math.log(globulin) - 141.61 * math.log(plt) - 75)
    safe = round(min(295.0, max(-45.0, safe)), 2)
    liverrisk = round(min(30.0, max(0.0, 2.5 + 3.2 * fib4 + 1.5 * apri + 0.04 * (age - 50) + (1.2 if dm else 0) + ctx.normal(0, 0.5))), 2)
    return fib4, apri, bard, safe, liverrisk


def _prescribe(ctx, p, date, vid, drugs, days):
    days = min(days, (ctx.today - date).days + 1)           # 종료일이 기준일을 넘지 않도록
    days = max(1, days)
    out = {}
    for c in drugs:
        if c == SEMA:   # 주 1회 피하주사
            n = max(1, days // 7)
            did, _ = ctx.drug(p, date, c, days, vid=vid, quantity=n, interval=7, number=n)
        else:
            f = 2 if c == METFORMIN else 1
            did, _ = ctx.drug(p, date, c, days, vid=vid, freq=f, quantity=days * f)
        out[c] = did
    return out


def _ultrasound(ctx, p, date, vid, stage, steat):
    ctx.procedure(p, date, US, vid=vid)
    en, ko = STEATOSIS[steat]
    cirr = stage == 4
    txt = US_REPORT.format(atten=["mild posterior attenuation", "moderate posterior attenuation", "marked posterior attenuation and poor visualization of the diaphragm"][steat],
                           grade=en, grade_ko=ko, contour="nodular and irregular" if cirr else "smooth",
                           spleen=f"enlarged ({ctx.randint(13, 17)} cm)" if cirr else "normal in size",
                           cirr=", 간경변 형태" if cirr else "")
    ctx.note(p, date, txt, note_type=NOTE_RAD, note_class=CLASS_RAD, vid=vid)


def _elastography(ctx, p, date, vid, stage, steat):
    ctx.procedure(p, date, TE, vid=vid)
    kpa = round(ctx.rand(*KPA[stage]), 1)
    cap = int(ctx.normal([255, 290, 330][steat], 18, 180, 400, 0))
    txt = TE_REPORT.format(kpa=kpa, iqr=ctx.randint(5, 25), n=10, cap=cap, stage=stage, sgrade=steat + 1)
    ctx.note(p, date, txt, note_type=NOTE_RAD, note_class=CLASS_RAD, vid=vid)


def _biopsy(ctx, p, date, vid, stage, steat):
    ctx.procedure(p, date, BIOPSY, vid=vid)
    li, bal = ctx.randint(0, 3), ctx.randint(0, 2)
    txt = PATH_REPORT.format(sg=steat + 1, pct=[ctx.randint(5, 33), ctx.randint(34, 66), ctx.randint(67, 90)][steat], li=li, bal=bal,
                             nas=steat + 1 + li + bal, stage=stage, portal="bridging fibrosis" if stage >= 3 else "mild periportal fibrosis" if stage >= 1 else "unremarkable")
    path_day = ctx.days(date, ctx.randint(2, 5))
    if _ok(ctx, p, path_day):
        ctx.note(p, path_day, txt, note_type=NOTE_PATH, note_class=CLASS_PATH, vid=ctx.visit_on(p, path_day))


def _transplant(ctx, p, tx, dm):
    tvid = ctx.visit(p, tx, INPATIENT, los=14)
    ctx.procedure(p, tx, LT, vid=tvid)
    living = ctx.bern(0.6)
    _record(ctx, p, ctx.days(tx, 7), tvid, _lab_values(ctx, 2, dm, False))     # 이식 후 회복기 검사
    txt = DSCH_REPORT.format(kind="living donor" if living else "deceased donor", meld=ctx.randint(18, 32), date=tx.isoformat(),
                             course=ctx.choice(["uneventful", "transient acute kidney injury, recovered", "biliary leak managed conservatively"]))
    ctx.note(p, ctx.days(tx, 14), txt, note_type=NOTE_DSCH, note_class=CLASS_DSCH, vid=tvid)


def _death(ctx, p, dd):
    ctx.set_death(p, dd)
    ctx.visit(p, ctx.days(dd, -3), INPATIENT, los=3)
    for r in ctx.rows["DRUG_EXPOSURE"]:                      # 사망일 이후로 이어지는 처방은 사망일에 종료
        if r["person_id"] == p.person_id and r["drug_exposure_end_date"] > dd:
            r["drug_exposure_end_date"] = dd
            r["days_supply"] = (dd - r["drug_exposure_start_date"]).days + 1
            if r["dosing_number"] is not None:
                r["dosing_number"] = max(1, r["days_supply"] // 7)
                r["quantity"] = r["dosing_number"]
            elif r["quantity"] is not None:
                r["quantity"] = r["days_supply"] * (r["frequency_per_day"] or 1)


# ============================================================== main
def generate(ctx: CtxV3, n=100):
    for _ in range(n):
        gender = FEMALE if ctx.bern(0.45) else MALE
        age = int(ctx.normal(52, 11, 20, 80, 0))
        index = D(2019, 1, 1) + dt.timedelta(days=ctx.randint(0, 365 * 5 + 240))
        p = ctx.person(gender, age, index)

        stage = ctx.choice([0, 1, 2, 3, 4], p=[0.25, 0.30, 0.20, 0.15, 0.10])
        steat = ctx.choice([0, 1, 2], p=[0.45, 0.4, 0.15])
        dm, htn, hld = ctx.bern(0.38), ctx.bern(0.45), ctx.bern(0.5)
        ht = ctx.normal(171 if gender == MALE else 158, 6, 145, 195)
        bmi0 = ctx.normal(27.5, 3.5, 19, 42)
        wt = round(bmi0 * (ht / 100) ** 2, 1)
        obese = bmi0 >= 25 and ctx.bern(0.7)
        responder = ctx.bern(0.4)          # 생활습관 중재 반응군 (체중 감소)
        smoker = ctx.bern(0.45 if gender == MALE else 0.08)
        drugs = []
        if dm:
            drugs.append(METFORMIN)
            if ctx.bern(0.4): drugs.append(EMPA)
            elif ctx.bern(0.4): drugs.append(PIO)
            if bmi0 >= 27 and ctx.bern(0.3): drugs.append(SEMA)
        elif bmi0 >= 30 and ctx.bern(0.3):
            drugs.append(SEMA)
        if hld: drugs.append(STATIN)
        if htn: drugs.append(ACEI)
        statin = STATIN in drugs

        # ---- 1) 진단 외래 (index)
        vid = ctx.visit(p, index)
        ctx.condition(p, index, FATTY if ctx.bern(0.6) else NAFLD, vid=vid)
        for c, flag in ((T2DM, dm), (HTN, htn), (HLD, hld), (OBESITY, obese)):
            if flag: ctx.condition(p, index, c, vid=vid)
        cirr_date = None
        if stage == 4:
            ctx.condition(p, index, CIRRHOSIS, vid=vid); cirr_date = index
        _ultrasound(ctx, p, index, vid, stage, steat)
        bmi, sbp = _anthro(ctx, p, index, vid, ht, wt, htn)
        vals = _lab_values(ctx, stage, dm, statin)
        if not (dm or htn or hld or obese or bmi >= 23 or vals[HBA1C] >= 5.7 or sbp >= 130 or vals[TG] >= 150):
            vals[TG] = float(ctx.randint(155, 260))     # MASLD 정의: 심장대사 기준 1개 보장
        _record(ctx, p, index, vid, vals)
        fib4, apri, bard, safe, liverrisk = _scores(ctx, p.age_on(index), vals, bmi, dm)
        ctx.disease_row(p, vid, fib4_score=fib4, apri_score=apri, bard_score=bard, safe_score=safe, liverrisk_score=liverrisk)
        ctx.observation(p, index, OBS_SMOKING, vid=vid, value_string="Current smoker" if smoker else "Never smoker")
        ctx.observation(p, index, OBS_LIFESTYLE, vid=vid, value_string="Lifestyle counselling: weight loss 7-10%, Mediterranean diet, exercise 150 min/wk")
        txt = f"Outpatient note. MASLD confirmed on ultrasound ({STEATOSIS[steat][0]} steatosis). BMI {bmi}. Cardiometabolic risk: " \
              + ", ".join([n_ for n_, f in (("T2DM", dm), ("HTN", htn), ("dyslipidemia", hld), ("obesity", obese)) if f] or ["BMI/lab criteria"]) \
              + f". FIB-4 {fib4}, APRI {apri}. Lifestyle modification counselled; FibroScan scheduled."
        ctx.note(p, index, txt, note_type=NOTE_OPD, note_class=CLASS_PROG, vid=vid)
        sema_first = None
        m1 = ctx.days(index, ctx.randint(28, 35))
        fu0 = ctx.days(index, ctx.randint(170, 200))
        if drugs:
            ids = _prescribe(ctx, p, index, vid, drugs, (m1 - index).days)      # 다음 처방(1개월 외래) 전날까지
            sema_first = (index, ids.get(SEMA))

        # ---- 2) 1개월 외래: FibroScan, 90일 처방 / 간생검
        if _ok(ctx, p, m1):
            mvid = ctx.visit_on(p, m1)
            if ctx.bern(0.8):
                _elastography(ctx, p, m1, mvid, stage, steat)
            ctx.observation(p, m1, OBS_LIFESTYLE, vid=mvid, value_string="Lifestyle counselling reinforced")
            if drugs: _prescribe(ctx, p, m1, mvid, drugs, 90)
            if ctx.bern(0.15):
                bx = ctx.days(m1, ctx.randint(10, 55))
                if _ok(ctx, p, bx):
                    _biopsy(ctx, p, bx, ctx.visit_on(p, bx), stage, steat)
        # semaglutide 오심 (초회 처방 후 5~20일)
        if sema_first and sema_first[1] and ctx.bern(0.4):
            ae_day = ctx.days(sema_first[0], ctx.randint(5, 20))
            if _ok(ctx, p, ae_day):
                avid = ctx.visit_on(p, ae_day)
                ctx.ae(p, ae_day, NAUSEA, ctx.randint(1, 2), vid=avid, causality=2, action=1)
                ctx.condition(p, ae_day, NAUSEA, vid=avid)
        # statin 간독성 (경도, 약물 중단 없이 관찰)
        if statin and ctx.bern(0.05):
            ae_day = ctx.days(index, ctx.randint(30, 120))
            if _ok(ctx, p, ae_day):
                avid = ctx.visit_on(p, ae_day)
                ctx.ae(p, ae_day, HEPATOTOX, ctx.randint(1, 2), vid=avid, causality=3, action=1)
                ctx.condition(p, ae_day, HEPATOTOX, vid=avid)
        # 중간 리필 (1개월 방문 + 90일)
        if drugs and _ok(ctx, p, ctx.days(m1, 90)):
            r = ctx.days(m1, 90)
            _prescribe(ctx, p, r, ctx.visit_on(p, r), drugs, (fu0 - r).days)    # 첫 6개월 추적 전날까지

        # ---- 3) 6개월 간격 추적
        n_fu = ctx.randint(4, 10)
        fu = fu0
        k, transplanted = 0, None
        while k < n_fu and fu <= ctx.today:
            # 이번 추적에서 결정되는 사망일 (이후 이벤트는 이 날짜 이전으로 제한)
            dd = None
            if cirr_date and transplanted is None and ctx.bern(0.07):
                dd = ctx.days(fu, ctx.randint(30, 150))
            elif transplanted and ctx.bern(0.06):
                dd = ctx.days(fu, ctx.randint(30, 150))
            elif ctx.bern(0.004):
                dd = ctx.days(fu, ctx.randint(10, 120))
            if dd is not None and dd > ctx.today:
                dd = None
            fvid = ctx.visit_on(p, fu)
            if responder:
                wt = round(max(35.0, wt - ctx.rand(0.3, 1.2)), 1)
            else:
                wt = round(max(35.0, wt + ctx.rand(-0.6, 0.8)), 1)
            bmi, _b = _anthro(ctx, p, fu, fvid, ht, wt, htn)
            # 진행: F3 -> F4
            if stage == 3 and cirr_date is None and k >= 2 and ctx.bern(0.15):
                stage = 4; cirr_date = fu
                ctx.condition(p, fu, CIRRHOSIS, vid=fvid)
                _elastography(ctx, p, fu, fvid, stage, steat)
            elif stage >= 1 and k % 2 == 1 and ctx.bern(0.5) and transplanted is None:
                _elastography(ctx, p, fu, fvid, stage, steat)
            _record(ctx, p, fu, fvid, _lab_values(ctx, stage if transplanted is None else 1, dm, statin, full=(stage >= 3 or k % 2 == 0)))
            ctx.observation(p, fu, OBS_LIFESTYLE, vid=fvid, value_string=f"Lifestyle counselling; weight {wt} kg")
            gap = ctx.randint(170, 200)
            next_fu = ctx.days(fu, gap)
            # 간이식 (간경변 진단 1년 이후): 다음 방문일이 달라지므로 처방 기간 산정 전에 결정
            tx = None
            if cirr_date and transplanted is None and dd is None and (fu - cirr_date).days >= 365 and ctx.bern(0.09):
                tx_c = ctx.days(fu, ctx.randint(45, 120))
                if ctx.days(tx_c, 14) <= ctx.today:
                    tx = tx_c
                    next_fu = ctx.days(tx, ctx.randint(170, 200))
            if drugs:
                _prescribe(ctx, p, fu, fvid, drugs, 90)
                r = ctx.days(fu, 90)
                if _ok(ctx, p, r) and (dd is None or r < dd):
                    _prescribe(ctx, p, r, ctx.visit_on(p, r), drugs, (next_fu - r).days)   # 다음 추적 전날까지
            if tx is not None:
                _transplant(ctx, p, tx, dm)
                transplanted = tx
                fu = next_fu; k += 1
                continue
            if dd is not None:
                _death(ctx, p, dd)
                break
            fu = next_fu; k += 1
        ctx.finalize_person(p)

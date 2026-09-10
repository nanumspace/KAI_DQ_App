# -*- coding: utf-8 -*-
"""
대사이상지방간(MASLD) 코호트 시나리오 (환자 여정 템플릿)

여정 개요
  1) 진단 외래(index): 복부 초음파(지방간 등급 판독문), 코호트 진단(4058680 지방간 / 46273476 NAFLD),
     심장대사 동반질환(비만/제2형 당뇨/고혈압/이상지질혈증), 신체계측(신장/체중/BMI), 혈압,
     생활습관(음주: MASLD 정의 임계 미만, 흡연, 운동), 기본 혈액검사(AST/ALT/혈소판/HbA1c/혈당/지질/알부민/빌리루빈/크레아티닌),
     예후 척도 FIB-4 / APRI (동일 검사값으로 산출, 입력항목별 1행), 일부 BARD
  2) 1개월 외래: 간 순간탄성측정(FibroScan, kPa + F0~F4) 80%, 90일 처방. 약 15% 는 간생검(병리 판독문)
  3) 관리: 생활습관 상담(OBSERVATION), 약물(metformin/empagliflozin/pioglitazone/semaglutide/atorvastatin/lisinopril)
     DRUG_EXPOSURE(30~90일 공급, 방문마다 재처방 + 중간 리필) 및 특화 테이블 drug 행, 이상사례(semaglutide 오심, 저혈당)
  4) 6개월 간격 추적 2~5년: 검사 + FIB-4/APRI 재산출(검사일 기준 나이), 일부 F3 -> F4 진행(간경변 4112343),
     간경변 환자 일부 간이식(입원 14일, oprt 그룹 + 4321806), 일부 사망(사망 후 이벤트 없음, death_date 는 PERSON 과 동일)
  5) 주요 시술마다 proc 그룹 행(procedure_occurrence_id + 생성일시 timestamp)
이 코호트에는 ANTP_THERAPY 가 없으므로 antp_id 는 항상 NULL 이다 (D-11).

규칙 충족 설계 메모
  - SEM-MA-001: AST/ALT/혈소판은 FIB-4 산출일에만 기록하고(±7일 안에 1세트), 점수는 그 값으로 그대로 계산한다.
  - SEM-MA-003: 음주량 drnk_qty x drnk_nt <= 10(여) / 15(남) 으로 제한.
  - SEM-MA-005: 진단/BMI>=23/HbA1c>=5.7/SBP>=130/TG>=150 중 하나를 index 시점에 반드시 갖도록 보정.
  - exam_gnrx_input_nm / _vl 은 스칼라이므로 척도 1개당 입력항목별 1행 (폐암 gmt 유전자별 1행과 같은 방식).
"""
from framework import *

# ---- concepts
FATTY, NAFLD = 4058680, 46273476
T2DM, HTN, HLD, OBESITY, CIRRHOSIS = 201826, 320128, 432867, 433736, 4112343
METFORMIN, EMPA, PIO, SEMA, STATIN, ACEI = 1503297, 45774435, 1584910, 1583722, 1545958, 1308216
AST, ALT, PLT, HBA1C, GLU, TG, HDL, LDL = 3013721, 3006923, 3024929, 3004410, 3004501, 3022192, 3007070, 3028437
BMI_C, HT_C, WT_C, SBP, DBP, ALB, BILI, CR = 3038553, 3036277, 3025315, 3004249, 3012888, 3020491, 3024128, 3016723
US, TE, BIOPSY, LT = 4180938, 4260906, 4287806, 4321806
NAUSEA, HYPOGLY = 27674, 24609
# 관찰 concept (대표값; Athena 대조 필요) : 생활습관 상담, 흡연 상태
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


def _proc_row(ctx, p, vid, date, pid):
    # 문자열 timestamp 로 기록: datetime 객체와 NULL 이 섞인 컬럼은 pandas 가 datetime64 로 추론해 NaT 가 생기고,
    # framework.fmt 가 NaT.strftime 에서 실패한다 (framework 수정 없이 우회).
    ts = dt.datetime(date.year, date.month, date.day, ctx.randint(8, 17), ctx.randint(0, 59), ctx.randint(0, 59)).strftime("%Y-%m-%d %H:%M:%S")
    ctx.disease_row(p, vid, procedure_occurrence_crtn_dt=ts, care_site_id=p.care_site, procedure_occurrence_id=pid)


def _note_row(ctx, p, vid, date, ntype, text, nid):
    ctx.disease_row(p, vid, note_date=date, note_type_concept_id=ntype, note_text=text, note_id=nid)


def _anthro(ctx, p, date, vid, ht, wt, htn):
    bmi = round(wt / (ht / 100) ** 2, 1)
    ctx.measure(p, date, HT_C, ht, vid=vid); ctx.measure(p, date, WT_C, wt, vid=vid); ctx.measure(p, date, BMI_C, bmi, vid=vid)
    sbp = ctx.normal(136 if htn else 122, 11, 90, 200, 0); dbp = ctx.normal(84 if htn else 76, 8, 50, 120, 0)
    ctx.measure(p, date, SBP, sbp, vid=vid); ctx.measure(p, date, DBP, dbp, vid=vid)
    ctx.disease_row(p, vid, anth_rcrd_ymd=date, ht_msrm_vl=ht, wt_msrm_vl=wt, bmi_vl=bmi)
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
    return {c: ctx.measure(p, date, c, v, vid=vid) for c, v in vals.items()}


def _score_rows(ctx, p, vid, date, vals, mids, bmi, dm, with_bard):
    """FIB-4 / APRI (/BARD) 점수 행. 척도별 입력항목마다 1행, 점수값은 같은 날 MEASUREMENT 값으로 산출."""
    age = p.age_on(date)
    ast, alt, plt = vals[AST], vals[ALT], vals[PLT]
    fib4 = round(age * ast / (plt * math.sqrt(alt)), 2)
    apri = round((ast / 40.0) * 100.0 / plt, 2)
    for nm, c in (("AST", AST), ("ALT", ALT), ("Platelet count", PLT)):
        ctx.disease_row(p, vid, exam_gnrx_ymd=date, exam_gnrx_idx_nm="FIB-4", exam_gnrx_rslt_vl=fib4, fib4_score=fib4, age=age,
                        exam_gnrx_input_nm=nm, exam_gnrx_input_nm_vl=vals[c], measurement_id=mids[c])
    for nm, c in (("AST", AST), ("Platelet count", PLT)):
        ctx.disease_row(p, vid, exam_gnrx_ymd=date, exam_gnrx_idx_nm="APRI", exam_gnrx_rslt_vl=apri, apri_score=apri,
                        exam_gnrx_input_nm=nm, exam_gnrx_input_nm_vl=vals[c], measurement_id=mids[c])
    if with_bard:
        ratio = round(ast / alt, 2)
        bard = (2 if ratio >= 0.8 else 0) + (1 if bmi >= 28 else 0) + (1 if dm else 0)
        ctx.disease_row(p, vid, exam_gnrx_ymd=date, exam_gnrx_idx_nm="BARD", exam_gnrx_rslt_vl=bard, bard_score=bard,
                        exam_gnrx_input_nm="AST/ALT ratio", exam_gnrx_input_nm_vl=ratio)
        ctx.disease_row(p, vid, exam_gnrx_ymd=date, exam_gnrx_idx_nm="BARD", exam_gnrx_rslt_vl=bard, bard_score=bard,
                        exam_gnrx_input_nm="BMI", exam_gnrx_input_nm_vl=bmi)
    return fib4, apri


def _prescribe(ctx, p, date, vid, drugs, days):
    # 종료일(start + days - 1)이 검증일/사망일을 넘지 않도록 공급일수 제한
    days = min(days, (ctx.today - date).days + 1)
    if p.death_date is not None:
        days = min(days, (p.death_date - date).days + 1)
    days = max(1, days)
    out = {}
    for c in drugs:
        if c == SEMA:   # 주 1회 피하주사
            did, _ = ctx.drug(p, date, c, days, vid=vid, interval=7, number=max(1, days // 7))
        else:
            did, _ = ctx.drug(p, date, c, days, vid=vid, freq=2 if c == METFORMIN else 1)
        ctx.disease_row(p, vid, drug_prsc_ymd=date, drug_exposure_id=did)
        out[c] = did
    return out


def _ultrasound(ctx, p, date, vid, stage, steat):
    pid = ctx.procedure(p, date, US, vid=vid)
    en, ko = STEATOSIS[steat]
    cirr = stage == 4
    txt = US_REPORT.format(atten=["mild posterior attenuation", "moderate posterior attenuation", "marked posterior attenuation and poor visualization of the diaphragm"][steat],
                           grade=en, grade_ko=ko, contour="nodular and irregular" if cirr else "smooth",
                           spleen=f"enlarged ({ctx.randint(13, 17)} cm)" if cirr else "normal in size",
                           cirr=", 간경변 형태" if cirr else "")
    nid = ctx.note(p, date, txt, note_type=NOTE_RAD, note_class=CLASS_RAD, vid=vid)
    ctx.disease_row(p, vid, imex_ymd=date, imex_kncd="US-ABD", imex_knnm="복부 초음파", imex_rslt_cont=txt,
                    lver_fbrs_grnm="F4 (cirrhotic morphology)" if cirr else None, procedure_occurrence_id=pid, note_id=nid)
    _note_row(ctx, p, vid, date, NOTE_RAD, txt, nid)
    _proc_row(ctx, p, vid, date, pid)


def _elastography(ctx, p, date, vid, stage, steat):
    pid = ctx.procedure(p, date, TE, vid=vid)
    kpa = round(ctx.rand(*KPA[stage]), 1)
    cap = int(ctx.normal([255, 290, 330][steat], 18, 180, 400, 0))
    txt = TE_REPORT.format(kpa=kpa, iqr=ctx.randint(5, 25), n=10, cap=cap, stage=stage, sgrade=steat + 1)
    nid = ctx.note(p, date, txt, note_type=NOTE_RAD, note_class=CLASS_RAD, vid=vid)
    ctx.disease_row(p, vid, imex_ymd=date, imex_kncd="FIBROSCAN", imex_knnm="간 순간탄성측정(Transient elastography)", imex_rslt_cont=txt,
                    lver_fbrs_grnm=f"F{stage}", procedure_occurrence_id=pid, note_id=nid)
    _note_row(ctx, p, vid, date, NOTE_RAD, txt, nid)
    _proc_row(ctx, p, vid, date, pid)
    return kpa


def _biopsy(ctx, p, date, vid, stage, steat):
    pid = ctx.procedure(p, date, BIOPSY, vid=vid)
    li, bal = ctx.randint(0, 3), ctx.randint(0, 2)
    txt = PATH_REPORT.format(sg=steat + 1, pct=[ctx.randint(5, 33), ctx.randint(34, 66), ctx.randint(67, 90)][steat], li=li, bal=bal,
                             nas=steat + 1 + li + bal, stage=stage, portal="bridging fibrosis" if stage >= 3 else "mild periportal fibrosis" if stage >= 1 else "unremarkable")
    path_day = ctx.days(date, ctx.randint(2, 5))
    pvid = ctx.visit_on(p, path_day)
    nid = ctx.note(p, path_day, txt, note_type=NOTE_PATH, note_class=CLASS_PATH, vid=pvid)
    _note_row(ctx, p, pvid, path_day, NOTE_PATH, txt, nid)
    _proc_row(ctx, p, vid, date, pid)


def _transplant(ctx, p, tx, stage, dm):
    tvid = ctx.visit(p, tx, INPATIENT, los=14)
    pid = ctx.procedure(p, tx, LT, vid=tvid)
    living = ctx.bern(0.6)
    ctx.disease_row(p, tvid, oprt_ymd=tx, oprt_kncd="LT-LDLT" if living else "LT-DDLT", oprt_knnm="생체 간이식" if living else "뇌사자 간이식",
                    procedure_occurrence_id=pid)
    _proc_row(ctx, p, tvid, tx, pid)
    d7 = ctx.days(tx, 7)
    vals = _lab_values(ctx, 2, dm, False)          # 이식 후 회복기 검사 (FIB-4 산출 없음)
    _record(ctx, p, d7, tvid, vals)
    d14 = ctx.days(tx, 14)
    txt = DSCH_REPORT.format(kind="living donor" if living else "deceased donor", meld=ctx.randint(18, 32), date=tx.isoformat(),
                             course=ctx.choice(["uneventful", "transient acute kidney injury, recovered", "biliary leak managed conservatively"]))
    nid = ctx.note(p, d14, txt, note_type=NOTE_DSCH, note_class=CLASS_DSCH, vid=tvid)
    _note_row(ctx, p, tvid, d14, NOTE_DSCH, txt, nid)
    return tvid


def _death(ctx, p, dd):
    ctx.set_death(p, dd)
    dvid = ctx.visit(p, ctx.days(dd, -3), INPATIENT, los=3)
    ctx.disease_row(p, dvid, death_date=dd)
    p.patient_fields["death_date"] = dd
    for r in ctx.rows["MASLD"]:
        if r["person_id"] == p.person_id:
            r["death_date"] = dd


# ============================================================== main
def generate(ctx: Ctx, n=100):
    for _ in range(n):
        gender = FEMALE if ctx.bern(0.45) else MALE
        age = int(ctx.normal(52, 11, 20, 80, 0))
        index = D(2019, 1, 1) + dt.timedelta(days=ctx.randint(0, 365 * 5 + 240))
        p = ctx.person(gender, age, index)
        p.patient_fields = dict(date_of_birth=p.birth)

        stage = ctx.choice([0, 1, 2, 3, 4], p=[0.25, 0.30, 0.20, 0.15, 0.10])
        steat = ctx.choice([0, 1, 2], p=[0.45, 0.4, 0.15])
        dm, htn, hld = ctx.bern(0.38), ctx.bern(0.45), ctx.bern(0.5)
        ht = ctx.normal(171 if gender == MALE else 158, 6, 145, 195)
        bmi0 = ctx.normal(27.5, 3.5, 19, 42)
        wt = round(bmi0 * (ht / 100) ** 2, 1)
        obese = bmi0 >= 25 and ctx.bern(0.7)
        responder = ctx.bern(0.4)          # 생활습관 중재 반응군 (체중 감소)
        drinker = ctx.bern(0.6 if gender == MALE else 0.35)
        smoker = ctx.bern(0.45 if gender == MALE else 0.08)
        exerciser = ctx.bern(0.55)
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
            vals[TG] = float(ctx.randint(155, 260))     # SEM-MA-005: 심장대사 기준 1개 보장
        mids = _record(ctx, p, index, vid, vals)
        _score_rows(ctx, p, vid, index, vals, mids, bmi, dm, with_bard=ctx.bern(0.3))
        # 생활습관
        limit = 10 if gender == FEMALE else 15
        nt = ctx.randint(1, 8) if drinker else 0
        qty = min(round(ctx.rand(0.5, 1.5), 1), round(limit / nt, 1)) if drinker else 0
        hist = dict(drnk_dtrn_ycnt=ctx.randint(3, min(40, age - 18)) if drinker else 0, drnk_nt=nt, drnk_qty=qty,
                    shis_yn_noans_spcd="Y" if smoker else "N", shis_yn_noans_spnm="예" if smoker else "아니오",
                    smok_dtrn_ycnt=ctx.randint(5, min(35, age - 18)) if smoker else None, smok_qty=round(ctx.rand(0.3, 1.5), 1) if smoker else None,
                    exercise_ycnt=round(ctx.rand(0.5, 10), 1) if exerciser else 0, exercise_nt=ctx.randint(1, 6) if exerciser else 0,
                    exercise_tm=ctx.randint(20, 90) if exerciser else 0)
        ctx.disease_row(p, vid, rcrd_ymd=index, **hist)
        ctx.observation(p, index, OBS_SMOKING, vid=vid, value_string="Current smoker" if smoker else "Never smoker")
        oid = ctx.observation(p, index, OBS_LIFESTYLE, vid=vid, value_string="Lifestyle counselling: weight loss 7-10%, Mediterranean diet, exercise 150 min/wk")
        txt = f"Outpatient note. MASLD confirmed on ultrasound ({STEATOSIS[steat][0]} steatosis). BMI {bmi}. Cardiometabolic risk: " \
              + ", ".join([n for n, f in (("T2DM", dm), ("HTN", htn), ("dyslipidemia", hld), ("obesity", obese)) if f] or ["BMI/lab criteria"]) \
              + ". Lifestyle modification counselled; FibroScan scheduled."
        nid = ctx.note(p, index, txt, note_type=NOTE_OPD, note_class=CLASS_PROG, vid=vid)
        _note_row(ctx, p, vid, index, NOTE_OPD, txt, nid)
        sema_first = None
        if drugs:
            ids = _prescribe(ctx, p, index, vid, drugs, 30)
            sema_first = (index, ids.get(SEMA))

        # ---- 2) 1개월 외래: FibroScan, 90일 처방 / 간생검
        m1 = ctx.days(index, ctx.randint(28, 35))
        last = index
        if _ok(ctx, p, m1):
            mvid = ctx.visit_on(p, m1)
            if ctx.bern(0.8):
                _elastography(ctx, p, m1, mvid, stage, steat)
            ctx.observation(p, m1, OBS_LIFESTYLE, vid=mvid, value_string="Lifestyle counselling reinforced")
            if drugs: _prescribe(ctx, p, m1, mvid, drugs, 90)
            last = m1
            if ctx.bern(0.15):
                bx = ctx.days(m1, ctx.randint(10, 55))
                if _ok(ctx, p, bx):
                    _biopsy(ctx, p, bx, ctx.visit_on(p, bx), stage, steat)
                    last = bx
        # semaglutide 오심 (초회 처방 후 5~20일)
        if sema_first and sema_first[1] and ctx.bern(0.4):
            ae_day = ctx.days(sema_first[0], ctx.randint(5, 20))
            avid = ctx.visit_on(p, ae_day)
            ctx.ae(p, ae_day, NAUSEA, ctx.randint(1, 2), vid=avid, drug_exposure_id=sema_first[1], causality=2, action=1)
            ctx.condition(p, ae_day, NAUSEA, vid=avid)
        # 중간 리필 (1개월 방문 + 90일)
        if drugs and _ok(ctx, p, ctx.days(m1, 90)):
            r = ctx.days(m1, 90)
            _prescribe(ctx, p, r, ctx.visit_on(p, r), drugs, 90)

        # ---- 3) 6개월 간격 추적
        n_fu = ctx.randint(4, 10)
        fu = ctx.days(index, ctx.randint(170, 200))
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
            # 체중 변화
            if responder:
                wt = round(max(35.0, wt - ctx.rand(0.3, 1.2)), 1)
            else:
                wt = round(max(35.0, wt + ctx.rand(-0.6, 0.8)), 1)
            bmi, _ = _anthro(ctx, p, fu, fvid, ht, wt, htn)
            # 진행: F3 -> F4
            if stage == 3 and cirr_date is None and k >= 2 and ctx.bern(0.15):
                stage = 4; cirr_date = fu
                ctx.condition(p, fu, CIRRHOSIS, vid=fvid)
                _elastography(ctx, p, fu, fvid, stage, steat)
            elif stage >= 1 and k % 2 == 1 and ctx.bern(0.5) and transplanted is None:
                _elastography(ctx, p, fu, fvid, stage, steat)
            vals = _lab_values(ctx, stage if transplanted is None else 1, dm, statin, full=(stage >= 3 or k % 2 == 0))
            mids = _record(ctx, p, fu, fvid, vals)
            if transplanted is None:
                _score_rows(ctx, p, fvid, fu, vals, mids, bmi, dm, with_bard=(k % 3 == 2))
            ctx.observation(p, fu, OBS_LIFESTYLE, vid=fvid, value_string=f"Lifestyle counselling; weight {wt} kg")
            if k % 2 == 1:
                h = dict(hist)
                if exerciser or responder:
                    h.update(exercise_ycnt=round((hist["exercise_ycnt"] or 0) + (k + 1) / 2, 1), exercise_nt=ctx.randint(2, 6), exercise_tm=ctx.randint(30, 90))
                if drinker:
                    h.update(drnk_nt=max(0, nt - ctx.randint(0, nt)), drnk_dtrn_ycnt=hist["drnk_dtrn_ycnt"] + (k + 1) // 2)
                ctx.disease_row(p, fvid, rcrd_ymd=fu, **h)
            if drugs:
                _prescribe(ctx, p, fu, fvid, drugs, 90)
                r = ctx.days(fu, 90)
                if _ok(ctx, p, r) and (dd is None or r < dd):
                    _prescribe(ctx, p, r, ctx.visit_on(p, r), drugs, 90)
            # 저혈당 이상사례 (당뇨 약물)
            if dm and ctx.bern(0.05):
                ae_day = ctx.days(fu, ctx.randint(5, 60))
                if _ok(ctx, p, ae_day) and (dd is None or ae_day < dd):
                    grade = ctx.choice([1, 2, 3], p=[0.55, 0.3, 0.15])
                    avid = ctx.visit(p, ae_day, ER if grade >= 3 else OUTPATIENT)
                    ctx.ae(p, ae_day, HYPOGLY, grade, vid=avid, causality=2, action=2 if grade >= 3 else 1)
                    ctx.condition(p, ae_day, HYPOGLY, vid=avid)
            # 간이식 (간경변 진단 1년 이후)
            if cirr_date and transplanted is None and dd is None and (fu - cirr_date).days >= 365 and ctx.bern(0.09):
                tx = ctx.days(fu, ctx.randint(45, 120))
                if ctx.days(tx, 14) <= ctx.today:
                    _transplant(ctx, p, tx, stage, dm)
                    transplanted = tx
                    fu = ctx.days(tx, ctx.randint(170, 200)); k += 1
                    continue
            if dd is not None:
                _death(ctx, p, dd)
                break
            fu = ctx.days(fu, ctx.randint(170, 200)); k += 1
        ctx.finalize_person(p)

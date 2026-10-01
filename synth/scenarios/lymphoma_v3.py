# -*- coding: utf-8 -*-
"""
림프종 코호트 시나리오 (v3)

v1 림프종 여정(`lymphoma.py`)을 v3 테이블로 옮겼다. 특화 테이블 LYMPHOMA 는 환자당 1행(진단 입원 방문에 매단다).

아형(histology_icdo3_code) 구성: DLBCL 9680/3(일부 9684/3·9688/3) 45%, 고전적 호지킨 9650/3 15%, 외투세포 9673/3 10%,
말초 T세포 NOS 9702/3 10%, 여포성 9690/3 10%, 변연부 9699/3 10%.
  cell_of_origin 은 DLBCL 계열 코드에만 채운다 (SEM3-LY-001/002).
  아형별 선택 항목: MIPI·MIPI-c(외투세포), IPS(호지킨 진행기), PIT(PTCL), double-expressor/double-hit(DLBCL),
  t(14;18)(DLBCL·여포성), t(11;14)(외투세포), MRD·ctDNA(일부).
여정: 진단 입원(5일, 생검·PET·골수검사) → 아형별 1차 요법(R-CHOP / ABVD / R-CVP / CHOP / 리툭시맙 단독) →
      중간·종료 PET → (일부) 리툭시맙 유지 → 재발·불응 시 구제요법(R-GDP / GDP / BV) → 자가이식 / CAR-T / 진행·사망 → 추적.
"""
from framework_v3 import *

DLBCL, HL, MCL, PTCL, FL, MZL = "DLBCL", "HL", "MCL", "PTCL", "FL", "MZL"
SUBS = [DLBCL, HL, MCL, PTCL, FL, MZL]
SUB_P = [0.45, 0.15, 0.10, 0.10, 0.10, 0.10]
CONDITION = {DLBCL: 4300704, HL: 438090, MCL: 4038836, PTCL: 4038838, FL: 4147411,
             MZL: 4147411}          # 변연부 림프종 전용 개념이 concepts.yaml 에 없어 같은 저등급 B세포 개념(여포성)으로 대용
LABEL = {DLBCL: "Diffuse large B-cell lymphoma", HL: "Classical Hodgkin lymphoma", MCL: "Mantle cell lymphoma",
         PTCL: "Peripheral T-cell lymphoma, NOS", FL: "Follicular lymphoma", MZL: "Marginal zone lymphoma"}
NODAL_SITES = ["cervical lymph node", "axillary lymph node", "mediastinal lymph node", "inguinal lymph node",
               "retroperitoneal lymph node", "abdominal lymph node"]
EXTRANODAL = ["stomach", "bone", "liver", "lung", "skin", "bone marrow", "small intestine", "kidney"]
R_CHOP = [1314273, 1310317, 1338512, 1308290, 1551099]
CHOP = [1310317, 1338512, 1308290, 1551099]
R_CVP = [1314273, 1310317, 1308290, 1551099]
ABVD = [1338512, 1329033, 19008264, 1319193]    # doxorubicin, bleomycin, vinblastine, dacarbazine
R_GDP = [1314273, 1314924, 1518254, 1397141]
GDP = [1314924, 1518254, 1397141]
DEX4 = {1518254: 4}                       # 덱사메타손은 사이클당 4일
BASE_LABS = [3000963, 3010813, 3017732, 3024929, 3016723, 3013721, 3006923, 3020491, 3024128, 3022250, 3006315]
RESP_OF_DS = {1: "CR", 2: "CR", 3: "CR", 4: "PR", 5: "PD"}

PATH_REPORT = ("Lymph node, {site}, excisional biopsy: {hist}. Immunohistochemistry: {ihc}. Ki-67 {ki67}%. "
               "Specimen adequate for ancillary studies.")
PET_REPORT = ("FDG PET/CT (baseline). Hypermetabolic lymphadenopathy in {n} nodal region{s} including {primary}{dist}, "
              "SUVmax {suv}. {extra} Impression: Lymphoma, Lugano stage {stage}.")
RESP_REPORT = "FDG PET/CT ({tp}). Deauville score {ds}. {resp}."
# DLBCL(Hans 알고리즘, 세포기원과 일치)·외투세포(cyclin D1 은 t(11;14) 결과와 일치)는 _ihc_text 가 만든다.
IHC_TXT = {HL: "CD30 positive, CD15 positive, PAX5 weak positive, CD20 negative",
           PTCL: "CD3 positive, CD4 positive, CD5 partial loss, CD20 negative",
           FL: "CD20 positive, CD10 positive, BCL2 positive, BCL6 positive",
           MZL: "CD20 positive, CD5 negative, CD10 negative, CD23 negative"}
LABEL_BY_CODE = {"9684/3": "Diffuse large B-cell lymphoma, immunoblastic",
                 "9688/3": "T-cell/histiocyte-rich large B-cell lymphoma"}


def generate(ctx: CtxV3, n=100):
    for _ in range(n):
        sub = ctx.choice(SUBS, p=SUB_P)
        gender = FEMALE if ctx.bern(0.42) else MALE
        age = {HL: int(ctx.normal(34, 12, 18, 80, 0)), FL: int(ctx.normal(58, 11, 25, 85, 0))}.get(sub) \
            or int(ctx.normal(64, 11, 22, 90, 0))
        index = D(2019, 1, 1) + dt.timedelta(days=ctx.randint(0, 365 * 6 - 5))
        p = ctx.person(gender, age, index)
        dlbcl, hl, mcl, ptcl, fl, mzl = (sub == s for s in SUBS)
        code = {DLBCL: ctx.choice(["9680/3", "9684/3", "9688/3"], p=[0.92, 0.04, 0.04]), HL: "9650/3", MCL: "9673/3",
                PTCL: "9702/3", FL: "9690/3", MZL: "9699/3"}[sub]

        # ---- 1) 진단 입원 (5일)
        dx_vid = ctx.visit(p, index, INPATIENT, los=5)
        ctx.condition(p, index, CONDITION[sub], vid=dx_vid)
        if ctx.bern(0.3): ctx.condition(p, index, 320128, vid=dx_vid)      # HTN
        if ctx.bern(0.15): ctx.condition(p, index, 201826, vid=dx_vid)     # T2DM
        primary = ctx.choice(NODAL_SITES)
        stage = ctx.choice(["I", "II", "III", "IV"], p=[0.25, 0.35, 0.2, 0.2] if hl else
                           ([0.1, 0.2, 0.3, 0.4] if (fl or mcl or mzl) else [0.15, 0.3, 0.25, 0.3]))
        adv = stage in ("III", "IV")
        bulky = ctx.bern(0.25)
        ecog = ctx.choice([0, 1, 2, 3], p=[0.35, 0.45, 0.15, 0.05])
        labs = ctx.labs(p, index, BASE_LABS, vid=dx_vid,
                        shifts={3022250: 150 if (adv and (dlbcl or ptcl)) else (40 if adv else 0), 3006315: 1.0 if adv else 0})
        ht = ctx.normal(171 if gender == MALE else 158, 6, 145, 190); wt = ctx.normal(67 if gender == MALE else 56, 9, 38, 110)
        ctx.measure(p, index, 3036277, ht, vid=dx_vid); ctx.measure(p, index, 3025315, wt, vid=dx_vid)
        ctx.observation(p, index, 4257895, vid=dx_vid, value_number=ecog, value_string=f"ECOG {ecog}")
        ctx.procedure(p, index, 4306780, vid=dx_vid)                       # 절제 림프절 생검
        pet_day, bm_day = ctx.days(index, 1), ctx.days(index, 2)
        ctx.procedure(p, pet_day, 4305790, vid=dx_vid)
        ctx.procedure(p, bm_day, 4023083, vid=dx_vid)
        ki67 = int(ctx.normal(70 if (dlbcl or ptcl) else (25 if mcl else (12 if (fl or mzl) else 40)), 12, 3, 99, 0))
        leuk = labs[3010813]
        ldh_high = labs[3022250] > 250
        extranodal = stage == "IV"            # Lugano IV 만 비인접 결외 침범이 있다 (I~III 은 결절 영역으로만 기술)
        fields = _subtype_fields(ctx, sub, p.age_at_index, ecog, ldh_high, leuk, ki67, adv, extranodal)
        ctx.note(p, bm_day, PATH_REPORT.format(site=primary, hist=LABEL_BY_CODE.get(code, LABEL[sub]), ki67=ki67,
                                               ihc=_ihc_text(ctx, sub, fields)),
                 note_type=44814640, note_class=36716165, vid=dx_vid)
        suv = ctx.normal(18 if (dlbcl or hl or ptcl) else 9, 5, 3, 40)
        if stage == "I":
            n_reg, dist = 1, ""
        elif stage == "II":
            n_reg, dist = ctx.randint(2, 3), ", all on the same side of the diaphragm"
        elif stage == "III":
            n_reg, dist = ctx.randint(4, 9), ", on both sides of the diaphragm"
        else:
            n_reg, dist = ctx.randint(2, 9), ""
        if extranodal:
            sites = [ctx.choice(EXTRANODAL)]
            if ctx.bern(0.4):
                other = ctx.choice(EXTRANODAL)
                if other not in sites:
                    sites.append(other)
            extra = f"Non-contiguous extranodal involvement: {', '.join(sites)}."
        else:
            extra = "No extranodal involvement."
        ctx.note(p, pet_day, PET_REPORT.format(n=n_reg, s="" if n_reg == 1 else "s", primary=primary, dist=dist, suv=suv,
                                               stage=stage, extra=extra), vid=dx_vid)
        row = ctx.disease_row(p, dx_vid, diagnosis_date=index, histology_icdo3_code=code)
        row.update(fields)

        # ---- 2) 1차 치료
        last = ctx.days(index, 5)
        outcome = ctx.choice(["cured", "relapse", "refractory"], p=([0.6, 0.35, 0.05] if fl else [0.8, 0.15, 0.05]) if (fl or hl)
                             else [0.68, 0.22, 0.10])
        watch_wait = (fl or mzl) and adv and ctx.bern(0.5)
        end1, resp_ok, regimen = None, False, None
        if watch_wait:
            ctx.note(p, bm_day, "Low tumor burden indolent lymphoma (GELF criteria not met). Plan: watch and wait with 3-monthly follow-up.",
                     note_type=32831, note_class=36716177, vid=dx_vid)
            outcome = "cured"
        else:
            s1 = ctx.days(index, ctx.randint(10, 25))
            if hl:
                regimen, drugs, cyc_n, cd, intent, inp = "ABVD", ABVD, 12 if adv else 8, 14, 5, False
            elif fl or mzl:
                regimen, drugs, cyc_n, cd, intent, inp = "R-CVP", R_CVP, 6, 21, 3, False
            elif ptcl:
                regimen, drugs, cyc_n, cd, intent, inp = "CHOP", CHOP, 6, 21, 5, True
            else:
                cyc = 4 if (not adv and not bulky and dlbcl) else 6
                regimen, drugs, cyc_n, cd, intent, inp = "R-CHOP", R_CHOP, cyc, 21, 5 if dlbcl else 3, True
            rt = (not adv and (hl or dlbcl) and ctx.bern(0.6)) and outcome != "refractory"
            if outcome == "refractory":
                cyc_n = 2
            sid, e1, cyc = ctx.sact(p, regimen, drugs, s1, cyc_n, intent, ecog=ecog, response="PD" if outcome == "refractory" else "CR",
                                    cycle_days=cd, inpatient_first=inp)
            ctx.monitor(p, cyc, drugs)
            end1 = e1; last = max(last, e1)
            interim = ctx.days(cyc[2], -1) if len(cyc) >= 3 else ctx.days(e1, 10)
            ds = 5 if outcome == "refractory" else ctx.choice([1, 2, 3, 4], p=[0.2, 0.35, 0.3, 0.15])
            last = max(last, _response(ctx, p, interim, "interim PET2", ds))
            first_sid = sid
            if outcome == "refractory":
                ctx.sact_update(sid, date_of_progression=interim, recurrence_anatomic_site=primary)
                last, dead = _salvage(ctx, p, sub, ecog, primary, interim, last, True)
                if dead:
                    ctx.finalize_person(p)
                    continue
                resp_ok = p.__dict__.get("_remission", False)
            else:
                eot_base = e1
                if rt:
                    rt_day = ctx.days(e1, ctx.randint(21, 35))
                    ctx.procedure(p, rt_day, 4181206, vid=ctx.visit_on(p, rt_day))
                    ctx.note(p, rt_day, f"Involved-site radiotherapy to {primary}, {30 if hl else 36} Gy started.",
                             note_type=32831, note_class=36716177)
                    eot_base = ctx.days(rt_day, 21 if hl else 25)
                    last = max(last, rt_day)
                eot = ctx.days(eot_base, ctx.randint(21, 35))
                last = max(last, _response(ctx, p, eot, "end of treatment", ctx.choice([1, 2, 3], p=[0.3, 0.4, 0.3])))
                resp_ok = True
                # 리툭시맙 유지 (여포성·외투세포 일부)
                ms = ctx.days(eot, ctx.randint(30, 60))
                if (fl or mcl) and ctx.bern(0.6) and ms <= ctx.days(ctx.today, -120):
                    _, me, mcyc = ctx.sact(p, "Rituximab maintenance", [1314273], ms, ctx.randint(4, 8), 4, ecog=ecog,
                                           response="CR", cycle_days=56)
                    ctx.monitor(p, mcyc, [1314273], ae_p=0.1)
                    end1 = max(end1, me); last = max(last, me)

        # ---- 3) 재발·구제, 추적
        dead = False
        if outcome == "relapse" and not watch_wait:
            rel = ctx.days(end1, ctx.randint(150, 900))
            if rel <= ctx.days(ctx.today, -240):
                fu_from = _followups(ctx, p, last, rel)
                site = ctx.choice(NODAL_SITES) + ("; " + ctx.choice(EXTRANODAL) if ctx.bern(0.4) else "")
                rvid = ctx.visit_on(p, rel)
                ctx.procedure(p, rel, 4305790, vid=rvid)
                ctx.note(p, rel, f"FDG PET/CT: new hypermetabolic lesions ({site}). Relapsed lymphoma.", vid=rvid)
                ctx.sact_update(first_sid, date_of_progression=rel, recurrence_anatomic_site=site.split(";")[0])
                last = max(last, fu_from, rel)
                last, dead = _salvage(ctx, p, sub, ecog, primary, rel, last, False)
        if dead:
            ctx.finalize_person(p)
            continue
        _followups(ctx, p, last, ctx.today)
        ctx.finalize_person(p)


# ----------------------------------------------------------------------------------------------- helpers
def _subtype_fields(ctx, sub, age, ecog, ldh_high, leuk, ki67, adv, extranodal):
    """아형별 선택 항목. 다른 아형 전용 항목은 채우지 않는다."""
    f = {}
    if sub == DLBCL:
        f["cell_of_origin"] = ctx.choice(["GCB", "ABC/non-GCB", "unclassifiable"], p=[0.45, 0.40, 0.15])
        de = ctx.bern(0.3)
        f["double_expressor_yn"] = int(de)
        f["double_hit_triple_hit_status"] = ctx.choice(["Not detected", "Double-hit (MYC + BCL2)", "Triple-hit"],
                                                       p=[0.9, 0.07, 0.03]) if (de or ctx.bern(0.3)) else None
        f["t_14_18_result"] = ctx.choice(["Positive", "Negative"], p=[0.2, 0.8]) if ctx.bern(0.6) else None
    elif sub == FL:
        f["t_14_18_result"] = ctx.choice(["Positive", "Negative"], p=[0.85, 0.15])
    elif sub == MCL:
        f["t_11_14_result"] = ctx.choice(["Positive", "Negative"], p=[0.92, 0.08])
        pts = (0 if age < 50 else 1 if age < 60 else 2 if age < 70 else 3) + (2 if ecog >= 2 else 0) \
            + (3 if ldh_high and ctx.bern(0.4) else 2 if ldh_high else ctx.choice([0, 1])) \
            + (0 if leuk < 6.7 else 1 if leuk < 10 else 2 if leuk < 15 else 3)
        f["mipi_score"] = min(pts, 11)
        grade = (0 if pts <= 3 else 1 if pts <= 5 else 2) + (1 if ki67 >= 30 else 0)
        f["mipi_c_risk_group"] = ["Low", "Low-intermediate", "High-intermediate", "High"][min(grade, 3)]
    elif sub == HL and adv:
        f["hodgkin_ips_score"] = min(7, ctx.randint(0, 3) + int(ctx.bern(0.3)) + int(ctx.bern(0.3)) + int(ctx.bern(0.2)))
    elif sub == PTCL:
        f["pit_score"] = min(4, int(age > 60) + int(ecog >= 2) + int(ldh_high) + int(ctx.bern(0.25)))
    if sub in (DLBCL, FL, MCL) and ctx.bern(0.3):
        f["minimal_residual_disease_result"] = ctx.choice(["Negative", "Positive (1e-4)", "Not evaluable"], p=[0.7, 0.2, 0.1])
    if sub in (DLBCL, HL, PTCL) and ctx.bern(0.25):
        f["ctdna_result"] = ctx.choice(["Not detected", "Detected"], p=[0.45, 0.55])
    return f


def _ihc_text(ctx, sub, f):
    """면역염색 소견. DLBCL 은 Hans 알고리즘 결과가 cell_of_origin 과 같고, 외투세포는 cyclin D1 이 t(11;14) 와 같다."""
    if sub == DLBCL:
        coo = f["cell_of_origin"]
        if coo == "unclassifiable":
            return "CD20 positive; CD10, BCL6 and MUM1 not interpretable (limited viable tissue), Hans algorithm cannot classify"
        if coo == "GCB":      # CD10 양성, 또는 CD10 음성이면서 BCL6 양성·MUM1 음성
            cd10, bcl6, mum1 = ("positive", "positive", "negative") if ctx.bern(0.7) else ("negative", "positive", "negative")
        else:                 # CD10 음성이면서 MUM1 양성 (BCL6 무관)
            cd10, bcl6, mum1 = "negative", ctx.choice(["positive", "negative"]), "positive"
        de = "present (double-expressor)" if f.get("double_expressor_yn") else "absent"
        return (f"CD20 positive, CD10 {cd10}, BCL6 {bcl6}, MUM1 {mum1}. Cell of origin by Hans algorithm: {coo}. "
                f"MYC/BCL2 protein co-expression {de}")
    if sub == MCL:
        cyclin = "positive" if f["t_11_14_result"] == "Positive" else "negative"
        return f"CD20 positive, CD5 positive, Cyclin D1 {cyclin}, SOX11 positive"
    return IHC_TXT[sub]


def _followups(ctx, p, start, until):
    """3~6개월 간격 추적 외래(CT + 검사). 마지막 방문일을 반환."""
    fu = ctx.days(start, ctx.randint(80, 120)); last = start; k = 0
    while fu < ctx.days(until, -20) and fu <= ctx.today and k < 12:
        fvid = ctx.visit_on(p, fu)
        ctx.procedure(p, fu, 4207701, vid=fvid)
        ctx.labs(p, fu, [3000963, 3022250], vid=fvid)
        last = fu
        fu = ctx.days(fu, ctx.randint(85, 185)); k += 1
    return last


def _response(ctx, p, day, timepoint, ds):
    """PET 반응평가(처치 + 판독 노트)."""
    vid = ctx.visit_on(p, day)
    ctx.procedure(p, day, 4305790, vid=vid)
    resp = {1: "Complete metabolic response", 2: "Complete metabolic response", 3: "Complete metabolic response",
            4: "Partial metabolic response", 5: "Progressive metabolic disease"}[ds]
    ctx.note(p, day, RESP_REPORT.format(tp=timepoint, ds=ds, resp=resp), vid=vid)
    return day


def _salvage(ctx, p, sub, ecog, primary, pd_day, last, refractory):
    """구제요법 -> 반응 PET -> 자가이식 / CAR-T / 진행 -> 일부 사망. (last, dead) 반환."""
    hl, dlbcl = sub == HL, sub == DLBCL
    s2 = ctx.days(pd_day, ctx.randint(7, 21))
    p._remission = False
    if s2 > ctx.today or (p.death_date is not None and s2 > p.death_date):
        return last, False
    if hl:
        regimen, drugs, cyc_n, dd_days = "Brentuximab vedotin", [1305058], 4, None
    elif sub != PTCL:
        regimen, drugs, cyc_n, dd_days = "R-GDP", R_GDP, 3, DEX4
    else:
        regimen, drugs, cyc_n, dd_days = "GDP", GDP, 3, DEX4
    sid, e2, cyc2 = ctx.sact(p, regimen, drugs, s2, cyc_n, 6, ecog=min(ecog + 1, 3), response=None, drug_days=dd_days)
    ctx.monitor(p, cyc2, drugs, ae_p=0.5)
    last = max(last, e2)
    resp_day = ctx.days(e2, ctx.randint(14, 28))
    if resp_day > ctx.today:
        return last, False
    sensitive = ctx.bern(0.35 if refractory else 0.7)
    ds = ctx.choice([2, 3, 4], p=[0.4, 0.4, 0.2]) if sensitive else 5
    last = max(last, _response(ctx, p, resp_day, "end of treatment", ds))
    ctx.sact_update(sid, best_overall_response=RESP_OF_DS[ds])
    if not sensitive:
        ctx.sact_update(sid, date_of_progression=resp_day, recurrence_anatomic_site=primary)
    if sensitive and p.age_at_index <= 68 and ecog <= 2 and ctx.days(resp_day, 120) <= ctx.today:
        # 자가조혈모세포이식 (입원 21일)
        coll = ctx.days(resp_day, ctx.randint(20, 30))
        ctx.procedure(p, coll, 4283893, vid=ctx.visit_on(p, coll))                    # 조혈모세포 채집
        sct = ctx.days(coll, ctx.randint(10, 20))
        svid = ctx.visit(p, sct, INPATIENT, los=21)
        ctx.procedure(p, sct, 4030027, vid=svid)
        ctx.note(p, sct, "High-dose chemotherapy (BEAM) followed by autologous peripheral blood stem cell infusion (day 0).",
                 note_type=32831, note_class=36716177, vid=svid)
        ctx.labs(p, ctx.days(sct, 7), [3000963, 3010813, 3017732, 3024929], vid=svid,
                 shifts={3017732: -3.5, 3010813: -5.0, 3024929: -150, 3000963: -3.0})
        ctx.ae(p, ctx.days(sct, 6), 4304213, 3, vid=svid, action=1)
        ctx.condition(p, ctx.days(sct, 6), 4304213, vid=svid)
        ctx.drug(p, ctx.days(sct, 5), 1301125, 7, vid=svid, freq=1)
        last = max(last, ctx.days(sct, 21))
        post = ctx.days(sct, ctx.randint(90, 110))
        if post <= ctx.today:
            last = max(last, _response(ctx, p, post, "follow-up", ctx.choice([1, 2, 3])))
        p._remission = True
        return last, False
    if dlbcl and (not sensitive or ctx.bern(0.3)) and ctx.days(resp_day, 120) <= ctx.today:
        # CAR-T: 성분채집 -> 림프구감소(입원 16일) -> 주입 -> CRS
        leuk = ctx.days(resp_day, ctx.randint(7, 14))
        ctx.procedure(p, leuk, 4283893, vid=ctx.visit_on(p, leuk))
        ld = ctx.days(leuk, ctx.randint(24, 35))
        cvid = ctx.visit(p, ld, INPATIENT, los=16)
        sid3, e3, _ = ctx.sact(p, "CD19 CAR-T lymphodepletion (cyclophosphamide)", [1310317], ld, 3, 6, ecog=min(ecog + 1, 3),
                               cycle_days=1)
        inf = ctx.days(ld, 5)
        ctx.procedure(p, inf, 4053096, vid=cvid)
        ctx.note(p, inf, "CD19-directed CAR-T infused on day 0 after fludarabine/cyclophosphamide lymphodepletion.",
                 note_type=32831, note_class=36716177, vid=cvid)
        crs_day = ctx.days(inf, ctx.randint(1, 5))
        g = ctx.choice([1, 2, 3], p=[0.4, 0.4, 0.2])
        ctx.ae(p, crs_day, 4185711, g, vid=cvid, action=1, causality=1)
        ctx.condition(p, crs_day, 4185711, vid=cvid)
        ctx.labs(p, crs_day, [3020460, 3010813, 3017732], vid=cvid, shifts={3020460: 60 * g, 3017732: -3.0})
        last = max(last, ctx.days(ld, 16))
        d30 = ctx.days(inf, 30)
        ds30 = ctx.choice([1, 2, 3], p=[0.4, 0.35, 0.25]) if ctx.bern(0.55) else 5
        if d30 <= ctx.today:
            last = max(last, _response(ctx, p, d30, "follow-up", ds30))
            ctx.sact_update(sid3, best_overall_response=RESP_OF_DS[ds30])
            if ds30 == 5:
                ctx.sact_update(sid3, date_of_progression=d30, recurrence_anatomic_site=primary)
                return _disease_death(ctx, p, last)
        p._remission = True
        return last, False
    if not sensitive:
        return _disease_death(ctx, p, last)
    p._remission = True
    return last, False


def _disease_death(ctx, p, last):
    """진행 후 30~150일 내 사망 (오늘 이후이면 생존 추적으로 남김). 이후 이벤트는 만들지 않는다."""
    dd = ctx.days(last, ctx.randint(30, 150))
    if dd > ctx.today:
        return last, False
    ctx.visit(p, ctx.days(dd, -3), INPATIENT, los=3)
    ctx.set_death(p, dd)
    return dd, True

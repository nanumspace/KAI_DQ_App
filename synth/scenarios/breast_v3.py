# -*- coding: utf-8 -*-
"""
유방암 코호트 시나리오 (v3)

v1 유방암 여정(`breast.py`)을 v3 테이블로 옮겼다. 특화 테이블 BREAST_CANCER 는 환자당 1행(진단 방문)이며
진단일, 폐경 상태, 임신/분만/출산 후 1년/가임력 보존 치료 여부를 담는다 (남성은 해당 항목이 모두 4=Not Applicable).

여정: 진단 외래(유방촬영·침생검) → 병리/IHC → 병기 → 선행항암(AC-T / TCH) → 수술 → 보조항암/trastuzumab →
      방사선 → 내분비치료(tamoxifen/letrozole/anastrozole) → 추적, 재발 시 전이성 요법.
호르몬제(category 3)도 모두 SACT 로 묶는다 (SEM3-SACT-006).
"""
from framework_v3 import *

BC_INV, BC_DCIS = 4112853, 4162253
HIST = {"IDC": "Invasive ductal carcinoma, NOS", "ILC": "Invasive lobular carcinoma", "MUC": "Mucinous carcinoma",
        "DCIS": "Ductal carcinoma in situ"}
LOC = [("UOQ", "Upper outer quadrant"), ("UIQ", "Upper inner quadrant"), ("LOQ", "Lower outer quadrant"),
       ("LIQ", "Lower inner quadrant"), ("CEN", "Central portion")]
LOC_P = [0.5, 0.15, 0.13, 0.1, 0.12]
TSIZE = {"Tis": (0.5, 4.0), "T1a": (0.2, 0.5), "T1b": (0.6, 1.0), "T1c": (1.1, 2.0), "T2": (2.1, 5.0), "T3": (5.1, 8.0),
         "T4b": (3.0, 9.0)}
STAGE_TNM = {"I": ([("T1a", "N0"), ("T1b", "N0"), ("T1c", "N0")], [0.1, 0.25, 0.65]),
             "II": ([("T1c", "N1"), ("T2", "N0"), ("T2", "N1")], [0.2, 0.4, 0.4]),
             "III": ([("T3", "N1"), ("T2", "N2"), ("T4b", "N1")], [0.4, 0.35, 0.25]),
             "IV": ([("T2", "N1"), ("T3", "N2"), ("T4b", "N2"), ("T2", "N0")], [0.35, 0.3, 0.2, 0.15])}
SUBTYPES = ["HR+/HER2-", "HR+/HER2+", "HR-/HER2+", "TNBC"]
MET_SITES = [("Bone",), ("Liver",), ("Lung",), ("Brain",), ("Distant lymph node",)]
MET_P = [0.4, 0.2, 0.2, 0.08, 0.12]
REC_SITES = [("Ipsilateral breast / chest wall", False), ("Regional axillary lymph node", False)] + \
            [(s[0], True) for s in MET_SITES]
REC_P = [0.2, 0.1, 0.28, 0.14, 0.14, 0.06, 0.08]
AE_CHEMO = ((27674, 0.18), (432791, 0.08), (301794, 0.2), (4304213, 0.06), (439777, 0.12), (4166735, 0.12),
            (4223659, 0.12), (4265412, 0.04), (196523, 0.05), (4141062, 0.03))
AE_CAPE = ((196523, 0.3), (4265412, 0.2), (140214, 0.25), (4223659, 0.15), (27674, 0.1))
AE_HORM = ((4223659, 0.6), (140214, 0.2), (27674, 0.2))
LAB_FEW = (3000963, 3016723)

MMG_REPORT = ("Bilateral digital mammography with tomosynthesis. {lat} breast: {size} cm {shape} at the {loc}. Axilla: {ax}. "
              "Contralateral breast: no suspicious finding. Impression: BI-RADS {birads}. Recommend ultrasound-guided core needle biopsy.")
BX_REPORT = ("Breast, {lat}, {loc}, ultrasound-guided core needle biopsy: {hist}. Nottingham histologic grade {grade}. "
             "Immunohistochemistry: ER {er}% ({erp}), PR {pr}% ({prp}), HER2 IHC {her2}{fish}, Ki-67 labeling index {ki}%. "
             "Molecular subtype: {sub}.")
CT_REPORT = ("CT chest, abdomen and pelvis with contrast. {lat} breast mass {size} cm. {node}. {met} "
             "Impression: breast cancer, c{t}{n}{m}.")
SP_REPORT = ("Breast, {lat}, {op}{slnb}: {hist}. Tumor size {size} cm. Lymphovascular invasion: {lvi}. "
             "Resection margins: {margin}. Lymph nodes: {psln}/{tsln} positive. Pathologic stage {t}{n}M0.{resp}")


def _plan(ctx, age, gender):
    """환자 수준 임상 특성(조직형/병기/아형/폐경/동반질환)."""
    st = {}
    st["hist"] = "IDC" if gender == MALE else ctx.choice(["IDC", "ILC", "MUC", "DCIS"], p=[0.74, 0.09, 0.04, 0.13])
    dcis = st["hist"] == "DCIS"
    st["loc"] = ctx.choice(LOC, p=LOC_P)
    st["lat"] = ctx.choice(["R", "L"])
    if dcis:
        st["stage"], T, N, M = "0", "Tis", "N0", "M0"
    else:
        st["stage"] = ctx.choice(["I", "II", "III", "IV"], p=[0.40, 0.35, 0.15, 0.10])
        opts, pr = STAGE_TNM[st["stage"]]
        i = ctx.choice(list(range(len(opts))), p=pr)
        T, N = opts[i]
        M = "M1" if st["stage"] == "IV" else "M0"
    st.update(T=T, N=N, M=M, size=round(ctx.rand(*TSIZE[T]), 1))
    if dcis:
        sub = "HR+/HER2-" if ctx.bern(0.8) else "TNBC"
    elif gender == MALE:
        sub = "HR+/HER2-"
    else:
        sub = ctx.choice(SUBTYPES, p=[0.65, 0.10, 0.08, 0.17])
    st["sub"], st["hr"], st["her2"] = sub, sub.startswith("HR+"), "HER2+" in sub
    st["er"] = ctx.randint(60, 100) if st["hr"] else 0
    st["pr"] = (0 if ctx.bern(0.2) else ctx.randint(5, 100)) if st["hr"] else 0
    if st["her2"]:
        st["her2_ihc"] = 3 if ctx.bern(0.8) else 2
        st["fish"] = round(ctx.rand(2.2, 8.0), 2) if st["her2_ihc"] == 2 else None
    else:
        st["her2_ihc"] = ctx.choice([0, 1, 2], p=[0.5, 0.35, 0.15])
        st["fish"] = round(ctx.rand(1.0, 1.7), 2) if st["her2_ihc"] == 2 else None
    st["ki67"] = ctx.randint(40, 90) if sub == "TNBC" and not dcis else (ctx.randint(20, 70) if st["her2"] else ctx.randint(5, 35))
    if dcis:
        st["grade"] = ctx.choice([1, 2, 3], p=[0.3, 0.45, 0.25])
    elif sub == "TNBC" or st["her2"]:
        st["grade"] = ctx.choice([2, 3], p=[0.3, 0.7])
    else:
        st["grade"] = ctx.choice([1, 2, 3], p=[0.25, 0.55, 0.2])
    if gender == MALE:
        st["meno"] = 4
    elif age < 45:
        st["meno"] = 1 if ctx.bern(0.97) else 3
    elif age < 55:
        st["meno"] = ctx.choice([1, 2, 3], p=[0.48, 0.48, 0.04])
    else:
        st["meno"] = 2 if ctx.bern(0.97) else 3
    st["ecog"] = ctx.choice([0, 1, 2], p=[0.3, 0.5, 0.2]) if st["stage"] == "IV" else ctx.choice([0, 1, 2], p=[0.6, 0.35, 0.05])
    st["htn"] = ctx.bern(0.2 + (0.2 if age > 60 else 0))
    st["dm"] = ctx.bern(0.08 + (0.1 if age > 60 else 0))
    st["hl"] = ctx.bern(0.2)
    return st


def _breast_row(ctx, p, st, vid, index, age, plan_chemo):
    """BREAST_CANCER 환자당 1행: 진단일 + 폐경/임신/분만/출산 후/가임력 보존."""
    meno = st["meno"]
    if p.gender == MALE:
        return ctx.disease_row(p, vid, diag_rgst_ymd=index, menopause_status=4, pregnant_at_diagnosis=4,
                               history_of_live_birth=4, postpartum_at_diagnosis=4, fertility_history=4,
                               fertility_treatment_type=None)
    live = age >= 23 and ctx.bern(0.78)
    unknown_hx = ctx.bern(0.02)
    pregnant = 1 if (meno == 1 and 18 <= age <= 45 and ctx.bern(0.03)) else 2
    post = 1 if (live and age <= 42 and meno == 1 and ctx.bern(0.05)) else 2
    fert = meno == 1 and age <= 40 and plan_chemo and ctx.bern(0.55)
    f = dict(diag_rgst_ymd=index, menopause_status=meno, pregnant_at_diagnosis=pregnant,
             history_of_live_birth=3 if unknown_hx else (1 if live else 2),
             postpartum_at_diagnosis=post, fertility_history=1 if fert else 2,
             fertility_treatment_type=ctx.choice([1, 2, 3, 4, 5], p=[0.45, 0.2, 0.1, 0.1, 0.15]) if fert else None)
    if unknown_hx:
        f["postpartum_at_diagnosis"] = 3 if post == 2 else post
    return ctx.disease_row(p, vid, **f)


def _sact(ctx, p, name, drugs, start, cycles, intent, ecog, resp, cycle_days=None, oral=False, limit=None):
    """SACT 래퍼: 마지막 사이클 투여가 오늘/사망/limit 을 넘지 않도록 주기 수를 줄인다. 1주기도 못 넣으면 None."""
    cd = cycle_days or max(CONCEPTS["drugs"][c]["cycle_days"] or 21 for c in drugs)
    hi = min(x for x in (ctx.today, p.death_date, limit) if x is not None)
    span = cd if (oral or any(CONCEPTS["drugs"][c]["route"] == "PO" for c in drugs)) else 1
    room = (hi - start).days - span + 1
    if room < 0:
        return None
    cycles = min(cycles, room // cd + 1)
    sid, end, cyc = ctx.sact(p, name, drugs, start, cycles, intent, ecog=ecog, response=resp, cycle_days=cd, oral=oral)
    return sid, end, cyc


def _mon(ctx, p, cyc, drugs, pool=AE_CHEMO, ae_p=0.45, labs=True):
    ctx.monitor(p, cyc, drugs, ae_p=ae_p, ae_pool=pool, labs=(3000963, 3010813, 3017732, 3024929, 3016723, 3013721, 3006923) if labs else LAB_FEW)


def _surgery(ctx, p, st, day, nact, salvage=False):
    """수술 입원. 반환 (svid, bcs, los)."""
    T = st["T"]
    if salvage or p.gender == MALE:
        bcs = False
    elif st["hist"] == "DCIS":
        bcs = ctx.bern(0.7)
    elif nact:
        bcs = ctx.bern(0.5)
    else:
        bcs = T in ("T1a", "T1b", "T1c", "T2") and st["size"] <= 3.0 and ctx.bern(0.7)
    los = 3 if bcs else 6
    svid = ctx.visit(p, day, INPATIENT, los=los)
    ctx.procedure(p, day, 4118029 if bcs else 4234573, vid=svid)
    slnb = not (st["hist"] == "DCIS" and bcs) and not salvage
    if slnb:
        ctx.procedure(p, day, 4090256, vid=svid)
    st["slnb"] = slnb
    ctx.labs(p, ctx.days(day, 1), [3000963, 3010813, 3016723], vid=svid)
    if ctx.bern(0.15):
        ctx.ae(p, ctx.days(day, 2), 437663, 1, vid=svid)
    return svid, bcs, los


def _surg_path(ctx, p, st, op_day, nact, bcs, salvage=False):
    """외과병리 노트. 반환 (path_day, pN, pcr)."""
    T, N = st["T"], st["N"]
    path_day = ctx.days(op_day, ctx.randint(4, 9))
    pvid = ctx.visit_on(p, path_day)
    pcr = False
    if salvage:
        pT, pN, psize = "T2", "NX", round(ctx.rand(1.0, 4.0), 1)
    elif nact:
        pcr = ctx.bern({"HR+/HER2+": 0.5, "HR-/HER2+": 0.6, "TNBC": 0.45}.get(st["sub"], 0.12))
        if pcr:
            pT, pN, psize = "yT0", "yN0", 0.0
        else:
            t = ctx.choice(["T1a", "T1b", "T1c", "T2"], p=[0.15, 0.25, 0.35, 0.25])
            pT, psize = "y" + t, round(ctx.rand(*TSIZE[t]), 1)
            pN = "y" + ("N0" if (N == "N0" or ctx.bern(0.5)) else ctx.choice(["N1", "N2"], p=[0.7, 0.3]))
    else:
        t = "Tis" if st["hist"] == "DCIS" else (T if ctx.bern(0.8) else ctx.choice(["T1b", "T1c", "T2"]))
        pT, psize = t, round(ctx.rand(*TSIZE[t]), 1)
        if st["hist"] == "DCIS":
            pN = "N0" if st["slnb"] else "NX"
        else:
            pN = N if ctx.bern(0.75) else ctx.choice(["N0", "N1", "N2"], p=[0.5, 0.35, 0.15])
    nn = pN.lstrip("y")
    if nn == "N2":                      # pN2 = 양성 림프절 4~9개 → 전액와 림프절 수 기준
        tot = ctx.randint(6, 14)
        pos = ctx.randint(4, min(9, tot))
    elif st["slnb"]:
        tot = ctx.randint(1, 5)
        pos = 0 if nn == "N0" else ctx.randint(1, min(3, tot))
    else:
        tot = pos = "-"
    lvi = (not pcr) and ctx.bern(0.3 if nn != "N0" else 0.12)
    resp = ""
    if nact:
        resp = " Miller-Payne grade 5 (no residual invasive tumor)." if pcr else f" Miller-Payne grade {ctx.randint(2, 4)} (partial response)."
    ctx.note(p, path_day, SP_REPORT.format(
        lat="right" if st["lat"] == "R" else "left", op="partial mastectomy" if bcs else "total mastectomy",
        slnb=" with sentinel lymph node biopsy" if st["slnb"] else "",
        hist="No residual invasive carcinoma (pathologic complete response)" if pcr else HIST[st["hist"]], size=psize,
        lvi="present" if lvi else "absent", margin=ctx.choice(["negative margin (>= 2 mm)", "close margin (< 2 mm)"], p=[0.85, 0.15]),
        psln=pos, tsln=tot, t=pT, n=pN, resp=resp), note_type=44814640, note_class=36716165, vid=pvid)
    return path_day, pN, pcr


def _rt(ctx, p, day, kind):
    rvid = ctx.visit_on(p, day)
    ctx.procedure(p, day, 4181206, vid=rvid)
    fx = ctx.choice([16, 25], p=[0.6, 0.4]) if kind == "WBI" else 25
    return ctx.days(day, int(fx * 1.4) + 3)


def _endocrine(ctx, p, st, start, ecog, limit=None):
    """보조 내분비치료 (84일 처방 단위, 최대 5년)."""
    if st["meno"] == 2 and ctx.bern(0.9):
        drug, name = (1348265, "Letrozole") if ctx.bern(0.6) else (1319247, "Anastrozole")
    else:
        drug, name = 1436678, "Tamoxifen"
    cycles = ctx.randint(2, 12) if ctx.bern(0.1) else 22
    r = _sact(ctx, p, name, [drug], start, cycles, 2, ecog, "NE", cycle_days=84, oral=True, limit=limit)
    if r is not None:
        _mon(ctx, p, r[2], [drug], AE_HORM, ae_p=0.08, labs=False)
    return r


def _palliative(ctx, p, st, start, ecog, first_intent=3):
    """전이/재발 후 전신치료 순차 라인. 반환 (last_end, last_sid)."""
    if st["her2"]:
        plan = [("Docetaxel + Trastuzumab", [1315942, 1387104], 21, 6, 2, first_intent, AE_CHEMO, 0.45, False),
                ("Trastuzumab maintenance", [1387104], 21, ctx.randint(4, 16), 2, 4, AE_HORM, 0.1, False),
                ("Capecitabine", [1337620], 21, ctx.randint(4, 8), 1, 3, AE_CAPE, 0.4, True)]
    elif st["hr"]:
        drug, name = (1348265, "Letrozole") if st["meno"] == 2 else (1436678, "Tamoxifen")
        plan = [(name, [drug], 28, ctx.randint(6, 24), 3, first_intent, AE_HORM, 0.08, True),
                ("Weekly Paclitaxel", [1378382], 7, ctx.randint(8, 18), 1, 3, AE_CHEMO, 0.45, False),
                ("Capecitabine", [1337620], 21, ctx.randint(4, 8), 1, 3, AE_CAPE, 0.4, True)]
    else:
        plan = [("Weekly Paclitaxel + Carboplatin", [1378382, 1344905], 7, 12, 1, first_intent, AE_CHEMO, 0.45, False),
                ("Capecitabine", [1337620], 21, ctx.randint(4, 8), 1, 3, AE_CAPE, 0.4, True)]
    last_end, last_sid, cur, cur_ecog = start, None, start, ecog
    for i, (name, drugs, cd, cycles, cat, intent, aes, ae_p, oral) in enumerate(plan):
        r = _sact(ctx, p, name, drugs, cur, cycles, intent, cur_ecog, "NE", cycle_days=cd, oral=oral)
        if r is None:
            break
        sid, e, cyc = r
        last_end, last_sid = e, sid
        _mon(ctx, p, cyc, drugs, aes, ae_p=ae_p, labs=cat != 3)
        if i + 1 < len(plan) and plan[i + 1][5] == 4:          # 유지요법으로 이어짐
            ctx.sact_update(sid, best_overall_response=ctx.choice(["PR", "SD", "CR"], p=[0.6, 0.3, 0.1]))
            cur = ctx.days(e, 21)
            continue
        progressed = ctx.bern(0.65) and ctx.days(e, 60) <= ctx.today
        if progressed:
            pd_day = ctx.days(e, ctx.randint(0, 45))
            site = ctx.choice(MET_SITES, p=MET_P)[0]
            pvid = ctx.visit_on(p, pd_day)
            ctx.procedure(p, pd_day, 4207701, vid=pvid)
            ctx.note(p, pd_day, f"CT chest/abdomen/pelvis: interval increase of known lesions and new {site.lower()} metastases. "
                                "Progressive disease by RECIST 1.1.", vid=pvid)
            ctx.sact_update(sid, date_of_progression=pd_day, recurrence_anatomic_site=site,
                            best_overall_response=ctx.choice(["PR", "SD", "PD"], p=[0.35, 0.4, 0.25]))
            last_end = pd_day
            cur_ecog = min(cur_ecog + 1, 3)
            if cur_ecog <= 2 and ctx.bern(0.75) and i + 1 < len(plan):
                cur = ctx.days(pd_day, ctx.randint(7, 21))
                continue
            break
        ctx.sact_update(sid, best_overall_response=ctx.choice(["PR", "SD", "CR"], p=[0.55, 0.35, 0.1]))
        break
    return last_end, last_sid


def _die(ctx, p, last_end):
    dd = ctx.days(last_end, ctx.randint(30, 300))
    if dd > ctx.today:
        return False
    ctx.set_death(p, dd)
    ctx.visit(p, ctx.days(dd, -2), INPATIENT, los=2)
    return True


def generate(ctx: CtxV3, n=100):
    for i in range(n):
        gender = MALE if i % 100 == 50 else FEMALE          # 약 1% 남성
        age = int(ctx.normal(66 if gender == MALE else 52, 11, 26, 88, 0))
        index = D(2019, 1, 1) + dt.timedelta(days=ctx.randint(0, 2190))
        p = ctx.person(gender, age, index)
        st = _plan(ctx, age, gender)
        dcis = st["hist"] == "DCIS"
        T, N, M, sub, lat = st["T"], st["N"], st["M"], st["sub"], st["lat"]
        loc_nm = st["loc"][1]
        ecog = st["ecog"]
        lat_en = "Right" if lat == "R" else "Left"
        size = st["size"]

        # 치료 계획 플래그 (가임력 보존 결정에 필요하므로 미리 결정)
        big = T not in ("Tis", "T1a", "T1b") or N != "N0"
        if M == "M1" or dcis:
            plan_nact, plan_adj_chemo = False, False
        elif st["her2"]:
            plan_nact, plan_adj_chemo = big, not big
        elif sub == "TNBC":
            plan_nact, plan_adj_chemo = big, T == "T1b"
        else:   # HR+/HER2-
            plan_nact = (T in ("T3", "T4b") or N in ("N2", "N3")) and ctx.bern(0.5)
            st["rs"] = ctx.choice([ctx.randint(0, 15), ctx.randint(16, 25), ctx.randint(26, 60)], p=[0.5, 0.35, 0.15])
            st["odx"] = (not plan_nact) and N in ("N0", "N1") and ctx.bern(0.6)
            plan_adj_chemo = (not plan_nact) and ((st["odx"] and st["rs"] >= 26) or (N != "N0" and ctx.bern(0.6)) or (T in ("T3", "T4b")))
        plan_chemo = plan_nact or plan_adj_chemo or M == "M1"

        # ---- 1) 진단 외래: 유방촬영 + 침생검
        dx_vid = ctx.visit(p, index, OUTPATIENT)
        ctx.condition(p, index, BC_DCIS if dcis else BC_INV, vid=dx_vid)
        if st["htn"]: ctx.condition(p, index, 320128, vid=dx_vid)
        if st["dm"]: ctx.condition(p, index, 201826, vid=dx_vid)
        if st["hl"]: ctx.condition(p, index, 432867, vid=dx_vid)
        ctx.procedure(p, index, 4044530, vid=dx_vid)
        ctx.procedure(p, index, 4249893, vid=dx_vid)
        birads = ctx.choice(["4B", "4C", "5"], p=[0.3, 0.4, 0.3]) if dcis else ctx.choice(["4A", "4B", "4C", "5"], p=[0.08, 0.17, 0.3, 0.45])
        ctx.note(p, index, MMG_REPORT.format(
            lat=lat_en, size=size, loc=loc_nm.lower(),
            shape="segmental pleomorphic microcalcifications" if dcis else ctx.choice(["spiculated mass", "irregular hypoechoic mass"], p=[0.7, 0.3]),
            ax="suspicious enlarged lymph node" if N != "N0" else "no abnormal lymph node", birads=birads), vid=dx_vid)
        _breast_row(ctx, p, st, dx_vid, index, age, plan_chemo)

        # ---- 병리/IHC 외래 (3~6일 후)
        path_day = ctx.days(index, ctx.randint(3, 6))
        pv = ctx.visit_on(p, path_day)
        her2_txt = {0: "0", 1: "1+", 2: "2+", 3: "3+"}[st["her2_ihc"]]
        fish_txt = f" (FISH HER2/CEP17 ratio {st['fish']}, {'amplified' if st['her2'] else 'not amplified'})" if st["fish"] else ""
        ctx.note(p, path_day, BX_REPORT.format(lat=lat_en.lower(), loc=loc_nm.lower(), hist=HIST[st["hist"]], grade=st["grade"],
                                                er=st["er"], erp="positive" if st["hr"] else "negative", pr=st["pr"],
                                                prp="positive" if st["pr"] > 0 else "negative", her2=her2_txt, fish=fish_txt,
                                                ki=st["ki67"], sub=sub if not dcis else ("ER-positive DCIS" if st["hr"] else "ER-negative DCIS")),
                 note_type=44814640, note_class=36716165, vid=pv)
        ctx.observation(p, path_day, 4257895, vid=pv, value_number=ecog, value_string=f"ECOG {ecog}")
        ht = ctx.normal(170 if gender == MALE else 158, 5.5, 140, 190)
        wt = ctx.normal(70 if gender == MALE else 58, 9, 38, 110)
        bmi = round(wt / (ht / 100) ** 2, 1)
        ctx.measure(p, path_day, 3036277, ht, vid=pv); ctx.measure(p, path_day, 3025315, wt, vid=pv); ctx.measure(p, path_day, 3038553, bmi, vid=pv)
        if bmi >= 30: ctx.condition(p, path_day, 433736, vid=pv)
        ctx.labs(p, path_day, [3000963, 3010813, 3017732, 3024929, 3016723, 3013721, 3006923, 3020491, 3024128, 3028641], vid=pv)

        # ---- 병기 결정
        if st["stage"] in ("0", "I"):
            stage_day = path_day
        else:
            stage_day = ctx.days(index, ctx.randint(7, 14))
            svid_stage = ctx.visit_on(p, stage_day)
            ctx.procedure(p, stage_day, 4207701, vid=svid_stage)
            ctx.procedure(p, stage_day, 4305790, vid=svid_stage)
            met = ctx.choice(MET_SITES, p=MET_P)[0] if M == "M1" else None
            node = "Enlarged axillary lymph nodes" if N != "N0" else "No significant lymphadenopathy"
            met_txt = f"Multiple metastatic lesions in {met.lower()}." if met else "No distant metastasis."
            ctx.note(p, stage_day, CT_REPORT.format(lat=lat_en, size=size, node=node, met=met_txt, t=T, n=N, m=M), vid=svid_stage)
            ctx.note(p, stage_day, f"Whole body FDG PET-CT. Hypermetabolic {lat_en.lower()} breast mass (SUVmax {round(ctx.rand(3.0, 15.0), 1)}). {node}. {met_txt}", vid=svid_stage)

        # ---- 2) 치료
        surgery_day = None
        last_adj_end = stage_day          # 내분비치료를 제외한 마지막 국소/전신 치료 종료일
        chemo_end = None
        prior_bcs = False
        recur_day = None
        if M == "M1":
            start = ctx.days(stage_day, ctx.randint(7, 21))
            last_end, last_sid = _palliative(ctx, p, st, start, ecog)
            last_adj_end = last_end
            if last_sid is not None and ctx.bern(0.6):
                _die(ctx, p, last_end)
        else:
            nact = plan_nact
            if nact:
                s = ctx.days(index, ctx.randint(14, 28))
                if st["her2"]:
                    drugs = [1315942, 1344905, 1387104]
                    r = _sact(ctx, p, "Docetaxel + Carboplatin + Trastuzumab (TCH)", drugs, s, 6, 1, ecog,
                              ctx.choice(["PR", "CR", "SD"], p=[0.5, 0.4, 0.1]))
                    if r: _mon(ctx, p, r[2], drugs)
                else:
                    r = _sact(ctx, p, "Doxorubicin + Cyclophosphamide (AC)", [1338512, 1310317], s, 4, 1, ecog, ctx.choice(["PR", "SD"], p=[0.7, 0.3]))
                    if r:
                        _mon(ctx, p, r[2], [1338512, 1310317])
                        drugs2 = [1378382, 1344905] if sub == "TNBC" else [1378382]
                        r2 = _sact(ctx, p, "Weekly Paclitaxel + Carboplatin" if sub == "TNBC" else "Weekly Paclitaxel", drugs2,
                                   ctx.days(r[1], 21), 12, 1, ecog, ctx.choice(["PR", "CR", "SD"], p=[0.5, 0.35, 0.15]), cycle_days=7)
                        if r2: _mon(ctx, p, r2[2], drugs2); r = r2
                if r is None:
                    nact = False
                    surgery_day = ctx.days(index, ctx.randint(21, 45))
                else:
                    chemo_end = r[1]
                    surgery_day = ctx.days(r[1], ctx.randint(21, 42))
            else:
                surgery_day = ctx.days(index, ctx.randint(21, 45))
            if surgery_day <= ctx.today:
                svid, bcs, los = _surgery(ctx, p, st, surgery_day, nact)
                prior_bcs = bcs
                spath_day, pN, pcr = _surg_path(ctx, p, st, surgery_day, nact, bcs)
                nn = pN.lstrip("y")
                last_adj_end = ctx.days(surgery_day, los)
                if st.get("odx"):
                    g_day = ctx.days(spath_day, ctx.randint(7, 21))
                    if g_day <= ctx.today:
                        rs = st["rs"]
                        risk = "low" if rs <= 15 else ("intermediate" if rs <= 25 else "high")
                        ctx.note(p, g_day, f"Oncotype DX Breast Recurrence Score assay (surgical specimen): Recurrence Score {rs} ({risk} risk).",
                                 note_type=44814640, note_class=36716165, vid=ctx.visit_on(p, g_day))
                        last_adj_end = max(last_adj_end, g_day)
                # 보조항암 (수술 선행군)
                if plan_adj_chemo and not nact:
                    s = ctx.days(last_adj_end, ctx.randint(21, 35))
                    if st["her2"]:
                        r = _sact(ctx, p, "Weekly Paclitaxel + Trastuzumab (APT)", [1378382, 1387104], s, 12, 2, ecog, "NE", cycle_days=7)
                        if r:
                            _mon(ctx, p, r[2], [1378382, 1387104]); chemo_end = last_adj_end = r[1]
                            r2 = _sact(ctx, p, "Trastuzumab", [1387104], ctx.days(r[1], 21), 13, 2, ecog, "NE")
                            if r2: _mon(ctx, p, r2[2], [1387104], AE_HORM, ae_p=0.08, labs=False); last_adj_end = r2[1]
                    else:
                        r = _sact(ctx, p, "Docetaxel + Cyclophosphamide (TC)", [1315942, 1310317], s, 4, 2, ecog, "NE")
                        if r: _mon(ctx, p, r[2], [1315942, 1310317]); chemo_end = last_adj_end = r[1]
                # 선행항암 후 보조치료
                if nact:
                    s = ctx.days(surgery_day, ctx.randint(28, 42))
                    if st["her2"]:
                        r = _sact(ctx, p, "Trastuzumab", [1387104], s, 11, 2, ecog, "NE")
                        if r: _mon(ctx, p, r[2], [1387104], AE_HORM, ae_p=0.08, labs=False); last_adj_end = r[1]
                    elif sub == "TNBC" and not pcr:
                        r = _sact(ctx, p, "Capecitabine", [1337620], s, 6, 2, ecog, "NE", oral=True)
                        if r: _mon(ctx, p, r[2], [1337620], AE_CAPE, ae_p=0.4); chemo_end = last_adj_end = r[1]
                # 방사선치료
                pmrt = (not bcs) and (T in ("T3", "T4b") or nn in ("N2", "N3") or (nn == "N1" and ctx.bern(0.5)))
                if bcs or pmrt:
                    rt_day = ctx.days(last_adj_end, ctx.randint(21, 42)) if (chemo_end and chemo_end > surgery_day) else ctx.days(surgery_day, ctx.randint(28, 50))
                    if rt_day <= ctx.today:
                        last_adj_end = max(last_adj_end, _rt(ctx, p, rt_day, "WBI" if bcs else "PMRT"))
                p_rec = {"0": 0.03, "I": 0.06, "II": 0.13, "III": 0.28}[st["stage"]] + (0.08 if sub == "TNBC" and not dcis else 0)
                recur_day = ctx.days(last_adj_end, ctx.randint(200, 1500)) if ctx.bern(p_rec) else None
                if recur_day is not None and recur_day > ctx.days(ctx.today, -45):
                    recur_day = None
                # 내분비치료
                if st["hr"] and (not dcis or ctx.bern(0.7)):
                    s = ctx.days(last_adj_end, ctx.randint(14, 30))
                    _endocrine(ctx, p, st, s, ecog, limit=ctx.days(recur_day, -1) if recur_day else None)

        # ---- 3) 추적 및 재발
        fu = ctx.days(last_adj_end, ctx.randint(170, 200))
        recurred = M == "M1"
        k = 0
        while p.death_date is None and fu <= ctx.today and k < 14:
            fvid = ctx.visit_on(p, fu)
            hit = recur_day is not None and not recurred and fu >= recur_day
            ctx.procedure(p, fu, 4207701 if recurred else 4044530, vid=fvid)
            ctx.labs(p, fu, [3000963, 3028641, 3013721] if recurred else [3000963, 3028641], vid=fvid)
            if hit:
                recurred = True
                site_nm, distant = ctx.choice(REC_SITES, p=REC_P)
                ctx.procedure(p, fu, 4207701, vid=fvid)
                ctx.procedure(p, fu, 4305790, vid=fvid)
                ctx.note(p, fu, f"PET-CT: new hypermetabolic lesion(s) in {site_nm.lower()}, consistent with {'distant' if distant else 'locoregional'} recurrence of breast cancer.", vid=fvid)
                start = ctx.days(fu, ctx.randint(7, 21))
                if not distant and site_nm.startswith("Ipsilateral"):
                    sd = ctx.days(fu, ctx.randint(14, 28))
                    if sd <= ctx.today and prior_bcs:       # 이전 전절제술 후 흉벽 재발에는 전절제술을 반복하지 않음
                        _surgery(ctx, p, st, sd, False, salvage=True)
                        _surg_path(ctx, p, st, sd, False, False, salvage=True)
                        start = ctx.days(sd, ctx.randint(30, 45))
                last_end, last_sid = _palliative(ctx, p, st, start, ecog, first_intent=3 if distant else 6)
                if last_sid is not None and ctx.bern(0.5 if distant else 0.25) and _die(ctx, p, last_end):
                    break
                fu = max(fu, last_end)
            fu = ctx.days(fu, ctx.randint(100, 130) if recurred else ctx.randint(170, 200)); k += 1
        ctx.finalize_person(p)

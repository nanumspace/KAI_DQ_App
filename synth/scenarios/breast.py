# -*- coding: utf-8 -*-
"""
유방암 코호트 시나리오 (환자 여정 템플릿)

여정 개요
  1) 진단 외래: 유방촬영(imex: 유방밀도/BI-RADS/미세석회화) + 초음파유도 중심부 침생검(bpsy)
     -> 병리 외래(3~6일 후): IHC(imem: ER/PR/HER2/Ki-67 각 1행), HER2 2+ 면 FISH(mlem), 진단/과거력/신체계측/가족력/산과력 행,
        기본 혈액검사(cexm), ECOG
     -> 병기 검사(II기 이상: CT/PET, imex + stag, M1 이면 mtst), 일부 생식세포 BRCA 검사(gmvx), HR+ 수술 후 Oncotype(gnrx)
  2) 아형/병기별 치료
     - DCIS          : 유방보존술/전절제 -> 외과병리(pTis) -> BCS 면 전유방 방사선 -> ER+ 면 tamoxifen 5년
     - HR+/HER2-     : 선행 수술(국소진행은 AC->paclitaxel 선행항암) -> Oncotype 고위험/N+ 면 TC 보조항암 -> RT -> 내분비치료(폐경 전 tamoxifen, 폐경 후 AI)
     - HER2+         : TCH 선행항암 6주기 -> 수술(ypTNM, pCR 약 55%) -> trastuzumab 보조 -> RT -> HR+ 면 내분비치료
                       (T1a/b N0 는 수술 -> paclitaxel+trastuzumab 주간 12회 -> trastuzumab)
     - TNBC          : AC 4주기 -> 주간 paclitaxel+carboplatin 12회 선행항암 -> 수술 -> 잔존 시 capecitabine -> RT
     - IV기(약 10%)  : 아형별 고식적 1차 -> 진행(days_to_progression) -> 2·3차, 일부 사망
  3) 항암 주기마다 CBC/신장/간기능, CTCAE 이상사례(3등급 이상은 응급실 방문, 호중구감소는 filgrastim)
  4) 추적 외래 6개월 간격(유방촬영 imex), 일부 재발(rlps + mtst) -> 구제/고식적 치료, 일부 사망
  5) 폐경 전 항암 환자는 치료 후 산과력 행(월경 재개/임신 시도) 추가
특화 테이블(BREAST_CANCER)은 이벤트 그룹 단위로 행을 만든다.
"""
from framework import *

BC_INV, BC_DCIS = 4112853, 4162253
HIST = {"IDC": ("8500/3", "Invasive ductal carcinoma, NOS"), "ILC": ("8520/3", "Invasive lobular carcinoma"),
        "MUC": ("8480/3", "Mucinous carcinoma"), "DCIS": ("8500/2", "Ductal carcinoma in situ")}
LOC = [("C50.4", "유방의 상외사분면 악성 신생물", "UOQ", "Upper outer quadrant"),
       ("C50.2", "유방의 상내사분면 악성 신생물", "UIQ", "Upper inner quadrant"),
       ("C50.5", "유방의 하외사분면 악성 신생물", "LOQ", "Lower outer quadrant"),
       ("C50.3", "유방의 하내사분면 악성 신생물", "LIQ", "Lower inner quadrant"),
       ("C50.1", "유방의 중앙부 악성 신생물", "CEN", "Central portion")]
LOC_P = [0.5, 0.15, 0.13, 0.1, 0.12]
TSIZE = {"Tis": (0.5, 4.0), "T0": (0.0, 0.0), "T1a": (0.2, 0.5), "T1b": (0.6, 1.0), "T1c": (1.1, 2.0),
         "T2": (2.1, 5.0), "T3": (5.1, 8.0), "T4b": (3.0, 9.0)}
STAGE_TNM = {"I": ([("T1a", "N0"), ("T1b", "N0"), ("T1c", "N0")], [0.1, 0.25, 0.65]),
             "II": ([("T2", "N0"), ("T1c", "N1"), ("T2", "N1"), ("T3", "N0")], [0.5, 0.2, 0.22, 0.08]),
             "III": ([("T3", "N1"), ("T2", "N2"), ("T4b", "N1"), ("T1c", "N3"), ("T3", "N2")], [0.3, 0.25, 0.2, 0.1, 0.15]),
             "IV": ([("T2", "N1"), ("T3", "N2"), ("T4b", "N2"), ("T2", "N0")], [0.35, 0.3, 0.2, 0.15])}
SUBTYPES = ["HR+/HER2-", "HR+/HER2+", "HR-/HER2+", "TNBC"]
DENSITY = {"A": "Almost entirely fatty", "B": "Scattered areas of fibroglandular density",
           "C": "Heterogeneously dense", "D": "Extremely dense"}
BIRADS = {"1": "BI-RADS 1 Negative", "2": "BI-RADS 2 Benign", "4A": "BI-RADS 4A Low suspicion for malignancy",
          "4B": "BI-RADS 4B Moderate suspicion for malignancy", "4C": "BI-RADS 4C High suspicion for malignancy",
          "5": "BI-RADS 5 Highly suggestive of malignancy"}
GRADE = {"G1": "Grade 1 (well differentiated)", "G2": "Grade 2 (moderately differentiated)", "G3": "Grade 3 (poorly differentiated)"}
LAT = {"R": "우측", "L": "좌측"}
MET_SITES = [("C41", "Bone"), ("C22", "Liver"), ("C34", "Lung"), ("C71", "Brain"), ("C77", "Distant lymph node")]
MET_P = [0.4, 0.2, 0.2, 0.08, 0.12]
REC_SITES = [("C50", "Ipsilateral breast / chest wall", False), ("C77.3", "Regional axillary lymph node", False)] + \
            [(c, n, True) for c, n in MET_SITES]
REC_P = [0.2, 0.1, 0.28, 0.14, 0.14, 0.06, 0.08]
FAMILY = [("MO", "어머니"), ("SI", "자매"), ("DA", "딸"), ("MGM", "외조모"), ("PGM", "친조모"), ("AU", "이모/고모")]
# 약제 정보: 분류코드, 분류명, 주성분코드, 주성분명, RxNorm 대표코드, 경로
DRUG_INFO = {
    1338512: ("CYTO", "세포독성항암제", "DOXORUBICIN", "doxorubicin hydrochloride", "3639", "IV"),
    1310317: ("CYTO", "세포독성항암제", "CYCLOPHOSPHAMIDE", "cyclophosphamide", "3002", "IV"),
    1378382: ("CYTO", "세포독성항암제", "PACLITAXEL", "paclitaxel", "56946", "IV"),
    1315942: ("CYTO", "세포독성항암제", "DOCETAXEL", "docetaxel", "72962", "IV"),
    1344905: ("CYTO", "세포독성항암제", "CARBOPLATIN", "carboplatin", "38936", "IV"),
    1337620: ("CYTO", "세포독성항암제", "CAPECITABINE", "capecitabine", "194000", "PO"),
    1387104: ("TARGET", "표적치료제", "TRASTUZUMAB", "trastuzumab", "224905", "IV"),
    1436678: ("HORM", "호르몬치료제", "TAMOXIFEN", "tamoxifen citrate", "10324", "PO"),
    1348265: ("HORM", "호르몬치료제", "LETROZOLE", "letrozole", "6440", "PO"),
    1319247: ("HORM", "호르몬치료제", "ANASTROZOLE", "anastrozole", "84857", "PO"),
}
ROUTE_NM = {"IV": "정맥주사", "PO": "경구"}
AE_CHEMO = ([27674, 432791, 301794, 4304213, 439777, 4166735, 4223659, 4265412, 196523, 4141062],
            [0.18, 0.08, 0.2, 0.06, 0.12, 0.12, 0.12, 0.04, 0.05, 0.03])
AE_CAPE = ([196523, 4265412, 140214, 4223659, 27674], [0.3, 0.2, 0.25, 0.15, 0.1])
AE_HORM = ([4223659, 140214, 27674], [0.6, 0.2, 0.2])

MMG_REPORT = ("Bilateral digital mammography with tomosynthesis. Breast composition: {dens} (ACR category {dcd}). "
              "{lat} breast: {size} cm irregular {shape} at the {loc}{calc}. Axilla: {ax}. Contralateral breast: no suspicious finding. "
              "Impression: {birads}. Recommend ultrasound-guided core needle biopsy.")
BX_REPORT = ("Breast, {lat}, {loc}, ultrasound-guided core needle biopsy: {hist}. Nottingham histologic grade {grade}. "
             "Immunohistochemistry: ER {er}% ({erp}), PR {pr}% ({prp}), HER2 IHC {her2}{fish}, Ki-67 labeling index {ki}%. "
             "Molecular subtype: {sub}.")
CT_REPORT = ("CT chest, abdomen and pelvis with contrast. {lat} breast mass {size} cm. {node}. {met} "
             "Impression: breast cancer, c{t}{n}{m}.")
PET_REPORT = "Whole body FDG PET-CT. Hypermetabolic {lat} breast mass (SUVmax {suv}). {node}. {met}"
SP_REPORT = ("Breast, {lat}, {op}{slnb}: {hist}. Tumor size {size} cm ({cnt} focus/foci). Nottingham grade {grade}. "
             "Lymphovascular invasion: {lvi}. Associated DCIS: {dcis}. Resection margins: {margin}. "
             "Sentinel lymph nodes: {psln}/{tsln} positive{aln}. Pathologic stage {t}{n}{m}.{resp}")
GERM_REPORT = ("Germline variant analysis (NGS multigene panel, peripheral blood): BRCA1 {b1}; BRCA2 {b2}. "
               "{summary} Reference sequences NM_007294.4 (BRCA1), NM_000059.4 (BRCA2).")
ODX_REPORT = "Oncotype DX Breast Recurrence Score assay (surgical specimen): Recurrence Score {rs} ({risk} risk). ER score {er}, PR score {pr}, HER2 score {her2}."


def yn(b):
    return ("Y", "예") if b else ("N", "아니오")


# ------------------------------------------------------------------ helpers
def _plan(ctx, age, gender):
    """환자 수준 임상 특성(조직형/병기/아형/IHC/폐경/동반질환)을 미리 결정한다."""
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
        T, N = ctx.choice(opts, p=pr)
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
        st["grade"] = ctx.choice(["G1", "G2", "G3"], p=[0.3, 0.45, 0.25])
    elif sub == "TNBC" or st["her2"]:
        st["grade"] = ctx.choice(["G2", "G3"], p=[0.3, 0.7])
    else:
        st["grade"] = ctx.choice(["G1", "G2", "G3"], p=[0.25, 0.55, 0.2])
    if gender == MALE:
        st["meno"] = None
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
    st["fam"] = ctx.bern(0.2)
    return st


def _imex_mmg(ctx, p, vid, day, density, birads, micf, boms=False):
    mc, mn = ("Y", "있음") if micf else ("N", "없음")
    bc, bn = ("Y", "있음") if boms else ("N", "없음")
    ctx.disease_row(p, vid, imex_ymd=day, imex_kncd="MMG-BIL", imex_knnm="Bilateral digital mammography", imex_smct_cd="71651007",
                    imex_smct_nm="Mammography", brst_dens_clcd=density, brst_dens_clnm=DENSITY[density],
                    imex_rslt_diag_clcd=birads, imex_rslt_diag_clnm=BIRADS[birads],
                    micf_yn_unid_spcd=mc, micf_yn_unid_spnm=mn, boms_yn_unid_spcd=bc, boms_yn_unid_spnm=bn)


def _imex_ct(ctx, p, vid, day, boms):
    bc, bn = ("Y", "있음") if boms else ("N", "없음")
    ctx.disease_row(p, vid, imex_ymd=day, imex_kncd="CT-CAP-C", imex_knnm="Chest and abdomen-pelvis CT with contrast",
                    imex_smct_cd="169069000_169070004", imex_smct_nm="CT of chest_CT of abdomen", boms_yn_unid_spcd=bc, boms_yn_unid_spnm=bn)


def _imex_pet(ctx, p, vid, day, boms):
    bc, bn = ("Y", "있음") if boms else ("N", "없음")
    ctx.disease_row(p, vid, imex_ymd=day, imex_kncd="PET-WB", imex_knnm="Whole body FDG PET-CT", imex_smct_cd="443271005",
                    imex_smct_nm="PET-CT", boms_yn_unid_spcd=bc, boms_yn_unid_spnm=bn)


def _drug_rows(ctx, p, cycle_dates, drugs, cd):
    """특화 테이블 drug 그룹: 처방일 = DRUG_EXPOSURE 시작일 (SEM-COM-028)."""
    for d in cycle_dates:
        vid = ctx.visit_on(p, d)
        for c in drugs:
            dc = CONCEPTS["drugs"][c]
            clcd, clnm, ing_cd, ing_nm, rx, route = DRUG_INFO[c]
            days = (14 if dc["name"] == "capecitabine" else cd) if route == "PO" else 1
            ctx.disease_row(p, vid, drug_prsc_ymd=d, drug_clcd=clcd, drug_clnm=clnm, drin_cd=ing_cd, drin_nm=ing_nm,
                            drug_rxnm_cd=rx, drug_rxnm_nm=dc["name"], amount_value=dc["dose"], amount_unit_concept_id=dc["unit"],
                            drug_prsc_capa=dc["dose"], drug_prsc_capa_unit_cd=dc["dose_unit_label"], drug_prsc_capa_unit_nm=dc["dose_unit_label"],
                            drug_prsc_dcnt=days, drug_injc_pth_cd=route, drug_injc_pth_nm=ROUTE_NM[route])


def _antp(ctx, p, lines, regimen, drugs, start, cycles, intent, category, ecog, response, cycle_days=None, oral=False, limit=None):
    """항암요법 래퍼: 오늘/제한일을 넘지 않도록 주기 수를 줄이고, line 번호를 시작 순서대로 부여한다. 1주기도 못 넣으면 None."""
    cd = cycle_days or max(CONCEPTS["drugs"][c]["cycle_days"] or 21 for c in drugs)
    lim = ctx.today if limit is None else min(limit, ctx.today)
    if p.death_date is not None:
        lim = min(lim, p.death_date)
    if start > lim:
        return None
    maxc = ((lim - start).days + 1) // cd
    if maxc < 1:
        return None
    cycles = max(1, min(cycles, maxc))
    aid, e, cyc = ctx.antp(p, len(lines) + 1, regimen, drugs, start, cycles, intent, category, ecog=ecog, response=response,
                           cycle_days=cd, oral=oral)
    lines.append(aid)
    _drug_rows(ctx, p, cyc, drugs, cd)
    return aid, e, cyc


def _monitor(ctx, p, cycle_dates, aid, ae_set, ae_p=0.45, labs=True):
    """사이클마다 CBC/신장/간기능, 일부 사이클에 이상사례 (같은 날 중복 AE 는 피한다)."""
    concepts, weights = ae_set
    used = p.__dict__.setdefault("_ae_dates", set())
    for i, d in enumerate(cycle_dates):
        vid = ctx.visit_on(p, d)
        if labs:
            shifts = {3017732: -1.5 if i > 0 else 0, 3000963: -1.0 if i > 0 else 0}
            ctx.labs(p, d, [3000963, 3010813, 3017732, 3024929, 3016723, 3013721, 3006923], vid=vid, shifts=shifts)
        if i > 0 and ctx.bern(ae_p):
            ae_day = ctx.days(d, ctx.randint(3, 12))
            if (p.death_date is not None and ae_day > p.death_date) or ae_day > ctx.today or ae_day in used:
                continue
            used.add(ae_day)
            concept = ctx.choice(concepts, p=weights)
            lo, hi = CONCEPTS["adverse_events"][concept]["typical_grade"]
            grade = ctx.randint(lo, hi)
            avid = ctx.visit(p, ae_day, ER if grade >= 3 else OUTPATIENT)
            ctx.ae(p, ae_day, concept, grade, antp_id=aid, vid=avid, action=2 if grade >= 3 else 1)
            ctx.condition(p, ae_day, concept, vid=avid)
            if concept in (301794, 4304213):
                ctx.drug(p, ae_day, 1301125, 3, vid=avid, freq=1)


def _surgery(ctx, p, st, day, nact, salvage=False):
    """수술 입원 + oprt 행. 반환 (svid, bcs, los)."""
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
    lat = st["lat"]
    if bcs:
        kncd, knnm, mtcd, mtnm = "BCS01", "유방보존술(부분 유방절제술)", "BCS", "Breast-conserving surgery"
        recon = (None, None)
    else:
        kncd, knnm = "MST01", "유방전절제술"
        mtcd, mtnm = ctx.choice([("TM", "Total mastectomy"), ("SSM", "Skin-sparing mastectomy"), ("NSM", "Nipple-sparing mastectomy")], p=[0.55, 0.25, 0.2])
        recon = ctx.choice([("NONE", "재건 없음"), ("IMPL", "보형물 삽입 재건"), ("AUTO", "자가조직 피판 재건")],
                           p=[0.85, 0.1, 0.05] if p.age_on(day) > 60 else [0.5, 0.35, 0.15])
    if salvage:
        kncd, knnm, prps = "MST02", "구제 유방전절제술", ("SAL", "구제적")
    else:
        prps = ("CUR", "근치적")
    if nact:
        asmt = ("MP", "Miller-Payne pathologic response grade")
    else:
        asmt = ("MRG", "Resection margin status")
    loc_cd, loc_nm = st["loc"][2], st["loc"][3]
    ctx.disease_row(p, svid, oprt_ymd=day, oprt_kncd=kncd, oprt_knnm=knnm, oprt_prps_cd=prps[0], oprt_prps_nm=prps[1],
                    oprt_site_cd=lat, oprt_site_nm=LAT[lat] + " 유방", oprt_mtcd=mtcd, oprt_mtnm=mtnm,
                    oprt_tumr_loca_cd=loc_cd, oprt_tumr_loca_nm=loc_nm, repr_clcd=recon[0], repr_clnm=recon[1],
                    afop_asmt_item_cd=asmt[0], afop_asmt_item_nm=asmt[1], dsch_ymd=ctx.days(day, los))
    ctx.labs(p, ctx.days(day, 1), [3000963, 3010813, 3016723], vid=svid)
    if ctx.bern(0.15):
        ctx.ae(p, ctx.days(day, 2), 437663, 1, vid=svid)
    return svid, bcs, los


def _surg_path(ctx, p, st, op_day, nact, bcs, salvage=False):
    """외과병리(sgpt) 행 + 병리 노트. 반환 (path_day, pN, pcr)."""
    T, N = st["T"], st["N"]
    path_day = ctx.days(op_day, ctx.randint(4, 9))
    pvid = ctx.visit_on(p, path_day)
    pcr = False
    if salvage:
        pT, pN, psize, cnt = "T2", "NX", round(ctx.rand(1.0, 4.0), 1), 1
    elif nact:
        pcr = ctx.bern({"HR+/HER2+": 0.5, "HR-/HER2+": 0.6, "TNBC": 0.45}.get(st["sub"], 0.12))
        if pcr:
            pT, pN, psize, cnt = "yT0", "yN0", 0.0, 0
        else:
            t = ctx.choice(["T1a", "T1b", "T1c", "T2"], p=[0.15, 0.25, 0.35, 0.25])
            pT, psize, cnt = "y" + t, round(ctx.rand(*TSIZE[t]), 1), 1
            pN = "y" + ("N0" if (N == "N0" or ctx.bern(0.5)) else ctx.choice(["N1", "N2"], p=[0.7, 0.3]))
    else:
        t = T if ctx.bern(0.8) else ctx.choice(["T1b", "T1c", "T2"])
        pT, psize = t, round(ctx.rand(*TSIZE[t]), 1)
        cnt = 2 if ctx.bern(0.1) else 1
        if st["hist"] == "DCIS":
            pN = "N0" if st["slnb"] else "NX"
        else:
            pN = N if ctx.bern(0.75) else ctx.choice(["N0", "N1", "N2"], p=[0.5, 0.35, 0.15])
    nn = pN.lstrip("y")
    if st["slnb"]:
        slnd_totl = ctx.randint(1, 5)
        pstv_slnd = 0 if nn == "N0" else ctx.randint(1, min(3, slnd_totl))
        if nn == "N0":
            totl_ln, pstv_ln = slnd_totl, 0
        else:
            totl_ln = ctx.randint(10, 25)
            pstv_ln = {"N1": ctx.randint(1, 3), "N2": ctx.randint(4, 9), "N3": ctx.randint(10, 15)}[nn]
            pstv_ln = max(pstv_slnd, min(pstv_ln, totl_ln))
    else:
        slnd_totl = pstv_slnd = totl_ln = pstv_ln = None
    grade = st["grade"] if not pcr else None
    lvi = (not pcr) and ctx.bern(0.3 if nn != "N0" else 0.12)
    micf = (not pcr) and ctx.bern(0.3)
    dcis_comp = (not pcr) and st["hist"] != "DCIS" and ctx.bern(0.5)
    margin = ctx.choice([("NEG", "Negative margin (>= 2 mm)"), ("CLS", "Close margin (< 2 mm)")], p=[0.85, 0.15])
    resi = ("R0", "No residual tumor")            # 근접 절제면도 육안/현미경 잔존 없음(R0)
    hist = ("8500/3", "No residual invasive carcinoma (pathologic complete response)") if pcr else HIST[st["hist"]]
    ctx.disease_row(p, pvid, srgc_ptem_ymd=path_day, sgpt_exam_site_latr_cd=st["lat"], sgpt_exam_site_latr_nm=LAT[st["lat"]],
                    sgpt_hvst_site_cd="BREAST", sgpt_hvst_site_nm="유방", htlg_diag_cd_po=hist[0], htlg_diag_nm_po=hist[1],
                    htlg_grcd=grade, htlg_grnm=GRADE[grade] if grade else None,
                    lvin_ex_yn_spcd=yn(lvi)[0], lvin_ex_yn_spnm="있음" if lvi else "없음",
                    sgpt_micf_ex_yn_spcd=yn(micf)[0], sgpt_micf_ex_yn_spnm="있음" if micf else "없음",
                    incn_asso_ex_yn_spcd=yn(dcis_comp)[0], incn_asso_ex_yn_spnm="있음" if dcis_comp else "없음",
                    srmg_rlct_cd=margin[0], srmg_rlct_nm=margin[1], resi_tumr_cd=resi[0], resi_tumr_nm=resi[1],
                    slnd_totl_cnt=slnd_totl, pstv_slnd_cnt=pstv_slnd, totl_ln_cnt=totl_ln, pstv_ln_cnt=pstv_ln,
                    srgc_ptem_rslt_tumr_cnt=cnt, tumr_max_diam_vl=psize,
                    afop_path_tnm_stag_vl=f"{pT}{pN}M0", afop_path_t_stag_vl=pT, afop_path_n_stag_vl=pN, afop_path_m_stag_vl="M0")
    resp = ""
    if nact:
        resp = " Miller-Payne grade 5 (no residual invasive tumor)." if pcr else f" Miller-Payne grade {ctx.randint(2, 4)} (partial response)."
    ctx.note(p, path_day, SP_REPORT.format(
        lat="right" if st["lat"] == "R" else "left", op="partial mastectomy" if bcs else "total mastectomy",
        slnb=" with sentinel lymph node biopsy" if st["slnb"] else "", hist=hist[1], size=psize, cnt=cnt,
        grade=grade[1] if grade else "not applicable", lvi="present" if lvi else "absent", dcis="present" if dcis_comp else "absent",
        margin=margin[1].lower(), psln=pstv_slnd if pstv_slnd is not None else "-", tsln=slnd_totl if slnd_totl is not None else "-",
        aln=f"; axillary dissection {pstv_ln}/{totl_ln} positive" if (totl_ln and nn != "N0") else "",
        t=pT, n=pN, m="M0", resp=resp), note_type=44814640, note_class=36716165, vid=pvid)
    return path_day, pN, pcr


def _rt(ctx, p, day, kind):
    """방사선치료 처방 행 + 처치. 반환 종료 추정일."""
    rvid = ctx.visit_on(p, day)
    ctx.procedure(p, day, 4181206, vid=rvid)
    if kind == "WBI":
        if ctx.bern(0.6):
            gy, fx, tot = 2.67, 16, 42.7
        else:
            gy, fx, tot = 2.0, 25, 50.0
        kncd, knnm, site = "RT-WBI", "Whole breast irradiation (IMRT)", ("BREAST", "유방")
    else:
        gy, fx, tot = 2.0, 25, 50.0
        kncd, knnm, site = "RT-PMRT", "Post-mastectomy chest wall and regional nodal irradiation", ("CWRN", "흉벽 및 영역 림프절")
    ctx.disease_row(p, rvid, rdt_prsc_ymd=day, rdt_kncd=kncd, rdt_knnm=knnm, rdt_prps_cd="ADJ", rdt_prps_nm="보조적",
                    rdt_site_cd=site[0], rdt_site_nm=site[1], rd_gy=gy, rd_impl_nt=fx, rd_totl_gy=tot)
    return ctx.days(day, int(fx * 1.4) + 3)


def _endocrine(ctx, p, st, start, lines, ecog, limit=None):
    """보조 내분비치료 5년(84일 처방 단위). 반환 (aid, end) 또는 None."""
    if st["meno"] == 2 and ctx.bern(0.9):
        drug, name = (1348265, "Letrozole") if ctx.bern(0.6) else (1319247, "Anastrozole")
    else:
        drug, name = 1436678, "Tamoxifen"
    cycles = ctx.randint(2, 12) if ctx.bern(0.1) else 22
    r = _antp(ctx, p, lines, name, [drug], start, cycles, 2, 3, ecog, "NE", cycle_days=84, oral=True, limit=limit)
    if r is None:
        return None
    aid, e, cyc = r
    ctx.antp_update(aid, treatment_outcome=1 if e >= ctx.days(ctx.today, -60) else 0)
    return aid, e


def _palliative(ctx, p, st, start, lines, ecog, first_intent=3):
    """전이/재발 후 전신치료 순차 라인. 반환 (last_end, last_aid)."""
    today = ctx.today
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
    last_end, last_aid, cur, cur_ecog = start, None, start, ecog
    for i, (name, drugs, cd, cycles, cat, intent, aes, ae_p, oral) in enumerate(plan):
        r = _antp(ctx, p, lines, name, drugs, cur, cycles, intent, cat, cur_ecog, "NE", cycle_days=cd, oral=oral)
        if r is None:
            break
        aid, e, cyc = r
        last_end, last_aid = e, aid
        _monitor(ctx, p, cyc, aid, aes, ae_p=ae_p)
        if i + 1 < len(plan) and plan[i + 1][5] == 4:          # 유지요법으로 이어짐
            ctx.antp_update(aid, treatment_outcome=0, best_overall_response_source_value=ctx.choice(["PR", "SD", "CR"], p=[0.6, 0.3, 0.1]))
            cur = ctx.days(e, 21)
            continue
        progressed = ctx.bern(0.65) and ctx.days(e, 60) <= today
        if progressed:
            pd_day = ctx.days(e, ctx.randint(0, 45))
            site_cd, site_nm = ctx.choice(MET_SITES, p=MET_P)
            pvid = ctx.visit_on(p, pd_day)
            ctx.procedure(p, pd_day, 4207701, vid=pvid)
            _imex_ct(ctx, p, pvid, pd_day, boms=True)
            ctx.note(p, pd_day, f"CT chest/abdomen/pelvis: interval increase of known lesions and new {site_nm.lower()} metastases. "
                                "Progressive disease by RECIST 1.1.", vid=pvid)
            ctx.antp_update(aid, treatment_outcome=0, days_to_progression=pd_day, progression_or_recurrence_anatomic_site=site_nm,
                            best_overall_response_source_value=ctx.choice(["PR", "SD", "PD"], p=[0.35, 0.4, 0.25]))
            ctx.disease_row(p, pvid, mtdg_ymd=pd_day, mtst_site_cd=site_cd, mtst_site_nm=site_nm)
            last_end = pd_day
            cur_ecog = min(cur_ecog + 1, 3)
            if cur_ecog <= 2 and ctx.bern(0.75) and i + 1 < len(plan):
                cur = ctx.days(pd_day, ctx.randint(7, 21))
                continue
            break
        ctx.antp_update(aid, treatment_outcome=1 if e >= ctx.days(today, -60) else 0,
                        best_overall_response_source_value=ctx.choice(["PR", "SD", "CR"], p=[0.55, 0.35, 0.1]))
        break
    return last_end, last_aid


def _die(ctx, p, last_end):
    dd = ctx.days(last_end, ctx.randint(30, 300))
    if dd > ctx.today:
        return False
    ctx.set_death(p, dd)
    ctx.visit(p, ctx.days(dd, -2), INPATIENT, los=2)
    ctx.disease_row(p, ctx.visit_on(p, dd), death_date=dd)
    for r in ctx.rows["BREAST_CANCER"]:
        if r["person_id"] == p.person_id:
            r["death_date"] = dd
    p.patient_fields["death_date"] = dd
    return True


def _obstetric_baseline(ctx, p, st, age, vid, day, plan_chemo):
    """진단 시 산과력/생식력 행 (여성만)."""
    meno = st["meno"]
    mena = ctx.randint(11, 16)
    f = dict(obtr_rcrd_ymd=day, menopause_status=meno, mena_age_vl=mena)
    if meno == 2:
        f["meno_yn_noans_spcd"], f["meno_yn_noans_spnm"] = "Y", "예"
        f["meno_age_vl"] = ctx.randint(44, min(56, age))
        hrt = ctx.bern(0.15)
        f["hrpr_yn_noans_spcd"], f["hrpr_yn_noans_spnm"] = yn(hrt)
        if hrt:
            f["hrt_impl_mcnt"] = ctx.randint(6, 120)
    elif meno == 1:
        f["meno_yn_noans_spcd"], f["meno_yn_noans_spnm"] = "N", "아니오"
        f["hrpr_yn_noans_spcd"], f["hrpr_yn_noans_spnm"] = "N", "아니오"
    live = age >= 23 and ctx.bern(0.78)
    f["history_of_live_birth"] = 1 if live else 2
    if live:
        f["delv_chld_cnt"] = ctx.choice([1, 2, 3, 4], p=[0.3, 0.5, 0.15, 0.05])
        f["delv_age_vl"] = ctx.randint(max(mena + 4, 20), min(38, age - 1))
        bf = ctx.bern(0.7)
        f["bfpr_yn_noans_spcd"], f["bfpr_yn_noans_spnm"] = yn(bf)
        f["postpartum_at_diagnosis"] = 1 if (age <= 42 and meno == 1 and ctx.bern(0.05)) else 2
    else:
        f["delv_chld_cnt"] = 0
        f["bfpr_yn_noans_spcd"], f["bfpr_yn_noans_spnm"] = "N", "아니오"
        f["postpartum_at_diagnosis"] = 2
    f["pregnant_at_diagnosis"] = 1 if (meno == 1 and 18 <= age <= 45 and ctx.bern(0.03)) else 2
    married = ctx.bern(0.72)
    f["marital_status"] = 1 if married else 2
    f["marg_yn_noans_spcd"], f["marg_yn_noans_spnm"] = yn(married)
    f["marg_detl_cd"], f["marg_detl_nm"] = ("MAR", "기혼") if married else ctx.choice([("SGL", "미혼"), ("DIV", "이혼"), ("WID", "사별")], p=[0.7, 0.2, 0.1])
    fert = meno == 1 and age <= 40 and plan_chemo and ctx.bern(0.55)
    f["fertility_history"] = 1 if fert else 2
    if fert:
        t = ctx.choice([1, 2, 3, 4, 5], p=[0.45, 0.2, 0.1, 0.1, 0.15])
        f["fertility_treatment_type"] = t
        if t == 4:
            f["fertility_treatment_type_other"] = "Ovarian tissue cryopreservation"
    ctx.disease_row(p, vid, **f)


def _obstetric_followup(ctx, p, st, age):
    """폐경 전 항암 환자의 치료 후 월경/임신 행 (여정 마지막에 생성)."""
    chemo_end = st.get("chemo_end")
    if p.death_date is not None or p.gender != FEMALE or st["meno"] != 1 or chemo_end is None:
        return
    R = ctx.days(chemo_end, ctx.randint(365, 600))
    if R > ctx.today:
        return
    max_end = max(r["antp_end_date"] for r in ctx.rows["ANTP_THERAPY"] if r["person_id"] == p.person_id)
    resumed = ctx.bern(0.85 if age < 40 else (0.6 if age < 45 else 0.2))
    f = dict(obtr_rcrd_ymd=R, menstruation_resumed_after_treatment=1 if resumed else 2, menstrual_regularity_after_treatment=3)
    attempt = False
    if resumed:
        fmp = ctx.days(chemo_end, ctx.randint(90, 330))
        f["menstrual_regularity_after_treatment"] = 1 if ctx.bern(0.6) else 2
        if fmp > max_end:      # SEM-BC-005: 모든 항암(내분비 포함) 종료일 이후일 때만 기재
            f["first_menstrual_period_date_after_treatment"] = fmp
        attempt = age <= 45 and ctx.bern(0.7)
    f["pregnancy_attempt"] = 1 if attempt else 2
    if attempt:
        f["pregnancy_attempt_start_date"] = min(ctx.days(fmp, ctx.randint(30, 200)), ctx.days(R, -60))
        success = ctx.bern(0.5)
        f["pregnancy_success"] = 1 if success else 2
        if success:
            f["method_of_conception"] = ctx.choice([1, 2, 3, 4, 5], p=[0.6, 0.1, 0.1, 0.15, 0.05])
            outcome = ctx.choice([1, 2, 3, 4], p=[0.1, 0.2, 0.15, 0.55])
            f["pregnancy_outcome"] = outcome
            f["delivery"] = 1 if outcome == 4 else 2
    ctx.disease_row(p, ctx.visit_on(p, R), **f)


# ----------------------------------------------------------------- journey
def generate(ctx: Ctx, n=100):
    for i in range(n):
        gender = MALE if i % 100 == 50 else FEMALE          # 약 1% 남성
        age = int(ctx.normal(66 if gender == MALE else 52, 11, 26, 88, 0))
        index = D(2019, 1, 1) + dt.timedelta(days=ctx.randint(0, 2190))
        p = ctx.person(gender, age, index)
        st = _plan(ctx, age, gender)
        dcis = st["hist"] == "DCIS"
        T, N, M, sub, lat = st["T"], st["N"], st["M"], st["sub"], st["lat"]
        kcd, kcd_nm, loc_cd, loc_nm = st["loc"]
        if dcis:
            kcd, kcd_nm = "D05.1", "유방의 관내 상피내암종"
        p.patient_fields = dict(brcn_diag_kncd=kcd, brcn_diag_knnm=kcd_nm, care_site_id=1)
        lines, ecog = [], st["ecog"]
        lat_en = "Right" if lat == "R" else "Left"
        size = st["size"]

        # 치료 계획 플래그 (산과력 행의 가임력 보존 결정에 필요하므로 미리 결정)
        big = T not in ("Tis", "T1a", "T1b") or N != "N0"
        if M == "M1":
            plan_nact, plan_adj_chemo = False, False
        elif dcis:
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
        density = ctx.choice(["A", "B", "C", "D"], p=[0.05, 0.2, 0.5, 0.25])
        st["density"] = density
        birads = ctx.choice(["4B", "4C", "5"], p=[0.3, 0.4, 0.3]) if dcis else ctx.choice(["4A", "4B", "4C", "5"], p=[0.08, 0.17, 0.3, 0.45])
        micf = dcis or ctx.bern(0.35)
        _imex_mmg(ctx, p, dx_vid, index, density, birads, micf)
        ctx.note(p, index, MMG_REPORT.format(
            dens=DENSITY[density].lower(), dcd=density, lat=lat_en, size=size,
            shape="segmental pleomorphic microcalcifications without discrete mass" if dcis else ("spiculated mass" if ctx.bern(0.7) else "irregular hypoechoic mass"),
            loc=loc_nm.lower(), calc=" with associated pleomorphic microcalcifications" if (micf and not dcis) else "",
            ax="suspicious enlarged lymph node" if N != "N0" else "no abnormal lymph node", birads=BIRADS[birads]), vid=dx_vid)
        ctx.disease_row(p, dx_vid, bpsy_ymd=index, bpsy_site_cd="BREAST", bpsy_site_nm="유방", bpsy_site_latr_cd=lat, bpsy_site_latr_nm=LAT[lat],
                        bpsy_mthd_kncd="CNB", bpsy_mthd_knnm="초음파 유도 중심부 침생검", htlg_diag_cd=HIST[st["hist"]][0], htlg_diag_nm=HIST[st["hist"]][1])

        # ---- 병리/IHC 외래 (3~6일 후)
        path_day = ctx.days(index, ctx.randint(3, 6))
        pv = ctx.visit_on(p, path_day)
        her2_txt = {0: "0", 1: "1+", 2: "2+", 3: "3+"}[st["her2_ihc"]]
        fish_txt = f" (FISH HER2/CEP17 ratio {st['fish']}, {'amplified' if st['her2'] else 'not amplified'})" if st["fish"] else ""
        ctx.note(p, path_day, BX_REPORT.format(lat=lat_en.lower(), loc=loc_nm.lower(), hist=HIST[st["hist"]][1], grade=st["grade"][1],
                                                er=st["er"], erp="positive" if st["hr"] else "negative", pr=st["pr"], prp="positive" if st["pr"] > 0 else "negative",
                                                her2=her2_txt, fish=fish_txt, ki=st["ki67"], sub=sub if not dcis else ("ER-positive DCIS" if st["hr"] else "ER-negative DCIS")),
                 note_type=44814640, note_class=36716165, vid=pv)
        for kncd, knnm, opn, val, unit in (
                ("IHC-ER", "Estrogen receptor IHC", ("POS", "Positive") if st["hr"] else ("NEG", "Negative"), st["er"], ("%", "percent of tumor cells")),
                ("IHC-PR", "Progesterone receptor IHC", ("POS", "Positive") if st["pr"] > 0 else ("NEG", "Negative"), st["pr"], ("%", "percent of tumor cells")),
                ("IHC-HER2", "HER2 IHC (HercepTest)", (her2_txt, f"IHC score {her2_txt}"), st["her2_ihc"], ("SCORE", "IHC score 0-3")),
                ("IHC-KI67", "Ki-67 labeling index", ("HIGH", "High (>= 20%)") if st["ki67"] >= 20 else ("LOW", "Low (< 20%)"), st["ki67"], ("%", "percent of tumor cells"))):
            ctx.disease_row(p, pv, imem_ymd=path_day, imem_kncd=kncd, imem_knnm=knnm, imem_opn_cd=opn[0], imem_opn_nm=opn[1],
                            imem_rslt_vl=val, imem_rslt_unit_cd=unit[0], imem_rslt_unit_nm=unit[1])
        if st["fish"]:
            amp = st["her2"]
            ctx.disease_row(p, pv, mlem_ymd=path_day, mlem_kncd="HER2-ISH", mlem_knnm="HER2 in situ hybridization", mlem_mtcd="FISH",
                            mlem_mtnm="Fluorescence in situ hybridization", mlem_rslt_cd="AMP" if amp else "NAMP",
                            mlem_rslt_nm="Amplified" if amp else "Not amplified", mlem_rslt_kncd="RATIO", mlem_rslt_knnm="HER2/CEP17 ratio", mlem_rslt_vl=st["fish"])
        smct = ("109889007", "Carcinoma in situ of breast") if dcis else ("254837009", "Malignant neoplasm of breast")
        ctx.disease_row(p, pv, diag_rgst_ymd=path_day, diag_smct_cd=smct[0], diag_smct_nm=smct[1])
        # 과거력 / ECOG
        lvds, cncr, tb, etc = ctx.bern(0.05), ctx.bern(0.05), ctx.bern(0.04), ctx.bern(0.15)
        anyhx = st["htn"] or st["dm"] or lvds or cncr or tb or etc
        ctx.observation(p, path_day, 4257895, vid=pv, value_number=ecog, value_string=f"ECOG {ecog}")
        ctx.disease_row(p, pv, rcrd_ymd=path_day, mhis_yn_noans_spcd=yn(anyhx)[0], mhis_yn_noans_spnm=yn(anyhx)[1],
                        mhis_htn_yn_noans_spcd=yn(st["htn"])[0], mhis_htn_yn_noans_spnm=yn(st["htn"])[1],
                        mhis_dbt_yn_noans_spcd=yn(st["dm"])[0], mhis_dbt_yn_noans_spnm=yn(st["dm"])[1],
                        mhis_lvds_yn_noans_spcd=yn(lvds)[0], mhis_lvds_yn_noans_spnm=yn(lvds)[1],
                        mhis_cncr_yn_noans_spcd=yn(cncr)[0], mhis_cncr_yn_noans_spnm=yn(cncr)[1],
                        mhis_cncr_kncd="C73" if cncr else None, mhis_cncr_knnm="갑상선의 악성 신생물" if cncr else None,
                        mhis_tb_yn_noans_spcd=yn(tb)[0], mhis_tb_yn_noans_spnm=yn(tb)[1],
                        etc_mhis_yn_noans_spcd=yn(etc)[0], etc_mhis_yn_noans_spnm=yn(etc)[1], ecog_cd=str(ecog), ecog_nm=f"ECOG {ecog}")
        # 신체계측
        ht = ctx.normal(170 if gender == MALE else 158, 5.5, 140, 190)
        wt = ctx.normal(70 if gender == MALE else 58, 9, 38, 110)
        bmi = round(wt / (ht / 100) ** 2, 1)
        ctx.measure(p, path_day, 3036277, ht, vid=pv); ctx.measure(p, path_day, 3025315, wt, vid=pv); ctx.measure(p, path_day, 3038553, bmi, vid=pv)
        ctx.disease_row(p, pv, anth_rcrd_ymd=path_day, ht_msrm_vl=ht, wt_msrm_vl=wt, bmi_vl=bmi)
        if bmi >= 30: ctx.condition(p, path_day, 433736, vid=pv)
        # 가족력
        if st["fam"]:
            rel = ctx.choice(FAMILY)
            fc = ("C50", "유방의 악성 신생물") if ctx.bern(0.8) else ("C56", "난소의 악성 신생물")
            ctx.disease_row(p, pv, fmht_rcrd_ymd=path_day, fmht_yn_noans_spcd="Y", fmht_yn_noans_spnm="예", pt_fm_rlcd=rel[0], pt_fm_rlnm=rel[1],
                            fmhs_cncr_yn_noans_spcd="Y", fmhs_cncr_yn_noans_spnm="예", fmht_cncr_kncd=fc[0], fmht_cncr_knnm=fc[1])
        else:
            ctx.disease_row(p, pv, fmht_rcrd_ymd=path_day, fmht_yn_noans_spcd="N", fmht_yn_noans_spnm="아니오", fmhs_cncr_yn_noans_spcd="N", fmhs_cncr_yn_noans_spnm="아니오")
        # 산과력 (여성)
        if gender == FEMALE:
            _obstetric_baseline(ctx, p, st, age, pv, path_day, plan_chemo)
        # 기본 혈액검사
        base = ctx.labs(p, path_day, [3000963, 3010813, 3017732, 3024929, 3016723, 3013721, 3006923, 3020491, 3024128, 3028641], vid=pv)
        ctx.disease_row(p, pv, cexm_ymd=path_day, cexm_kncd="L3011", cexm_knnm="CBC", cexm_loinc_cd="58410-2", cexm_loinc_nm="CBC panel - Blood by Automated count",
                        cexm_rslt_cont=f"Hb {base[3000963]} g/dL, WBC {base[3010813]} x10^3/uL, ANC {base[3017732]} x10^3/uL, Plt {base[3024929]} x10^3/uL", cexm_rslt_unit_cont="g/dL; 10^3/uL")
        ctx.disease_row(p, pv, cexm_ymd=path_day, cexm_kncd="L3201", cexm_knnm="Liver function panel", cexm_loinc_cd="24325-3", cexm_loinc_nm="Hepatic function 2000 panel - Serum or Plasma",
                        cexm_rslt_cont=f"AST {base[3013721]} U/L, ALT {base[3006923]} U/L, T.bil {base[3024128]} mg/dL, Albumin {base[3020491]} g/dL", cexm_rslt_unit_cont="U/L; mg/dL; g/dL")
        ctx.disease_row(p, pv, cexm_ymd=path_day, cexm_kncd="L5101", cexm_knnm="CEA", cexm_loinc_cd="2039-6", cexm_loinc_nm="Carcinoembryonic Ag [Mass/volume] in Serum or Plasma",
                        cexm_rslt_cont=f"CEA {base[3028641]} ng/mL", cexm_rslt_unit_cont="ng/mL")

        # ---- 병기 결정
        prty = ("CALC", "Segmental microcalcifications") if dcis else ctx.choice([("SPIC", "Spiculated mass"), ("IRR", "Irregular mass"), ("NME", "Non-mass enhancement")], p=[0.6, 0.3, 0.1])
        if st["stage"] in ("0", "I"):
            stage_day, svid_stage = path_day, pv
        else:
            stage_day = ctx.days(index, ctx.randint(7, 14))
            svid_stage = ctx.visit_on(p, stage_day)
            ctx.procedure(p, stage_day, 4207701, vid=svid_stage)
            ctx.procedure(p, stage_day, 4305790, vid=svid_stage)
            _imex_ct(ctx, p, svid_stage, stage_day, boms=(M == "M1"))
            _imex_pet(ctx, p, svid_stage, stage_day, boms=(M == "M1"))
            met = ctx.choice(MET_SITES, p=MET_P) if M == "M1" else None
            node = "Enlarged axillary lymph nodes" if N != "N0" else "No significant lymphadenopathy"
            met_txt = f"Multiple metastatic lesions in {met[1].lower()}." if met else "No distant metastasis."
            ctx.note(p, stage_day, CT_REPORT.format(lat=lat_en, size=size, node=node, met=met_txt, t=T, n=N, m=M), vid=svid_stage)
            ctx.note(p, stage_day, PET_REPORT.format(lat=lat_en.lower(), suv=round(ctx.rand(3.0, 15.0), 1), node=node, met=met_txt), vid=svid_stage)
            if met:
                ctx.disease_row(p, svid_stage, mtdg_ymd=stage_day, mtst_site_cd=met[0], mtst_site_nm=met[1])
        ctx.disease_row(p, svid_stage, diag_stag_rcrd_ymd=stage_day, clnc_tnm_stag_vl=f"{T}{N}{M}", clnc_t_stag_vl=T, clnc_n_stag_vl=N, clnc_m_stag_vl=M,
                        clnc_tumr_prty_cd=prty[0], clnc_tumr_prty_nm=prty[1])

        # ---- 생식세포 변이 검사 (젊은 환자 / TNBC / 가족력)
        if (age <= 45 or sub == "TNBC" or st["fam"]) and gender == FEMALE and ctx.bern(0.7):
            gm_day = ctx.days(index, ctx.randint(14, 40))
            gvid = ctx.visit_on(p, gm_day)
            pv_gene = ctx.choice(["BRCA1", "BRCA2", None], p=[0.06, 0.05, 0.89])
            vus_gene = None if pv_gene else ctx.choice(["BRCA1", "BRCA2", None], p=[0.05, 0.05, 0.9])
            res = {}
            for gene in ("BRCA1", "BRCA2"):
                f = dict(gmvx_ymd=gm_day, gmvx_mtcd="NGS", gmvx_mtnm="Next generation sequencing multigene panel", gmvx_gene_kncd=gene,
                         gmvx_gene_knnm=f"{gene} gene", ref_seq="NM_007294.4" if gene == "BRCA1" else "NM_000059.4")
                if gene == pv_gene:
                    f.update(pavr_detect_yn_spcd="Y", pavr_detect_yn_spnm="검출", uncl_varnt_detect_yn_spcd="N", uncl_varnt_detect_yn_spnm="미검출",
                             gmte_mtst_exam_rslt_cont="Pathogenic variant detected", dna_vainf_a_vl="c.68_69delAG" if gene == "BRCA1" else "c.5946delT",
                             dna_vainf_b_cd="DEL", dna_vainf_b_nm="Deletion", dna_vainf_c_cd="FS", dna_vainf_c_nm="Frameshift",
                             amsn_vainf_a_cd="Glu" if gene == "BRCA1" else "Ser", amsn_vainf_a_nm="Glutamic acid" if gene == "BRCA1" else "Serine",
                             amsn_vainf_b_vl=23 if gene == "BRCA1" else 1982, amsn_vainf_c_cd="fsTer", amsn_vainf_c_nm="Frameshift with premature termination")
                    res[gene] = f"pathogenic variant {f['dna_vainf_a_vl']} detected"
                elif gene == vus_gene:
                    f.update(pavr_detect_yn_spcd="N", pavr_detect_yn_spnm="미검출", uncl_varnt_detect_yn_spcd="Y", uncl_varnt_detect_yn_spnm="검출",
                             gmte_mtst_exam_rslt_cont="Variant of uncertain significance detected", dna_vainf_a_vl="c.4837A>G", dna_vainf_b_cd="SNV",
                             dna_vainf_b_nm="Single nucleotide variant", dna_vainf_c_cd="MIS", dna_vainf_c_nm="Missense")
                    res[gene] = "variant of uncertain significance c.4837A>G"
                else:
                    f.update(pavr_detect_yn_spcd="N", pavr_detect_yn_spnm="미검출", uncl_varnt_detect_yn_spcd="N", uncl_varnt_detect_yn_spnm="미검출",
                             gmte_mtst_exam_rslt_cont="No pathogenic variant detected")
                    res[gene] = "no pathogenic variant"
                ctx.disease_row(p, gvid, **f)
            summ = "Result consistent with hereditary breast and ovarian cancer syndrome; genetic counseling recommended." if pv_gene else "No clinically actionable germline variant identified."
            ctx.note(p, gm_day, GERM_REPORT.format(b1=res["BRCA1"], b2=res["BRCA2"], summary=summ), note_type=44814640, note_class=36716165, vid=gvid)

        # ---- 2) 치료
        surgery_day = None
        last_adj_end = stage_day          # 내분비치료를 제외한 마지막 국소/전신 치료 종료일
        chemo_end = None
        if M == "M1":
            start = ctx.days(stage_day, ctx.randint(7, 21))
            last_end, last_aid = _palliative(ctx, p, st, start, lines, ecog)
            last_adj_end = last_end
            if last_aid is not None and ctx.bern(0.6) and _die(ctx, p, last_end):
                ctx.antp_update(last_aid, treatment_outcome=0)
            recur_day = None
        else:
            nact = plan_nact
            # 선행항암
            if nact:
                s = ctx.days(index, ctx.randint(14, 28))
                if st["her2"]:
                    r = _antp(ctx, p, lines, "Docetaxel + Carboplatin + Trastuzumab (TCH)", [1315942, 1344905, 1387104], s, 6, 1, 2, ecog,
                              ctx.choice(["PR", "CR", "SD"], p=[0.5, 0.4, 0.1]))
                    if r: _monitor(ctx, p, r[2], r[0], AE_CHEMO); ctx.antp_update(r[0], treatment_outcome=0)
                else:
                    r = _antp(ctx, p, lines, "Doxorubicin + Cyclophosphamide (AC)", [1338512, 1310317], s, 4, 1, 1, ecog, ctx.choice(["PR", "SD"], p=[0.7, 0.3]))
                    if r:
                        _monitor(ctx, p, r[2], r[0], AE_CHEMO); ctx.antp_update(r[0], treatment_outcome=0)
                        drugs2 = [1378382, 1344905] if sub == "TNBC" else [1378382]
                        r2 = _antp(ctx, p, lines, "Weekly Paclitaxel + Carboplatin" if sub == "TNBC" else "Weekly Paclitaxel", drugs2,
                                   ctx.days(r[1], 21), 12, 1, 1, ecog, ctx.choice(["PR", "CR", "SD"], p=[0.5, 0.35, 0.15]), cycle_days=7)
                        if r2: _monitor(ctx, p, r2[2], r2[0], AE_CHEMO); ctx.antp_update(r2[0], treatment_outcome=0); r = r2
                if r is None:
                    nact = False
                    surgery_day = ctx.days(index, ctx.randint(21, 45))
                else:
                    chemo_end = r[1]
                    surgery_day = ctx.days(r[1], ctx.randint(21, 42))
            else:
                surgery_day = ctx.days(index, ctx.randint(21, 45))
            # 수술 + 외과병리
            svid, bcs, los = _surgery(ctx, p, st, surgery_day, nact)
            spath_day, pN, pcr = _surg_path(ctx, p, st, surgery_day, nact, bcs)
            nn = pN.lstrip("y")
            last_adj_end = ctx.days(surgery_day, los)
            # Oncotype (HR+/HER2-, 수술 후)
            if st.get("odx"):
                g_day = ctx.days(spath_day, ctx.randint(7, 21))
                gv = ctx.visit_on(p, g_day)
                rs = st["rs"]
                risk = ("LOW", "Low risk (RS 0-15)") if rs <= 15 else (("INT", "Intermediate risk (RS 16-25)") if rs <= 25 else ("HIGH", "High risk (RS 26-100)"))
                ctx.disease_row(p, gv, gnrx_ymd=g_day, gnrx_kncd="ODX", gnrx_knnm="Oncotype DX Breast Recurrence Score", gnrx_rslt_kncd=risk[0],
                                gnrx_rslt_knnm=risk[1], gnrx_rslt_cont=f"Recurrence Score {rs}")
                ctx.note(p, g_day, ODX_REPORT.format(rs=rs, risk=risk[1].split(" ")[0].lower(), er=round(ctx.rand(8.0, 12.0), 1), pr=round(ctx.rand(5.0, 10.0), 1), her2=round(ctx.rand(8.0, 10.5), 1)),
                         note_type=44814640, note_class=36716165, vid=gv)
                last_adj_end = max(last_adj_end, g_day)
            # 보조항암 (선행 수술군)
            if plan_adj_chemo and not nact:
                s = ctx.days(last_adj_end, ctx.randint(21, 35))
                if st["her2"]:
                    r = _antp(ctx, p, lines, "Weekly Paclitaxel + Trastuzumab (APT)", [1378382, 1387104], s, 12, 2, 2, ecog, "NE", cycle_days=7)
                    if r:
                        _monitor(ctx, p, r[2], r[0], AE_CHEMO); ctx.antp_update(r[0], treatment_outcome=0); chemo_end = r[1]; last_adj_end = r[1]
                        r2 = _antp(ctx, p, lines, "Trastuzumab", [1387104], ctx.days(r[1], 21), 13, 2, 2, ecog, "NE")
                        if r2: _monitor(ctx, p, r2[2], r2[0], AE_HORM, ae_p=0.08, labs=False); ctx.antp_update(r2[0], treatment_outcome=0); last_adj_end = r2[1]
                else:
                    r = _antp(ctx, p, lines, "Docetaxel + Cyclophosphamide (TC)", [1315942, 1310317], s, 4, 2, 1, ecog, "NE")
                    if r: _monitor(ctx, p, r[2], r[0], AE_CHEMO); ctx.antp_update(r[0], treatment_outcome=0); chemo_end = r[1]; last_adj_end = r[1]
            # 선행항암 후 보조치료
            if nact:
                s = ctx.days(surgery_day, ctx.randint(28, 42))
                if st["her2"]:
                    r = _antp(ctx, p, lines, "Trastuzumab", [1387104], s, 11, 2, 2, ecog, "NE")
                    if r: _monitor(ctx, p, r[2], r[0], AE_HORM, ae_p=0.08, labs=False); ctx.antp_update(r[0], treatment_outcome=0); last_adj_end = r[1]
                elif sub == "TNBC" and not pcr:
                    r = _antp(ctx, p, lines, "Capecitabine", [1337620], s, 6, 2, 1, ecog, "NE", oral=True)
                    if r: _monitor(ctx, p, r[2], r[0], AE_CAPE, ae_p=0.4); ctx.antp_update(r[0], treatment_outcome=0); chemo_end = r[1]; last_adj_end = r[1]
            st["chemo_end"] = chemo_end
            # 방사선치료
            pmrt = (not bcs) and (T in ("T3", "T4b") or nn in ("N2", "N3") or (nn == "N1" and ctx.bern(0.5)))
            if bcs or pmrt:
                rt_day = ctx.days(last_adj_end, ctx.randint(21, 42)) if (chemo_end and chemo_end > surgery_day) else ctx.days(surgery_day, ctx.randint(28, 50))
                if rt_day <= ctx.today:
                    rt_end = _rt(ctx, p, rt_day, "WBI" if bcs else "PMRT")
                    last_adj_end = max(last_adj_end, rt_end)
            # 재발 여부 사전 결정 (내분비치료 종료일을 재발 전으로 제한하기 위함)
            p_rec = {"0": 0.03, "I": 0.06, "II": 0.13, "III": 0.28}[st["stage"]] + (0.08 if sub == "TNBC" and not dcis else 0)
            recur_day = ctx.days(last_adj_end, ctx.randint(200, 1500)) if ctx.bern(p_rec) else None
            if recur_day is not None and recur_day > ctx.days(ctx.today, -45):
                recur_day = None
            # 내분비치료
            if st["hr"] and (not dcis or ctx.bern(0.7)):
                s = ctx.days(last_adj_end, ctx.randint(14, 30))
                _endocrine(ctx, p, st, s, lines, ecog, limit=ctx.days(recur_day, -1) if recur_day else None)

        # ---- 3) 추적 및 재발
        fu = ctx.days(last_adj_end, ctx.randint(170, 200))
        recurred = M == "M1"
        k = 0
        while p.death_date is None and fu <= ctx.today and k < 14:
            fvid = ctx.visit_on(p, fu)
            hit = recur_day is not None and not recurred and fu >= recur_day
            site = ctx.choice(REC_SITES, p=REC_P) if hit else None
            if not recurred:
                ctx.procedure(p, fu, 4044530, vid=fvid)
                _imex_mmg(ctx, p, fvid, fu, st["density"], "5" if (hit and not site[2]) else ctx.choice(["1", "2"]), micf=False)
                ctx.labs(p, fu, [3000963, 3028641], vid=fvid)
            else:
                ctx.procedure(p, fu, 4207701, vid=fvid)
                _imex_ct(ctx, p, fvid, fu, boms=True)
                ctx.labs(p, fu, [3000963, 3028641, 3013721], vid=fvid)
            if hit:
                recurred = True
                site_cd, site_nm, distant = site
                ctx.procedure(p, fu, 4207701, vid=fvid)
                ctx.procedure(p, fu, 4305790, vid=fvid)
                _imex_ct(ctx, p, fvid, fu, boms=distant)
                _imex_pet(ctx, p, fvid, fu, boms=distant)
                ctx.note(p, fu, f"PET-CT: new hypermetabolic lesion(s) in {site_nm.lower()}, consistent with {'distant' if distant else 'locoregional'} recurrence of breast cancer.", vid=fvid)
                ctx.disease_row(p, fvid, rldg_ymd=fu, rlps_site_cd=site_cd, rlps_site_nm=site_nm)
                if distant:
                    ctx.disease_row(p, fvid, mtdg_ymd=fu, mtst_site_cd=site_cd, mtst_site_nm=site_nm)
                start = ctx.days(fu, ctx.randint(7, 21))
                if site_cd == "C50":
                    sd = ctx.days(fu, ctx.randint(14, 28))
                    if sd <= ctx.today:
                        _, _, los2 = _surgery(ctx, p, st, sd, False, salvage=True)
                        _surg_path(ctx, p, st, sd, False, False, salvage=True)
                        start = ctx.days(sd, ctx.randint(30, 45))
                last_end, last_aid = _palliative(ctx, p, st, start, lines, ecog, first_intent=3 if distant else 6)
                if last_aid is not None and ctx.bern(0.5 if distant else 0.25) and _die(ctx, p, last_end):
                    ctx.antp_update(last_aid, treatment_outcome=0)
                    break
                fu = last_end
            fu = ctx.days(fu, ctx.randint(100, 130) if recurred else ctx.randint(170, 200)); k += 1

        # ---- 4) 치료 후 산과력 (폐경 전 항암 환자)
        _obstetric_followup(ctx, p, st, age)
        ctx.finalize_person(p)

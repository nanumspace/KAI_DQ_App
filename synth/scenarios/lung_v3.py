# -*- coding: utf-8 -*-
"""
폐암 코호트 시나리오 (v3)

v1 폐암 여정(`lung.py`)을 v3 테이블로 옮겼다. 특화 테이블 LUNG_CANCER 는 환자당 1행(진단 입원 방문에 매단다).

여정: 진단 입원(3일) → 병기별 치료 → 추적
  I~II   폐엽절제술 + 일부 보조항암 (선암·대세포 cisplatin/pemetrexed, 그 외 cisplatin/gemcitabine)
  III    동시항암방사선 (비소세포 주간 carboplatin/paclitaxel, 소세포 제한기 etoposide/cisplatin)
  IV     소세포 확장기 etoposide/cisplatin, EGFR 양성 osimertinib(진행 시 carboplatin/pemetrexed),
         선암·대세포 pembrolizumab+carboplatin+pemetrexed, 편평·기타 pembrolizumab+carboplatin+paclitaxel
         → 진행 시 docetaxel (소세포는 2차 요법 없음)
  pemetrexed 는 선암·대세포에만 쓴다. 공고요법(durvalumab)은 약물 목록에 없어 만들지 않는다.
특화 값:
  clinical_stage 는 clinical_stage_ajcc_edition 판의 병기군 (SEM3-LC-001), TNM 은 병기 표기와 같은 병기가 되도록 맞춘다,
  소세포폐암 일부는 LD/ED 이고 판수가 비어 있다 (SEM3-LC-002),
  histology_icdo3_code 는 histologic_diagnosis 범주와 맞고 (SEM3-LC-003), 원발 부위는 C34.x (SEM3-LC-004),
  stage_iv_diagnosis_date 는 처음부터 IV기이면 진단일과 같고, 수술 후 재발이면 재발일이다.
"""
from framework_v3 import *

LC = 4115276
HIST = {1: "Adenocarcinoma", 2: "Squamous cell carcinoma", 3: "Large cell carcinoma", 4: "Small cell carcinoma",
        5: "Carcinoma tumor 계열", 6: "NSCLC NOS", 7: "기타"}
ICDO3 = {1: ["8140/3", "8140/3", "8140/3", "8250/3", "8255/3"], 2: ["8070/3", "8070/3", "8071/3"], 3: ["8012/3"],
         4: ["8041/3"], 5: ["8010/3"], 6: ["8046/3"], 7: ["8560/3"]}
# 판 공통의 큰 병기군. 판마다 표기가 다르다.
BASE = ["IA", "IB", "IIA", "IIB", "IIIA", "IIIB", "IV"]
BASE_P = [0.16, 0.10, 0.07, 0.07, 0.12, 0.08, 0.40]
TNM = {"IA": ("T1b", "N0", "M0"), "IB": ("T2a", "N0", "M0"), "IIA": ("T2b", "N0", "M0"), "IIB": ("T3", "N0", "M0"),
       "IIIA": ("T2a", "N2", "M0"), "IIIB": ("T2a", "N3", "M0"), "IV": ("T2a", "N2", "M1b")}
NONSQ = (1, 3)                          # 선암·대세포: pemetrexed 사용 가능한 조직형
LOBE = [("RUL", "우상엽", "C34.1"), ("RML", "우중엽", "C34.2"), ("RLL", "우하엽", "C34.3"), ("LUL", "좌상엽", "C34.1"), ("LLL", "좌하엽", "C34.3")]
MET_SITES = [("Brain",), ("Bone",), ("Liver",), ("Adrenal gland",), ("Contralateral lung",)]

MORPH = {"8140/3": "Adenocarcinoma, NOS", "8250/3": "Adenocarcinoma, lepidic pattern", "8255/3": "Adenocarcinoma with mixed subtypes",
         "8070/3": "Squamous cell carcinoma, NOS", "8071/3": "Squamous cell carcinoma, keratinizing", "8012/3": "Large cell carcinoma",
         "8041/3": "Small cell carcinoma", "8010/3": "Carcinoma, NOS", "8046/3": "Non-small cell carcinoma, NOS",
         "8560/3": "Adenosquamous carcinoma"}

CT_REPORT = ("Chest CT (contrast). {lobe} 에 spiculated mass. {node}. {met} "
             "Impression: Lung cancer, {lobe}, c{t}{n}{m}. Recommend tissue confirmation.")
BX_REPORT = ("Lung, {lobe}, bronchoscopic biopsy: {hist}. Differentiation: {diff}. "
             "Pathologic TNM is not assigned on a biopsy specimen; clinical stage c{t}{n}{m} is from imaging.")
PATH_REPORT = ("Lung, {lobe}, lobectomy: {hist}. Differentiation: {diff}. Visceral pleural invasion: {vpi}. "
               "Lymph nodes: {ln}. Pathologic stage p{t}{n}{m}.")


def stage_label(ctx, base, edition):
    """큰 병기군을 판에 맞는 표기로. 8판은 IA→IA1/2/3, IV→IVA/IVB, IIIB 일부→IIIC."""
    if edition == 8:
        if base == "IA":
            return ctx.choice(["IA1", "IA2", "IA3"], p=[0.25, 0.45, 0.30])
        if base == "IIIB" and ctx.bern(0.3):
            return "IIIC"
        if base == "IV":
            return ctx.choice(["IVA", "IVB"], p=[0.55, 0.45])
    return base


def generate(ctx: CtxV3, n=100):
    for _ in range(n):
        gender = FEMALE if ctx.bern(0.38) else MALE
        age = int(ctx.normal(67, 9, 35, 90, 0))
        index = D(2019, 1, 1) + dt.timedelta(days=ctx.randint(0, 365 * 5))
        p = ctx.person(gender, age, index)
        hist = ctx.choice([1, 2, 4, 3, 6, 5, 7], p=[0.52, 0.22, 0.12, 0.04, 0.05, 0.03, 0.02])
        base = ctx.choice(BASE, p=BASE_P)
        if hist == 4 and base not in ("IIIB", "IV"):     # 소세포는 수술 대상 조기 병기로 만들지 않는다 (LD=IIIB, ED=IV)
            base = ctx.choice(["IIIB", "IV"])
        # 소세포폐암은 대부분 제한기/확장기(LD/ED)로 병기를 적고 AJCC 판수는 비운다.
        if hist == 4 and ctx.bern(0.7):
            edition, stage = None, ("ED" if base == "IV" else "LD")
        else:
            edition = ctx.choice([8, 7, 6], p=[0.78, 0.19, 0.03])
            stage = stage_label(ctx, base, edition)
        t, nn, m = TNM[base]
        if stage in ("IA1", "IA2", "IA3"):
            t = {"IA1": "T1a", "IA2": "T1b", "IA3": "T1c"}[stage]
        elif stage == "IIIC":
            t, nn = "T4", "N3"
        elif stage == "IVB":
            m = "M1c"
        stage_iv = base == "IV"
        lobe_cd, lobe_nm, c34 = ctx.choice(LOBE)
        smoker = ctx.bern(0.75 if gender == MALE else 0.15)
        cur_smok = smoker and ctx.bern(0.5)
        egfr = (hist == 1) and ctx.bern(0.45 if gender == FEMALE else 0.3)
        icd = ctx.choice(ICDO3[hist])

        # ---- 1) 진단 입원 (3일)
        dx_vid = ctx.visit(p, index, INPATIENT, los=3)
        ctx.condition(p, index, LC, vid=dx_vid)
        ctx.condition(p, index, 258375 if hist == 4 else 4311499, vid=dx_vid)
        if smoker and ctx.bern(0.4): ctx.condition(p, index, 255573, vid=dx_vid)     # COPD
        if ctx.bern(0.35): ctx.condition(p, index, 320128, vid=dx_vid)               # HTN
        if ctx.bern(0.2): ctx.condition(p, index, 201826, vid=dx_vid)                # T2DM
        ctx.procedure(p, index, 4059400, vid=dx_vid)                                  # chest CT
        bx_day = ctx.days(index, 1)
        ctx.procedure(p, bx_day, 4032404, vid=dx_vid)                                 # bronchoscopy biopsy
        pet_day = ctx.days(index, 2)
        ctx.procedure(p, pet_day, 4305790, vid=dx_vid)                                # PET
        ctx.labs(p, index, [3000963, 3010813, 3017732, 3024929, 3016723, 3013721, 3006923, 3020491, 3022250], vid=dx_vid)
        ht = ctx.normal(170 if gender == MALE else 157, 6, 145, 190); wt = ctx.normal(66 if gender == MALE else 56, 9, 38, 110)
        ctx.measure(p, index, 3036277, ht, vid=dx_vid); ctx.measure(p, index, 3025315, wt, vid=dx_vid)
        ctx.measure(p, index, 3038553, round(wt / (ht / 100) ** 2, 1), vid=dx_vid)
        ecog = ctx.choice([0, 1, 2, 3], p=[0.3, 0.45, 0.2, 0.05])
        ctx.observation(p, index, 4257895, vid=dx_vid, value_number=ecog, value_string=f"ECOG {ecog}")
        ctx.observation(p, index, 4275495, vid=dx_vid, value_string="Current smoker" if cur_smok else ("Ex-smoker" if smoker else "Never smoker"))
        if stage_iv:
            pool = [s_ for s_ in MET_SITES if s_[0] != "Contralateral lung"] if stage == "IVB" else MET_SITES
            met_nm = ctx.choice(pool)[0]
            if met_nm == "Contralateral lung":
                m = "M1a"
        else:
            met_nm = None
        node_txt = ("Mediastinal lymphadenopathy" if nn in ("N2", "N3") else "No significant lymphadenopathy")
        if met_nm:
            met_txt = f"Multiple extrathoracic metastases including {met_nm}." if stage == "IVB" else f"Metastasis to {met_nm}."
        else:
            met_txt = "No distant metastasis."
        ctx.note(p, index, CT_REPORT.format(lobe=lobe_nm, node=node_txt, met=met_txt, t=t, n=nn, m=m), vid=dx_vid)
        hist_txt = MORPH[icd]
        if hist == 4:
            diff = "not graded (high-grade neuroendocrine carcinoma)"
        elif hist == 3:
            diff = "poorly differentiated"
        else:
            diff = ctx.choice(["well", "moderately", "poorly"]) + " differentiated"
        ctx.note(p, bx_day, BX_REPORT.format(lobe=lobe_nm, hist=hist_txt, diff=diff, t=t, n=nn, m=m),
                 note_type=44814640, note_class=36716165, vid=dx_vid)
        row = ctx.disease_row(p, dx_vid, diag_rgst_ymd=index, histologic_diagnosis=hist, histology_icdo3_code=icd,
                              primary_site_icdo3_code=c34, histologic_diagnosis_source_value=HIST[hist],
                              clinical_stage=stage, clinical_stage_ajcc_edition=edition,
                              stage_iv_diagnosis_date=index if stage_iv else None)
        if hist != 4:
            gmt_day = ctx.days(index, ctx.randint(5, 12))
            gvid = ctx.visit_on(p, gmt_day)
            pdl1 = ctx.choice([0, 1, 5, 25, 50, 80])
            alk = ctx.bern(0.04) and not egfr
            kras = (not egfr and not alk) and ctx.bern(0.2)
            ctx.note(p, gmt_day, f"Molecular pathology (NGS panel): EGFR {'exon 19 deletion' if egfr else 'wild type'}; ALK IHC "
                                 f"{'positive' if alk else 'negative'}; KRAS {'G12C' if kras else 'wild type'}; PD-L1 TPS {pdl1}%.",
                     note_type=44814640, note_class=36716165, vid=gvid)

        # ---- 2) 치료
        last = ctx.days(index, 3)
        surgery_day = None
        sacts = []
        if base in ("IA", "IB", "IIA", "IIB", "IIIA") and ecog <= 2:
            surgery_day = ctx.days(index, ctx.randint(21, 45))
            svid = ctx.visit(p, surgery_day, INPATIENT, los=7)
            ctx.procedure(p, surgery_day, 4033181, vid=svid)
            path_day = ctx.days(surgery_day, ctx.randint(3, 7))
            pn = nn if ctx.bern(0.75) else ctx.choice(["N0", "N1", "N2"])
            tot_ln = ctx.randint(8, 30); pos_ln = 0 if pn == "N0" else ctx.randint(1, min(6, tot_ln))
            ctx.note(p, path_day, PATH_REPORT.format(lobe=lobe_nm, hist=hist_txt, diff=diff,
                                                     vpi="present" if ctx.bern(0.3) else "absent", ln=f"{pos_ln}/{tot_ln} positive", t=t, n=pn, m="M0"),
                     note_type=44814640, note_class=36716165, vid=svid)
            ctx.labs(p, ctx.days(surgery_day, 1), [3000963, 3010813, 3016723], vid=svid)
            last = ctx.days(surgery_day, 7)
            if ctx.bern(0.2):
                ctx.ae(p, ctx.days(surgery_day, 2), 437663, 1, vid=svid)   # postoperative fever
            if base in ("IB", "IIA", "IIB", "IIIA") and ctx.bern(0.7):
                s = ctx.days(surgery_day, ctx.randint(35, 60))
                adj_name, adj_drugs = (("Cisplatin + Pemetrexed", [1397141, 1304919]) if hist in NONSQ
                                       else ("Cisplatin + Gemcitabine", [1397141, 1314924]))
                sid, e, cyc = ctx.sact(p, adj_name, adj_drugs, s, 4, 2, ecog=ecog, response="NE")
                sacts.append(sid); last = e
                ctx.monitor(p, cyc, adj_drugs)
        elif base in ("IIIA", "IIIB") or (base in ("IA", "IB", "IIA", "IIB") and ecog > 2):
            s = ctx.days(index, ctx.randint(14, 30))
            if hist == 4:   # 소세포 제한기(LD): 흉부방사선과 동시 etoposide/cisplatin
                drugs = [1350504, 1397141]
                sid, e, cyc = ctx.sact(p, "Etoposide + Cisplatin (concurrent chemoradiation)", drugs, s, 4, 5, ecog=ecog,
                                       response=ctx.choice(["PR", "SD", "CR"]), cycle_days=21, inpatient_first=True)
            else:
                drugs = [1344905, 1378382]
                sid, e, cyc = ctx.sact(p, "Weekly Carboplatin + Paclitaxel (CCRT)", drugs, s, 6, 5, ecog=ecog,
                                       response=ctx.choice(["PR", "SD", "CR"]), cycle_days=7)
            sacts.append(sid); last = e
            ctx.monitor(p, cyc, drugs)
            rvid = ctx.visit_on(p, s)
            ctx.procedure(p, s, 4181206, vid=rvid)
        else:  # IV 또는 소세포
            s = ctx.days(index, ctx.randint(10, 25))
            resp1 = (ctx.choice(["PR", "CR", "SD", "PD"]) if hist == 4
                     else ctx.choice(["PR", "SD", "CR"], p=[0.7, 0.2, 0.1]) if egfr
                     else ctx.choice(["PR", "SD", "PD"], p=[0.5, 0.35, 0.15]))
            sid, e, cyc, drugs = _advanced_sact(ctx, p, hist, egfr, s, ecog, resp1, inpatient_first=True)
            sacts.append(sid); last = e
            ctx.monitor(p, cyc, drugs)
            pd_day = ctx.days(e, ctx.randint(0, 14) if resp1 == "PD" else ctx.randint(20, 120))
            if (resp1 == "PD" or ctx.bern(0.55)) and pd_day <= ctx.today:
                pvid = ctx.visit_on(p, pd_day)
                ctx.procedure(p, pd_day, 4059400, vid=pvid)
                ctx.note(p, pd_day, f"Chest CT: interval increase of {lobe_nm} mass and new nodules. Progressive disease.", vid=pvid)
                ctx.sact_update(sid, date_of_progression=pd_day, recurrence_anatomic_site=ctx.choice(["Lung", "Liver", "Bone", "Brain"]))
                last = pd_day
                if hist != 4 and ecog <= 2 and ctx.bern(0.7):   # 소세포는 목록에 2차 약제가 없어 만들지 않는다
                    s2 = ctx.days(pd_day, ctx.randint(7, 21))
                    # EGFR 진행: 백금+pemetrexed, 그 외 docetaxel
                    name2, drugs2 = (("Carboplatin + Pemetrexed", [1344905, 1304919]) if egfr else ("Docetaxel", [1315942]))
                    sid2, e2, cyc2 = ctx.sact(p, name2, drugs2, s2, ctx.randint(2, 6), 3, ecog=min(ecog + 1, 3),
                                              response=ctx.choice(["SD", "PD", "PR"]))
                    sacts.append(sid2); last = e2
                    ctx.monitor(p, cyc2, drugs2)
                if ctx.bern(0.5):
                    dd = min(ctx.days(last, ctx.randint(15, 180)), ctx.today)
                    if dd >= last:
                        ctx.set_death(p, dd)
                        ctx.visit(p, ctx.days(dd, -2), INPATIENT, los=2)

        # ---- 3) 추적 및 재발
        if p.death_date is None:
            fu = ctx.days(last, 90)
            recurred = False
            k = 0
            while fu <= ctx.today and k < 8:
                fvid = ctx.visit_on(p, fu)
                ctx.procedure(p, fu, 4059400, vid=fvid)
                ctx.labs(p, fu, [3000963, 3028641], vid=fvid)
                if surgery_day and not recurred and ctx.bern(0.08):
                    recurred = True
                    site = ctx.choice(MET_SITES)[0]
                    ctx.note(p, fu, f"Chest CT: new {site} lesion suspicious for recurrence.", vid=fvid)
                    row["stage_iv_diagnosis_date"] = fu
                    if sacts:    # 보조항암 후 재발이면 직전 요법에 진행일을 남긴다
                        ctx.sact_update(sacts[-1], date_of_progression=fu, recurrence_anatomic_site=site)
                    if ecog <= 2:
                        s3 = ctx.days(fu, ctx.randint(10, 30))
                        if s3 <= ctx.today:
                            sid3, e3, cyc3, drugs3 = _advanced_sact(ctx, p, hist, egfr, s3, ecog, "PR", inpatient_first=False)
                            ctx.sact_update(sid3, recurrence_anatomic_site=site)
                            ctx.monitor(p, cyc3, drugs3)
                            fu = e3
                fu = ctx.days(fu, ctx.randint(80, 100)); k += 1
        ctx.finalize_person(p)


def _advanced_sact(ctx, p, hist, egfr, start, ecog, response, inpatient_first):
    """IV기(또는 재발) 1차 전신요법. 조직형에 맞는 약제만 쓴다 (pemetrexed 는 선암·대세포만).
    반환 (sact_id, end_date, cycle_dates, drug_concepts)."""
    if hist == 4:
        name, drugs = "Etoposide + Cisplatin", [1350504, 1397141]
    elif egfr:
        drugs = [35604205]
        sid, e, cyc = ctx.sact(p, "Osimertinib", drugs, start, ctx.randint(6, 30), 3, ecog=ecog, response=response,
                               cycle_days=28, oral=True)
        return sid, e, cyc, drugs
    elif hist in NONSQ:
        name, drugs = "Pembrolizumab + Carboplatin + Pemetrexed", [45775965, 1344905, 1304919]
    else:
        name, drugs = "Pembrolizumab + Carboplatin + Paclitaxel", [45775965, 1344905, 1378382]
    sid, e, cyc = ctx.sact(p, name, drugs, start, 4, 3, ecog=ecog, response=response, inpatient_first=inpatient_first)
    return sid, e, cyc, drugs

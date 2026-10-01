# -*- coding: utf-8 -*-
"""
대장암 코호트 시나리오 (v3)

v1 대장암 여정(`colorectal.py`)을 v3 테이블로 옮겼다. 특화 테이블 COLORECTAL_CANCER 는 환자당 1행
(진단 방문에 매달고 diag_rgst_ymd = 진단일)이며, 자유기재(varchar) 열은 해당되는 일부 환자만 채운다.

여정: 진단 외래(대장내시경 생검, CT, 직장은 MRI, CEA) → 병기별 치료 → 추적(CT + CEA)
  결장 I~III      결장절제술 + III기(및 일부 고위험 II기) 보조 FOLFOX/CAPOX
  직장 II~III     수술 전 동시항암방사선(capecitabine) → LAR/APR(장루) → 보조항암
  IV              일부 고식적 절제, FOLFOX + bevacizumab 1차 → FOLFIRI + bevacizumab 2차, 일부 사망
  추적            6개월 간격 CT + CEA, 일부 재발 → 고식적 항암
"""
from framework_v3 import *

COLON, RECTOSIG, RECTUM = 4180790, 443381, 4164337
SITES = [  # (kcd, site name, cohort concept, side)
    ("C18.0", "Cecum", COLON, "R"), ("C18.2", "Ascending colon", COLON, "R"), ("C18.4", "Transverse colon", COLON, "R"),
    ("C18.6", "Descending colon", COLON, "L"), ("C18.7", "Sigmoid colon", COLON, "L"),
    ("C19", "Rectosigmoid junction", RECTOSIG, "L"), ("C20", "Rectum", RECTUM, "L"),
]
SITE_P = [0.08, 0.17, 0.08, 0.07, 0.25, 0.05, 0.30]
STAGES = ["I", "II", "III", "IV"]
STAGE_P = [0.20, 0.25, 0.33, 0.22]
TSIZE = {"T1": (0.8, 2.0), "T2": (2.0, 4.0), "T3": (3.0, 6.0), "T4a": (4.5, 8.0), "T4b": (5.0, 9.0)}
HIST = {"8140/3": "Adenocarcinoma, NOS", "8480/3": "Mucinous adenocarcinoma", "8490/3": "Signet ring cell carcinoma"}
GRADE = {"G1": "Well differentiated", "G2": "Moderately differentiated", "G3": "Poorly differentiated"}
DEPTH = {"T0": "No residual tumor", "T1": "Submucosa", "T2": "Muscularis propria", "T3": "Subserosa / perirectal fat",
         "T4a": "Serosa (visceral peritoneum)", "T4b": "Adjacent organ"}
GROSS = ["ulcerofungating", "ulceroinfiltrative", "polypoid", "infiltrative"]
MET_SITES = ["Liver", "Lung", "Peritoneum", "Distant lymph node", "Bone"]
MET_P = [0.5, 0.2, 0.15, 0.1, 0.05]
CC_TEXT = {"R": ["Iron deficiency anemia found on health check-up", "Vague right lower quadrant abdominal pain for 3 months"],
           "L": ["Hematochezia for 2 months", "Change of bowel habit (constipation) for 3 months"],
           "REC": ["Hematochezia and tenesmus for 2 months", "Blood-tinged stool with mucus for 6 weeks"]}

COLONO_REPORT = ("Colonoscopy: {desc} mass at {site}, {size} cm in size, occupying about {circ}% of the lumen. "
                 "Multiple biopsies taken. Impression: {site} cancer, r/o adenocarcinoma. Biopsy pending.")
BX_REPORT = "Colon, {site}, endoscopic biopsy: {hist}, {grade}."
CT_REPORT = ("CT abdomen and pelvis (contrast). Wall thickening of the {site} ({size} cm) with {node}. {met} "
             "Impression: {site} cancer, c{t}{n}{m}.")
SGPT_REPORT = ("{organ}, resection: {hist}, {grade}. Tumor size {size} cm, gross type {gross}. Depth of invasion: {depth}. "
               "Lymph nodes: {pos}/{tot} positive. Pathologic stage {tnm}.")

AE_BASE = {27674: 0.15, 196523: 0.10, 301794: 0.15, 439777: 0.10, 4223659: 0.12, 4166735: 0.05, 140214: 0.02, 4304213: 0.03,
           4141062: 0.08, 4265412: 0.06, 432791: 0.08}


def _pool(drugs):
    w = dict(AE_BASE)
    if 1320011 in drugs: w[4166735] += 0.30     # oxaliplatin: 말초신경병증
    if 1367268 in drugs or 1337620 in drugs: w[196523] += 0.15
    if 1337620 in drugs: w[140214] += 0.08      # hand-foot syndrome 을 rash 로 대표
    return tuple(w.items())


def _ctnm(ctx, stage):
    if stage == "I":
        return ctx.choice(["T1", "T2"], p=[0.4, 0.6]), "N0", "M0"
    if stage == "II":
        return ctx.choice(["T3", "T4a", "T4b"], p=[0.75, 0.2, 0.05]), "N0", "M0"
    if stage == "III":
        return ctx.choice(["T2", "T3", "T4a", "T4b"], p=[0.1, 0.6, 0.2, 0.1]), ctx.choice(["N1a", "N1b", "N2a", "N2b"], p=[0.3, 0.3, 0.25, 0.15]), "M0"
    return ctx.choice(["T3", "T4a", "T4b"], p=[0.6, 0.3, 0.1]), ctx.choice(["N1b", "N2a", "N2b"]), ctx.choice(["M1a", "M1b"], p=[0.6, 0.4])


def _cap_cycles(ctx, start, cycles, cd):
    """마지막 사이클이 검증일을 넘지 않도록 사이클 수 제한."""
    return max(0, min(cycles, (ctx.today - start).days // cd))


def _death(ctx, p, dd):
    if dd > ctx.today:
        return
    ctx.set_death(p, dd)
    ctx.visit(p, ctx.days(dd, -2), INPATIENT, los=2)


def _surgery(ctx, p, row, day, kcd, site_nm, side, rectal, low, obstruction, perforation, purpose):
    """수술 입원. 반환 (퇴원일, 장루 정보). 자유기재 열 일부를 질환 행에 채운다."""
    los = ctx.randint(6, 10) if purpose == "CUR" else ctx.randint(8, 14)
    svid = ctx.visit(p, day, INPATIENT, los=los)
    apr = rectal and low and ctx.bern(0.5)
    if rectal:
        ctx.procedure(p, day, 4148096, vid=svid)
        op_nm = "Abdominoperineal resection" if apr else "Low anterior resection"
    else:
        ctx.procedure(p, day, 4050470, vid=svid)
        op_nm = ("Anterior resection" if kcd == "C19" else "Right hemicolectomy" if side == "R"
                 else "Left hemicolectomy" if site_nm == "Descending colon" else "Anterior resection (sigmoidectomy)")
    lap = ctx.bern(0.8) and not perforation
    conv = lap and ctx.bern(0.08)
    ostomy = None
    if apr:
        ostomy = dict(temporary=False, kind="COLO", why="Permanent end colostomy (APR)")
    elif rectal and ctx.bern(0.8 if low else 0.4):
        ostomy = dict(temporary=True, kind="ILEO", why="Anastomosis protection (diverting ileostomy)")
    elif (obstruction or perforation) and ctx.bern(0.5):
        ostomy = dict(temporary=True, kind="COLO", why="Obstruction / perforation (Hartmann)")
    if ostomy and ctx.bern(0.6):
        row["ostm_frsn_clsf_etc_cont"] = ostomy["why"] + (", low anastomosis with poor tissue perfusion" if ostomy["temporary"] and ostomy["kind"] == "ILEO" else "")
    if not apr and ctx.bern(0.25):
        row["anes_mthd_etc_cont"] = ctx.choice(["Double stapling technique (side-to-end)", "Stapled end-to-end with reinforcing sutures",
                                                "Colonic J-pouch anastomosis" if rectal else "Intracorporeal side-to-side stapled anastomosis"])
    if purpose == "PAL" or conv:
        row["afop_asmt_item_etc_cont"] = ("Palliative resection, R2 (macroscopic residual disease)" if purpose == "PAL"
                                          else "Converted to open surgery due to adhesion; R0 resection")
    ebl = int(ctx.normal(150 if lap and not conv else 350, 120, 20, 2000, 0))
    compl = ctx.bern(0.15)
    dsch = ctx.days(day, los)
    ctx.labs(p, ctx.days(day, 1), [3000963, 3010813, 3016723, 3020460], vid=svid)
    if compl:
        ctx.ae(p, ctx.days(day, ctx.randint(2, 5)), 437663, ctx.randint(1, 2), vid=svid)
        ctx.condition(p, ctx.days(day, 2), 437663, vid=svid)
    ctx.note(p, dsch, f"Discharge summary. {op_nm} ({'laparoscopic' if lap else 'open'}{', converted to open' if conv else ''}) on {day.isoformat()} "
                      f"for {site_nm.lower()} cancer. EBL {ebl} mL. Postoperative course "
                      f"{'complicated by fever, treated conservatively' if compl else 'uneventful'}. Discharged on POD {los}.",
             note_type=44814641, note_class=36716213, vid=svid)
    return dsch, ostomy


def _pathology(ctx, p, row, surgery_day, site_nm, rectal, kcd, hist_cd, grade, pt, pn, pm, after_ccrt, csize, met_names=()):
    path_day = ctx.days(surgery_day, ctx.randint(0, 2))
    read_day = ctx.days(path_day, ctx.randint(3, 7))
    svid = ctx.visit_on(p, path_day)
    psize = 0.0 if pt == "T0" else round(csize * ctx.rand(0.7, 1.15), 1)
    tot_ln = ctx.randint(12, 40)
    pos_ln = min({"N0": 0, "N1a": 1, "N1b": ctx.randint(2, 3), "N2a": ctx.randint(4, 6), "N2b": ctx.randint(7, 12)}[pn], tot_ln)
    rm_pos = pt == "T4b" and ctx.bern(0.3)
    organ = "Rectum" if rectal else ("Rectosigmoid colon" if kcd == "C19" else "Colon")
    ctx.note(p, read_day, SGPT_REPORT.format(organ=organ, hist=HIST[hist_cd], grade=GRADE[grade].lower(), size=psize, gross=ctx.choice(GROSS),
                                             depth=DEPTH[pt], pos=pos_ln, tot=tot_ln, tnm=("y" if after_ccrt else "") + f"p{pt}{pn}{pm}"),
             note_type=44814640, note_class=36716165, vid=svid)
    row["inva_dgre_nm"] = DEPTH[pt]
    row["radi_rsmg_invl_yn_spnm"] = "침범" if rm_pos else "침범 없음"
    if rectal:
        row["tme_qlt_dgre_spnm"] = ctx.choice(["Complete", "Nearly complete", "Incomplete"], p=[0.75, 0.2, 0.05])
    return pos_ln, tot_ln


def generate(ctx: CtxV3, n=100):
    for _ in range(n):
        gender = FEMALE if ctx.bern(0.42) else MALE
        age = int(ctx.normal(65, 10, 30, 90, 0))
        index = D(2019, 1, 1) + dt.timedelta(days=ctx.randint(0, 365 * 5 + 150))
        p = ctx.person(gender, age, index)
        kcd, site_nm, dx_concept, side = ctx.choice(SITES, p=SITE_P)
        rectal = kcd == "C20"
        stage = ctx.choice(STAGES, p=STAGE_P)
        t, nn, m = _ctnm(ctx, stage)
        size = round(ctx.rand(*TSIZE[t]), 1)
        hist_cd = ctx.choice(list(HIST), p=[0.85, 0.12, 0.03])
        grade = ctx.choice(list(GRADE), p=[0.15, 0.7, 0.15])
        ecog = ctx.choice([0, 1, 2, 3], p=[0.4, 0.4, 0.15, 0.05])
        obstruction = ctx.bern(0.10) if t in ("T3", "T4a", "T4b") else False
        perforation = (not obstruction) and t in ("T4a", "T4b") and ctx.bern(0.1)

        # ---- 1) 진단 외래
        dx_vid = ctx.visit(p, index, OUTPATIENT)
        ctx.condition(p, index, dx_concept, vid=dx_vid)
        for prob, cid in ((0.35, 320128), (0.2, 201826), (0.15, 432867), (0.02, 81893)):
            if ctx.bern(prob): ctx.condition(p, index, cid, vid=dx_vid)
        ctx.procedure(p, index, 4179986, vid=dx_vid)
        circ = ctx.randint(25, 95) if t != "T1" else ctx.randint(10, 30)
        ctx.note(p, index, COLONO_REPORT.format(desc=ctx.choice(["Ulcerofungating", "Ulceroinfiltrative", "Polypoid"]), site=site_nm, size=size, circ=circ),
                 note_type=32831, note_class=36716177, vid=dx_vid)
        ctx.note(p, ctx.days(index, ctx.randint(2, 4)), BX_REPORT.format(site=site_nm, hist=HIST[hist_cd], grade=GRADE[grade].lower()),
                 note_type=44814640, note_class=36716165, vid=dx_vid)
        ht = ctx.normal(168 if gender == MALE else 156, 6, 145, 190); wt = ctx.normal(67 if gender == MALE else 57, 9, 38, 110)
        ctx.measure(p, index, 3036277, ht, vid=dx_vid); ctx.measure(p, index, 3025315, wt, vid=dx_vid)
        ctx.measure(p, index, 3038553, round(wt / (ht / 100) ** 2, 1), vid=dx_vid)
        ctx.observation(p, index, 4257895, vid=dx_vid, value_number=ecog, value_string=f"ECOG {ecog}")
        row = ctx.disease_row(p, dx_vid, diag_rgst_ymd=index)

        # ---- 병기 결정 검사 (CT / MRI / CEA)
        ct_day = ctx.days(index, ctx.randint(3, 8))
        wvid = ctx.visit(p, ct_day, OUTPATIENT)
        ctx.procedure(p, ct_day, 4207701, vid=wvid)
        met_nm = ctx.choice(MET_SITES, p=MET_P) if stage == "IV" else None
        node_txt = "enlarged regional lymph nodes" if nn != "N0" else "no significant regional lymphadenopathy"
        met_txt = f"Multiple metastatic nodules in the {met_nm.lower()}." if met_nm else "No distant metastasis."
        ctx.note(p, ct_day, CT_REPORT.format(site=site_nm.lower(), size=size, node=node_txt, met=met_txt, t=t[1:], n=nn[1:], m=m[1:]),
                 note_type=44814637, note_class=36716164, vid=wvid)
        low = False
        if rectal or kcd == "C19":
            ctx.procedure(p, ct_day, 4123795, vid=wvid)
            anvg = round(ctx.rand(2.0, 12.0), 2) if rectal else round(ctx.rand(12.0, 16.0), 2)
            low = anvg < 5
            ctx.note(p, ct_day, f"Rectal MRI. Tumor lower margin {anvg} cm from anal verge. mrT{t[1:]}, mrN{nn[1:]}. "
                                f"Shortest distance to mesorectal fascia {round(ctx.rand(0.5, 15), 1)} mm.",
                     note_type=44814637, note_class=36716164, vid=wvid)
        ctx.labs(p, ct_day, [3000963, 3010813, 3017732, 3024929, 3016723, 3013721, 3006923, 3020491, 3024128], vid=wvid)
        cea = ctx.lab_value(3028641, shift={"I": -3, "II": 0, "III": 4, "IV": 40}[stage], sd_scale={"IV": 4}.get(stage, 1.0), lo=0.3)
        ctx.measure(p, ct_day, 3028641, cea, vid=wvid)
        stag_day = ct_day
        if stage == "IV" and ctx.bern(0.6):
            stag_day = ctx.days(ct_day, ctx.randint(2, 6)); pv = ctx.visit_on(p, stag_day)
            ctx.procedure(p, stag_day, 4305790, vid=pv)
        if stage == "IV" and met_nm == "Peritoneum" and ctx.bern(0.5):
            row["inap_dsnt_mtst_site_etc_cont"] = "Peritoneal seeding with liver metastasis" if ctx.bern(0.5) else "Peritoneal carcinomatosis, multiple sites"
        elif stage == "IV" and met_nm == "Liver" and ctx.bern(0.2):
            row["inap_dsnt_mtst_site_etc_cont"] = "Liver and para-aortic lymph node metastases"

        # ---- 2) 치료
        last = max(stag_day, ctx.days(index, 10))
        surgery_day = None
        had_oxali = False
        n_sact = 0
        ccrt = rectal and stage in ("II", "III") and ecog <= 2
        pt, pn, pm = t, nn, "M0"
        if stage in ("I", "II", "III") and ecog <= 2:
            if ccrt:
                s = ctx.days(last, ctx.randint(10, 21))
                sid, e, cyc = ctx.sact(p, "Capecitabine (preoperative CCRT)", [1337620], s, 2, 1, ecog=ecog, response="NE", cycle_days=21)
                ctx.monitor(p, cyc, [1337620], ae_p=0.3, ae_pool=_pool([1337620]))
                ctx.procedure(p, s, 4181206, vid=ctx.visit_on(p, s))
                ctx.sact_update(sid, best_overall_response=ctx.choice(["PR", "SD", "CR"], p=[0.6, 0.25, 0.15]))
                rs_day = ctx.days(e, ctx.randint(35, 50))
                ctx.procedure(p, rs_day, 4123795, vid=ctx.visit_on(p, rs_day))
                trg = ctx.choice(["1", "2", "3", "4"], p=[0.15, 0.35, 0.35, 0.15])
                ctx.note(p, rs_day, f"Rectal MRI after CCRT. Interval decrease of tumor. mrTRG {trg}.", note_type=44814637, note_class=36716164)
                surgery_day = ctx.days(rs_day, ctx.randint(7, 21))
                if trg == "1": pt, pn = "T0", "N0"
                elif trg == "2":
                    pt = {"T4b": "T3", "T4a": "T3", "T3": "T2", "T2": "T1"}.get(t, t); pn = "N0" if ctx.bern(0.7) else "N1a"
                else:
                    pt = t if ctx.bern(0.7) else {"T4b": "T4a", "T4a": "T3", "T3": "T3", "T2": "T2"}[t]
                    pn = nn if ctx.bern(0.6) else ctx.choice(["N0", "N1a", "N1b"])
            else:
                surgery_day = ctx.days(last, ctx.randint(10, 30))
                pt = t if ctx.bern(0.8) else ctx.choice(["T2", "T3", "T4a"])
                pn = nn if ctx.bern(0.75) else ctx.choice(["N0", "N1a", "N1b", "N2a"])
            dsch, ostomy = _surgery(ctx, p, row, surgery_day, kcd, site_nm, side, rectal, low, obstruction, perforation, "CUR")
            last = dsch
            _pathology(ctx, p, row, surgery_day, site_nm, rectal, kcd, hist_cd, grade, pt, pn, pm, ccrt, size)
            path_stage = "III" if pn != "N0" else ("II" if pt in ("T3", "T4a", "T4b") else "I")
            if (path_stage == "III" or (path_stage == "II" and ctx.bern(0.3))) and ecog <= 2:
                s = ctx.days(surgery_day, ctx.randint(28, 50))
                if ctx.bern(0.6):
                    drugs, cd, reg, ncy = [1320011, 955632], 14, "FOLFOX", ctx.randint(8, 12)
                else:
                    drugs, cd, reg, ncy = [1320011, 1337620], 21, "CAPOX", ctx.randint(4, 8)
                ncy = _cap_cycles(ctx, s, ncy, cd)
                if ncy > 0:
                    sid, e, cyc = ctx.sact(p, reg, drugs, s, ncy, 2, ecog=ecog, response="NE", cycle_days=cd)
                    had_oxali = True; last = e
                    ctx.monitor(p, cyc, drugs, ae_pool=_pool(drugs))
            if ostomy and ostomy["temporary"] and ctx.bern(0.8):
                rd = ctx.days(max(ctx.days(surgery_day, 90), ctx.days(last, 30)), ctx.randint(0, 90))
                if rd <= ctx.today:
                    rvid = ctx.visit(p, rd, INPATIENT, los=5)
                    ctx.labs(p, ctx.days(rd, 1), [3000963, 3010813, 3016723], vid=rvid)
                    last = max(last, ctx.days(rd, 5))
        elif stage == "IV":
            if obstruction and ctx.bern(0.7):
                sd = ctx.days(last, ctx.randint(3, 14))
                surgery_day = sd
                dsch, _ = _surgery(ctx, p, row, sd, kcd, site_nm, side, rectal, low, obstruction, perforation, "PAL")
                _pathology(ctx, p, row, sd, site_nm, rectal, kcd, hist_cd, grade, t, nn, "M1", False, size)
                last = dsch
            s = ctx.days(last, ctx.randint(10, 25))
            if ecog <= 2:
                drugs = [1320011, 955632, 1397599]
                ncy = _cap_cycles(ctx, s, ctx.randint(8, 12), 14)
                if ncy > 0:
                    sid, e, cyc = ctx.sact(p, "FOLFOX + Bevacizumab", drugs, s, ncy, 3, ecog=ecog,
                                           response=ctx.choice(["PR", "SD", "PD"], p=[0.5, 0.35, 0.15]), cycle_days=14)
                    had_oxali = True; last = e
                    ctx.monitor(p, cyc, drugs, ae_pool=_pool(drugs))
                    if ctx.bern(0.55):
                        pd_day = ctx.days(e, ctx.randint(20, 120))
                        if pd_day <= ctx.today:
                            pvid = ctx.visit_on(p, pd_day)
                            ctx.procedure(p, pd_day, 4207701, vid=pvid)
                            new_nm = ctx.choice(MET_SITES, p=MET_P)
                            ctx.note(p, pd_day, f"CT abdomen and pelvis: interval increase of {met_nm.lower()} metastases and new {new_nm.lower()} lesions. "
                                                "Progressive disease.", note_type=44814637, note_class=36716164, vid=pvid)
                            ctx.sact_update(sid, date_of_progression=pd_day, recurrence_anatomic_site=new_nm)
                            last = pd_day
                            s2 = ctx.days(pd_day, ctx.randint(7, 21))
                            n2 = _cap_cycles(ctx, s2, ctx.randint(3, 8), 14)
                            if ctx.bern(0.7) and n2 > 0:
                                drugs2 = [1367268, 955632, 1397599]
                                sid2, e2, cyc2 = ctx.sact(p, "FOLFIRI + Bevacizumab", drugs2, s2, n2, 3, ecog=min(ecog + 1, 3),
                                                          response=ctx.choice(["SD", "PD", "PR"], p=[0.45, 0.4, 0.15]), cycle_days=14)
                                last = e2
                                ctx.monitor(p, cyc2, drugs2, ae_pool=_pool(drugs2))
                            if ctx.bern(0.5):
                                _death(ctx, p, ctx.days(last, ctx.randint(15, 180)))
            else:
                ctx.observation(p, s, 4257895, vid=ctx.visit_on(p, s), value_number=ecog, value_string=f"ECOG {ecog}, best supportive care")
                if ctx.bern(0.6):
                    _death(ctx, p, ctx.days(s, ctx.randint(30, 240)))
        else:
            ctx.observation(p, last, 4257895, vid=ctx.visit_on(p, last), value_number=ecog, value_string=f"ECOG {ecog}, not a surgical candidate")

        # ---- 3) 추적 및 재발
        if p.death_date is None:
            fu = ctx.days(last, 180)
            recurred = False; k = 0
            rec_p = {"I": 0.01, "II": 0.025, "III": 0.05, "IV": 0.0}[stage]
            while fu <= ctx.today and k < 10 and p.death_date is None:
                fvid = ctx.visit_on(p, fu)
                ctx.procedure(p, fu, 4207701, vid=fvid)
                ctx.measure(p, fu, 3028641, ctx.lab_value(3028641, shift=-3, lo=0.3), vid=fvid)
                if k % 2 == 0:
                    ctx.procedure(p, fu, 4179986, vid=fvid)
                if surgery_day is not None and stage != "IV" and not recurred and ctx.bern(rec_p):
                    recurred = True
                    if ctx.bern(0.25):
                        site_r = "Anastomotic site (local recurrence)"
                    else:
                        site_r = ctx.choice(MET_SITES, p=MET_P)
                    ctx.note(p, fu, f"CT abdomen and pelvis: new {site_r.lower()} lesion, suspicious for recurrence.",
                             note_type=44814637, note_class=36716164, vid=fvid)
                    s3 = ctx.days(fu, ctx.randint(10, 30))
                    n3 = _cap_cycles(ctx, s3, ctx.randint(6, 12), 14)
                    if ecog <= 2 and n3 > 0:
                        if had_oxali:
                            drugs3, reg = [1367268, 955632, 1397599], "FOLFIRI + Bevacizumab"
                        else:
                            drugs3, reg = [1320011, 955632, 1397599], "FOLFOX + Bevacizumab"
                        sid3, e3, cyc3 = ctx.sact(p, reg, drugs3, s3, n3, 3, ecog=ecog, response=ctx.choice(["PR", "SD", "PD"]), cycle_days=14)
                        ctx.sact_update(sid3, recurrence_anatomic_site=site_r if site_r in MET_SITES else None)
                        ctx.monitor(p, cyc3, drugs3, ae_pool=_pool(drugs3))
                        fu = e3
                        if ctx.bern(0.35):
                            _death(ctx, p, ctx.days(e3, ctx.randint(30, 240)))
                fu = ctx.days(fu, ctx.randint(170, 190)); k += 1
        ctx.finalize_person(p)

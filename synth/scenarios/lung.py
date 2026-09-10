# -*- coding: utf-8 -*-
"""
폐암 코호트 시나리오 (환자 여정 템플릿)

여정 개요
  1) 진단 방문(입원 3일): 흉부 CT, 기관지내시경 생검, PET-CT, 기본 혈액검사, 임상 병기, 유전자검사(EGFR/ALK/KRAS/PD-L1)
  2) 병기별 치료
     - I~II   : 폐엽절제술(입원 7일) + 외과병리(pTNM) + 일부 보조항암(cisplatin/pemetrexed 4주기)
     - III    : 동시항암방사선(주간 carboplatin/paclitaxel 6주 + 60 Gy/30 fx)
     - IV     : EGFR 양성 -> osimertinib 1차, 그 외 pembrolizumab + carboplatin/pemetrexed 4주기 후 유지
                진행 시 docetaxel 2차
  3) 항암 중 이상사례(CTCAE), 사이클마다 CBC/신장/간기능
  4) 추적 외래(3개월 간격, CT), 수술 환자 중 일부 재발(-> stage_iv_diagnosis_date), IV 환자 중 일부 사망
특화 테이블(LUNG_CANCER)은 이벤트 그룹 단위로 행을 만든다.
"""
from framework import *

LC = 4115276
HIST = {1: ("Adenocarcinoma", "8140/3"), 2: ("Squamous cell carcinoma", "8070/3"), 4: ("Small cell carcinoma", "8041/3"), 3: ("Large cell carcinoma", "8012/3")}
STAGES = ["IA", "IB", "IIA", "IIB", "IIIA", "IIIB", "IV"]
STAGE_P = [0.16, 0.10, 0.07, 0.07, 0.12, 0.08, 0.40]
TNM = {"IA": ("T1b", "N0", "M0"), "IB": ("T2a", "N0", "M0"), "IIA": ("T2b", "N0", "M0"), "IIB": ("T3", "N0", "M0"),
       "IIIA": ("T3", "N2", "M0"), "IIIB": ("T4", "N2", "M0"), "IV": ("T2a", "N2", "M1b")}
TSIZE = {"T1b": (1.1, 2.0), "T2a": (3.1, 4.0), "T2b": (4.1, 5.0), "T3": (5.1, 7.0), "T4": (7.1, 9.0)}
LOBE = [("RUL", "우상엽"), ("RML", "우중엽"), ("RLL", "우하엽"), ("LUL", "좌상엽"), ("LLL", "좌하엽")]
MET_SITES = [("C71", "Brain"), ("C41", "Bone"), ("C22", "Liver"), ("C74", "Adrenal gland"), ("C34", "Contralateral lung")]

CT_REPORT = ("Chest CT (contrast). {lobe} 에 {size} cm 크기의 spiculated mass. {node}. {met} "
             "Impression: Lung cancer, {lobe}, c{t}{n}{m}. Recommend tissue confirmation.")
PATH_REPORT = ("Lung, {lobe}, {method}: {hist}. Tumor size {size} cm. Differentiation: {diff}. "
               "Visceral pleural invasion: {vpi}. Lymph nodes: {ln}. Pathologic stage p{t}{n}{m}.")
MOL_REPORT = "Molecular pathology (NGS panel): EGFR {egfr}; ALK IHC {alk}; KRAS {kras}; PD-L1 TPS {pdl1}%."


def generate(ctx: Ctx, n=100):
    for _ in range(n):
        gender = FEMALE if ctx.bern(0.38) else MALE
        age = int(ctx.normal(67, 9, 35, 90, 0))
        index = D(2019, 1, 1) + dt.timedelta(days=ctx.randint(0, 365 * 5))
        p = ctx.person(gender, age, index)
        hist = ctx.choice([1, 2, 4, 3], p=[0.55, 0.25, 0.14, 0.06])
        stage = ctx.choice(STAGES, p=STAGE_P)
        if hist == 4 and stage in ("IA", "IB", "IIA"):
            stage = ctx.choice(["IIIB", "IV"])
        t, nn, m = TNM[stage]
        lobe_cd, lobe_nm = ctx.choice(LOBE)
        smoker = ctx.bern(0.75 if gender == MALE else 0.15)
        cur_smok = smoker and ctx.bern(0.5)
        egfr = (hist == 1) and ctx.bern(0.45 if gender == FEMALE else 0.3)
        p.patient_fields = dict(
            histologic_diagnosis=hist, histologic_diagnosis_source_value=HIST[hist][0], clinical_stage=stage,
            lucn_diag_kncd="C34.1" if "U" in lobe_cd else ("C34.2" if "M" in lobe_cd else "C34.3"),
            lucn_diag_knnm="폐의 악성 신생물", lung_tumr_prmr_loca_cd=lobe_cd, care_site_id=1,
            lung_tumr_size_vl=round(ctx.rand(*TSIZE[t]), 1))
        size = p.patient_fields["lung_tumr_size_vl"]

        # ---- 1) 진단 입원 (3일)
        dx_vid = ctx.visit(p, index, INPATIENT, los=3)
        ctx.condition(p, index, LC, vid=dx_vid)
        if hist == 4: ctx.condition(p, index, 258375, vid=dx_vid)
        else: ctx.condition(p, index, 4311499, vid=dx_vid)
        if smoker and ctx.bern(0.4): ctx.condition(p, index, 255573, vid=dx_vid)     # COPD
        if ctx.bern(0.35): ctx.condition(p, index, 320128, vid=dx_vid)               # HTN
        if ctx.bern(0.2): ctx.condition(p, index, 201826, vid=dx_vid)                # T2DM
        ct_day = index
        ctx.procedure(p, ct_day, 4059400, vid=dx_vid)                                 # chest CT
        bx_day = ctx.days(index, 1)
        ctx.procedure(p, bx_day, 4032404, vid=dx_vid)                                 # bronchoscopy biopsy
        pet_day = ctx.days(index, 2)
        ctx.procedure(p, pet_day, 4305790, vid=dx_vid)                                # PET
        base_labs = ctx.labs(p, index, [3000963, 3010813, 3017732, 3024929, 3016723, 3013721, 3006923, 3020491, 3022250], vid=dx_vid)
        ht = ctx.normal(170 if gender == MALE else 157, 6, 145, 190); wt = ctx.normal(66 if gender == MALE else 56, 9, 38, 110)
        bmi = round(wt / (ht / 100) ** 2, 1)
        ctx.measure(p, index, 3036277, ht, vid=dx_vid); ctx.measure(p, index, 3025315, wt, vid=dx_vid); ctx.measure(p, index, 3038553, bmi, vid=dx_vid)
        ecog = ctx.choice([0, 1, 2, 3], p=[0.3, 0.45, 0.2, 0.05])
        ctx.observation(p, index, 4257895, vid=dx_vid, value_number=ecog, value_string=f"ECOG {ecog}")      # ECOG performance status
        ctx.observation(p, index, 4275495, vid=dx_vid, value_string="Current smoker" if cur_smok else ("Ex-smoker" if smoker else "Never smoker"))
        met_cd, met_nm = (ctx.choice(MET_SITES) if stage == "IV" else (None, None))
        node_txt = "Mediastinal lymphadenopathy" if nn != "N0" else "No significant lymphadenopathy"
        met_txt = f"Metastasis to {met_nm}." if met_nm else "No distant metastasis."
        ctx.note(p, ct_day, CT_REPORT.format(lobe=lobe_nm, size=size, node=node_txt, met=met_txt, t=t, n=nn, m=m), vid=dx_vid)
        diff = ctx.choice(["well", "moderately", "poorly"])
        ctx.note(p, ctx.days(bx_day, 2) if ctx.days(bx_day, 2) <= ctx.days(index, 3) else bx_day, PATH_REPORT.format(
            lobe=lobe_nm, method="bronchoscopic biopsy", hist=HIST[hist][0], size=size, diff=diff, vpi="not assessable",
            ln="not assessable", t=t, n=nn, m=m), note_type=44814640, note_class=36716165, vid=dx_vid)
        # 특화 테이블: 진단 시 그룹들
        ctx.disease_row(p, dx_vid, rcrd_ymd=index, cur_smok_yn_noans_spcd="Y" if cur_smok else "N", cur_smok_yn_noans_spnm="예" if cur_smok else "아니오",
                        shis_yn_noans_spcd="Y" if smoker else "N", shis_yn_noans_spnm="예" if smoker else "아니오",
                        smok_qty=round(ctx.rand(0.5, 2.0), 1) if smoker else None, smok_dtrn_ycnt=ctx.randint(10, 50) if smoker else None,
                        nsmk_strt_yr=(index.year - ctx.randint(1, 15)) if (smoker and not cur_smok) else None,
                        mhis_tb_yn_noans_spcd="Y" if ctx.bern(0.1) else "N", mhis_cncr_yn_noans_spcd="N", ecog_cd=str(ecog), ecog_nm=f"ECOG {ecog}",
                        mhis_yn_noans_spcd="Y")
        ctx.disease_row(p, dx_vid, anth_rcrd_ymd=index, ht_msrm_vl=ht, wt_msrm_vl=wt, bmi_vl=bmi)
        ctx.disease_row(p, dx_vid, diag_rgst_ymd=index, diag_cd="LC" + str(hist), diag_nm=HIST[hist][0], diag_kcd_cd=p.patient_fields["lucn_diag_kncd"],
                        diag_kcd_nm="폐의 악성 신생물", diag_smct_cd="254637007", diag_smct_nm="Non-small cell lung cancer" if hist != 4 else "Small cell carcinoma of lung")
        ctx.disease_row(p, dx_vid, imex_ymd=ct_day, imex_kncd="CT-CHEST-C", imex_knnm="Chest CT with contrast", imex_smct_cd="169069000", imex_smct_nm="CT of chest")
        ctx.disease_row(p, dx_vid, imex_ymd=pet_day, imex_kncd="PET-WB", imex_knnm="Whole body PET-CT", imex_smct_cd="443271005", imex_smct_nm="PET-CT")
        ctx.disease_row(p, dx_vid, bpsy_ymd=bx_day, bpsy_spcd="LUNG", bpsy_spnm="폐", bpsy_cd=lobe_cd, bpsy_nm=lobe_nm, bpsy_mthd_kncd="BRONCH", bpsy_mthd_knnm="기관지내시경 생검",
                        bpsy_lung_site_dtlc_cd=lobe_cd, bpsy_lung_site_dtlc_nm=lobe_nm, htlg_diag_cd=HIST[hist][1], htlg_diag_nm=HIST[hist][0],
                        htlg_dfgd_cd={"well": "G1", "moderately": "G2", "poorly": "G3"}[diff], htlg_dfgd_nm=f"{diff} differentiated")
        ctx.disease_row(p, dx_vid, diag_stag_rcrd_ymd=pet_day, clnc_tnm_stag_vl=f"{t}{nn}{m}", clnc_t_stag_vl=t, clnc_n_stag_vl=nn, clnc_m_stag_vl=m,
                        clnc_tumr_prty_cd="SPIC", clnc_tumr_prty_nm="Spiculated mass")
        ctx.disease_row(p, dx_vid, cexm_ymd=index, cexm_kncd="L3011", cexm_knnm="CBC", cexm_loinc_cd="58410-2", cexm_loinc_nm="CBC panel",
                        cexm_rslt_cont=f"Hb {base_labs[3000963]} g/dL, WBC {base_labs[3010813]}", cexm_rslt_unit_cont="g/dL")
        if met_cd:
            ctx.disease_row(p, dx_vid, mtdg_ymd=pet_day, mtst_site_cd=met_cd, mtst_site_nm=met_nm)
            p.patient_fields["otog_mtst_site_cd"] = met_cd; p.patient_fields["otog_mtst_site_nm"] = met_nm
        for r in ctx.rows["LUNG_CANCER"]:
            if r["person_id"] == p.person_id and met_cd:
                r.setdefault("otog_mtst_site_cd", met_cd); r.setdefault("otog_mtst_site_nm", met_nm)
        # 유전자검사 (비소세포)
        pdl1 = None
        if hist != 4:
            gmt_day = ctx.days(index, ctx.randint(5, 12))
            gvid = ctx.visit_on(p, gmt_day)
            pdl1 = ctx.choice([0, 1, 5, 25, 50, 80])
            alk = ctx.bern(0.04) and not egfr
            kras = (not egfr and not alk) and ctx.bern(0.2)
            ctx.note(p, gmt_day, MOL_REPORT.format(egfr="exon 19 deletion" if egfr else "wild type", alk="positive" if alk else "negative",
                                                    kras="G12C" if kras else "wild type", pdl1=pdl1), note_type=44814640, note_class=36716165, vid=gvid)
            for gene, res in (("EGFR", "exon19del" if egfr else "WT"), ("ALK", "POS" if alk else "NEG"), ("KRAS", "G12C" if kras else "WT")):
                ctx.disease_row(p, gvid, gmt_ymd=gmt_day, gmt_mtcd="NGS", gmt_mtnm="Next generation sequencing", gmt_gene_kncd=gene, gmt_gene_knnm=f"{gene} ({res})")
            ctx.disease_row(p, gvid, imem_ymd=gmt_day, imem_kncd="PDL1-22C3", imem_knnm="PD-L1 IHC 22C3", imem_opn_cd="TPS", imem_opn_nm="Tumor proportion score",
                            imem_rslt_vl=pdl1, imem_rslt_unit_cd="%", imem_rslt_unit_nm="percent")
        # 폐기능검사 (수술 대상)
        cur = ctx.days(index, 3)
        if stage in ("IA", "IB", "IIA", "IIB", "IIIA"):
            pft_day = ctx.days(index, ctx.randint(7, 14))
            pv = ctx.visit_on(p, pft_day)
            fev1 = ctx.normal(85, 15, 35, 130)
            ctx.disease_row(p, pv, plex_ymd=pft_day, plex_spcd="PFT", plex_spnm="폐기능검사", plex_kncd="FEV1", plex_knnm="FEV1 (% predicted)", plex_rslt_vl=fev1)
            ctx.disease_row(p, pv, plex_ymd=pft_day, plex_spcd="PFT", plex_spnm="폐기능검사", plex_kncd="DLCO", plex_knnm="DLCO (% predicted)", plex_rslt_vl=ctx.normal(80, 15, 30, 130))

        # ---- 2) 치료
        last_ctx_date = cur
        surgery_day = None
        antp_ids = []
        if stage in ("IA", "IB", "IIA", "IIB", "IIIA") and ecog <= 2:
            surgery_day = ctx.days(index, ctx.randint(21, 45))
            svid = ctx.visit(p, surgery_day, INPATIENT, los=7)
            ctx.procedure(p, surgery_day, 4033181, vid=svid)
            path_day = ctx.days(surgery_day, ctx.randint(3, 7))
            pt = t if ctx.bern(0.8) else ctx.choice(list(TSIZE))
            psize = round(ctx.rand(*TSIZE[pt]), 1)
            pn = nn if ctx.bern(0.75) else ctx.choice(["N0", "N1", "N2"])
            tot_ln = ctx.randint(8, 30); pos_ln = 0 if pn == "N0" else ctx.randint(1, min(6, tot_ln))
            ctx.note(p, path_day, PATH_REPORT.format(lobe=lobe_nm, method="lobectomy", hist=HIST[hist][0], size=psize, diff=diff,
                                                      vpi="present" if ctx.bern(0.3) else "absent", ln=f"{pos_ln}/{tot_ln} positive", t=pt, n=pn, m="M0"),
                     note_type=44814640, note_class=36716165, vid=svid)
            ctx.disease_row(p, svid, oprt_ymd=surgery_day, oprt_kncd="O1421", oprt_knnm="폐엽절제술", oprt_prps_cd="CUR", oprt_prps_nm="근치적", oprt_site_cd=lobe_cd, oprt_site_nm=lobe_nm,
                            oprt_mtcd="VATS" if ctx.bern(0.7) else "OPEN", oprt_mtnm="흉강경 폐엽절제술" if ctx.bern(0.7) else "개흉 폐엽절제술", opls_detl_loca_cd=lobe_cd, dsch_ymd=ctx.days(surgery_day, 7))
            ctx.disease_row(p, svid, srgc_ptem_ymd=path_day, sgpt_hvst_site_cd=lobe_cd, sgpt_hvst_site_nm=lobe_nm, srgc_ptem_rslt_tumr_cnt=1,
                            tumr_wdth_lnth_vl=psize, tumr_lgtd_lnth_vl=round(psize * ctx.rand(0.6, 1.0), 1), tumr_hght_vl=round(psize * ctx.rand(0.5, 0.9), 1),
                            tumr_max_diam_vl=psize, afop_path_tnm_stag_vl=f"{pt}{pn}M0", afop_path_t_stag_vl=pt, afop_path_n_stag_vl=pn, afop_path_m_stag_vl="M0",
                            htlg_diag_cd_po=HIST[hist][1], htlg_diag_nm_po=HIST[hist][0])
            ctx.labs(p, ctx.days(surgery_day, 1), [3000963, 3010813, 3016723], vid=svid)
            last_ctx_date = ctx.days(surgery_day, 7)
            if ctx.bern(0.2):
                ctx.ae(p, ctx.days(surgery_day, 2), 437663, 1, vid=svid)   # postoperative fever
            # 보조항암
            if stage in ("IB", "IIA", "IIB", "IIIA") and ctx.bern(0.7):
                s = ctx.days(surgery_day, ctx.randint(35, 60))
                aid, e, cyc = ctx.antp(p, 1, "Cisplatin + Pemetrexed", [1397141, 1304919], s, 4, 2, 1, ecog=ecog, response="NE")
                antp_ids.append(aid); last_ctx_date = e
                _chemo_monitoring(ctx, p, cyc, aid, [1397141, 1304919])
                ctx.antp_update(aid, treatment_outcome=0)
        elif stage in ("IIIA", "IIIB") or (stage in ("IA", "IB", "IIA", "IIB") and ecog > 2):
            s = ctx.days(index, ctx.randint(14, 30))
            aid, e, cyc = ctx.antp(p, 1, "Weekly Carboplatin + Paclitaxel (CCRT)", [1344905, 1378382], s, 6, 5, 1, ecog=ecog, response=ctx.choice(["PR", "SD", "CR"]), cycle_days=7)
            antp_ids.append(aid); last_ctx_date = e
            _chemo_monitoring(ctx, p, cyc, aid, [1344905, 1378382])
            fx = 30; rvid = ctx.visit_on(p, s)
            ctx.procedure(p, s, 4181206, vid=rvid)
            ctx.disease_row(p, rvid, rdt_prsc_ymd=s, rdt_kncd="RT-3D", rdt_knnm="3D 입체조형 방사선치료", rdt_prps_cd="DEF", rdt_prps_nm="근치적", rdt_site_cd="LUNG", rdt_site_nm="폐/종격동",
                            rd_gy=2.0, rd_impl_nt=fx, rd_totl_gy=60.0)
            if hist != 4 and ctx.bern(0.6):
                s2 = ctx.days(e, 30)
                aid2, e2, cyc2 = ctx.antp(p, 2, "Durvalumab consolidation (pembrolizumab as proxy)", [45775965], s2, 6, 4, 5, ecog=ecog, response="SD", cycle_days=28)
                antp_ids.append(aid2); last_ctx_date = e2
                _chemo_monitoring(ctx, p, cyc2, aid2, [45775965], ae_p=0.25)
        else:  # IV 또는 소세포
            s = ctx.days(index, ctx.randint(10, 25))
            if hist == 4:
                aid, e, cyc = ctx.antp(p, 1, "Etoposide + Cisplatin", [1350504, 1397141], s, 4, 3, 1, ecog=ecog, response=ctx.choice(["PR", "CR", "SD", "PD"]), inpatient_first=True)
                drugs = [1350504, 1397141]
            elif egfr:
                aid, e, cyc = ctx.antp(p, 1, "Osimertinib", [35604205], s, ctx.randint(6, 30), 3, 2, ecog=ecog, response=ctx.choice(["PR", "SD", "CR"], p=[0.7, 0.2, 0.1]), cycle_days=28, oral=True)
                drugs = [35604205]
            else:
                aid, e, cyc = ctx.antp(p, 1, "Pembrolizumab + Carboplatin + Pemetrexed", [45775965, 1344905, 1304919], s, 4, 3, 5, ecog=ecog, response=ctx.choice(["PR", "SD", "PD"], p=[0.5, 0.35, 0.15]), inpatient_first=True)
                drugs = [45775965, 1344905, 1304919]
            antp_ids.append(aid); last_ctx_date = e
            _chemo_monitoring(ctx, p, cyc, aid, drugs)
            # 진행 및 2차
            if ctx.bern(0.55):
                pd_day = ctx.days(e, ctx.randint(20, 120))
                pvid = ctx.visit_on(p, pd_day)
                ctx.procedure(p, pd_day, 4059400, vid=pvid)
                ctx.note(p, pd_day, f"Chest CT: interval increase of {lobe_nm} mass and new nodules. Progressive disease.", vid=pvid)
                site = ctx.choice(["Lung", "Liver", "Bone", "Brain"])
                ctx.antp_update(aid, treatment_outcome=0, days_to_progression=pd_day, progression_or_recurrence_anatomic_site=site)
                ctx.disease_row(p, pvid, imex_ymd=pd_day, imex_kncd="CT-CHEST-C", imex_knnm="Chest CT with contrast", imex_smct_cd="169069000", imex_smct_nm="CT of chest")
                last_ctx_date = pd_day
                if ecog <= 2 and ctx.bern(0.7):
                    s2 = ctx.days(pd_day, ctx.randint(7, 21))
                    aid2, e2, cyc2 = ctx.antp(p, 2, "Docetaxel", [1315942], s2, ctx.randint(2, 6), 3, 1, ecog=min(ecog + 1, 3), response=ctx.choice(["SD", "PD", "PR"]))
                    antp_ids.append(aid2); last_ctx_date = e2
                    _chemo_monitoring(ctx, p, cyc2, aid2, [1315942])
                    ctx.antp_update(aid2, treatment_outcome=0)
                if ctx.bern(0.5):
                    dd = ctx.days(last_ctx_date, ctx.randint(15, 180))
                    ctx.set_death(p, dd)
                    ctx.visit(p, ctx.days(dd, -2), INPATIENT, los=2)
                    ctx.disease_row(p, ctx.visit_on(p, dd), death_date=dd)
                    for r in ctx.rows["LUNG_CANCER"]:
                        if r["person_id"] == p.person_id: r["death_date"] = dd
                    p.patient_fields["death_date"] = dd
            else:
                ctx.antp_update(aid, treatment_outcome=1 if e >= ctx.days(ctx.today, -60) else 0)
        # stage IV 진단일
        if stage == "IV":
            p.patient_fields["stage_iv_diagnosis_date"] = pet_day
            for r in ctx.rows["LUNG_CANCER"]:
                if r["person_id"] == p.person_id: r["stage_iv_diagnosis_date"] = pet_day

        # ---- 3) 추적 및 재발
        if p.death_date is None:
            fu = ctx.days(last_ctx_date, 90)
            recurred = False
            k = 0
            while fu <= ctx.today and k < 8:
                fvid = ctx.visit_on(p, fu)
                ctx.procedure(p, fu, 4059400, vid=fvid)
                ctx.labs(p, fu, [3000963, 3028641], vid=fvid)
                ctx.disease_row(p, fvid, imex_ymd=fu, imex_kncd="CT-CHEST-C", imex_knnm="Chest CT with contrast", imex_smct_cd="169069000", imex_smct_nm="CT of chest")
                if surgery_day and not recurred and ctx.bern(0.08):
                    recurred = True
                    site_cd, site_nm = ctx.choice(MET_SITES)
                    ctx.note(p, fu, f"Chest CT: new {site_nm} lesion suspicious for recurrence.", vid=fvid)
                    ctx.disease_row(p, fvid, rldg_ymd=fu, rlps_site_cd=site_cd, rlps_site_nm=site_nm)
                    ctx.disease_row(p, fvid, mtdg_ymd=fu, mtst_site_cd=site_cd, mtst_site_nm=site_nm)
                    p.patient_fields["stage_iv_diagnosis_date"] = fu
                    for r in ctx.rows["LUNG_CANCER"]:
                        if r["person_id"] == p.person_id: r["stage_iv_diagnosis_date"] = fu
                    if ctx.has_antp and ecog <= 2:
                        s3 = ctx.days(fu, ctx.randint(10, 30))
                        line = len(antp_ids) + 1
                        aid3, e3, cyc3 = ctx.antp(p, line, "Pembrolizumab + Carboplatin + Pemetrexed", [45775965, 1344905, 1304919], s3, 4, 3, 5, ecog=ecog, response="PR")
                        antp_ids.append(aid3)
                        _chemo_monitoring(ctx, p, cyc3, aid3, [45775965, 1344905, 1304919])
                        ctx.antp_update(aid3, treatment_outcome=1 if e3 >= ctx.days(ctx.today, -60) else 0)
                        fu = e3
                fu = ctx.days(fu, ctx.randint(80, 100)); k += 1
        ctx.finalize_person(p)


def _chemo_monitoring(ctx, p, cycle_dates, aid, drugs, ae_p=0.45):
    """사이클마다 CBC/신장/간기능, 일부 사이클에 이상사례."""
    for i, d in enumerate(cycle_dates):
        vid = ctx.visit_on(p, d)
        shifts = {3017732: -1.5 if i > 0 else 0, 3000963: -1.0 if i > 0 else 0}
        ctx.labs(p, d, [3000963, 3010813, 3017732, 3024929, 3016723, 3013721, 3006923], vid=vid, shifts=shifts)
        if i > 0 and ctx.bern(ae_p):
            ae_day = ctx.days(d, ctx.randint(3, 12))
            if p.death_date is not None and ae_day > p.death_date:
                continue
            concept = ctx.choice([27674, 301794, 439777, 4223659, 196523, 4166735, 140214, 4304213], p=[0.2, 0.2, 0.15, 0.15, 0.1, 0.1, 0.05, 0.05])
            lo, hi = CONCEPTS["adverse_events"][concept]["typical_grade"]
            grade = ctx.randint(lo, hi)
            avid = ctx.visit(p, ae_day, ER if grade >= 3 else OUTPATIENT)
            ctx.ae(p, ae_day, concept, grade, antp_id=aid, vid=avid, action=2 if grade >= 3 else 1)
            ctx.condition(p, ae_day, concept, vid=avid)
            if concept in (301794, 4304213):
                ctx.drug(p, ae_day, 1301125, 3, vid=avid, freq=1)

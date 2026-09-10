# -*- coding: utf-8 -*-
"""
대장암 코호트 시나리오 (환자 여정 템플릿)

여정 개요
  1) 진단 외래: 대장내시경 생검(bpsy, 판독일), 복부골반 CT(imex), 직장암은 골반 MRI(imex: 직장간막근막 거리, EMVI, 항문연 거리 등),
     CEA/기본 혈액검사(cexm), 임상 병기(stag, cTNM), 병력(hist), 가족력(fmht, 유전성 대장암), 신체계측(anth), 주증상(cc),
     면역조직화학 MMR(imem, 판독일), 분자병리 KRAS/NRAS/BRAF/MSI(mlem, 판독일), 진단(diag)
  2) 병기별 치료
     - 결장 I~III      : 결장절제술(복강경, 일부 개복전환) + 외과병리(pTNM) + III기(및 고위험 II기) 보조 FOLFOX/CAPOX
     - 직장 I           : 저위전방절제술
     - 직장 II~III      : 수술 전 동시항암방사선(50.4 Gy/28 fx + capecitabine) -> 재병기 MRI -> LAR/APR(장루) -> 외과병리 -> 보조항암
     - IV(약 20%)       : 일부 폐색 시 고식적 절제, FOLFOX + bevacizumab 1차, 진행 시 FOLFIRI + bevacizumab 2차, 일부 사망
  3) 항암 중 사이클별 CBC/신장/간기능, CTCAE 이상사례(oxaliplatin -> 말초신경병증 다수), 중증은 응급실 방문
  4) 장루 복원(ostm_reop, 3~9개월), 6개월 간격 추적(CT + CEA), 일부 재발(rlps + mtst) -> 고식적 항암, 일부 사망
특화 테이블(COLORECTAL_CANCER)은 이벤트 그룹 단위로 행을 만든다.
"""
from framework import *

COLON, RECTOSIG, RECTUM = 4180790, 443381, 4164337
SITES = [  # (kcd, kor name, site code, site name, cohort concept, side)
    ("C18.0", "맹장의 악성 신생물", "CEC", "Cecum", COLON, "R"),
    ("C18.2", "상행결장의 악성 신생물", "ASC", "Ascending colon", COLON, "R"),
    ("C18.4", "횡행결장의 악성 신생물", "TRA", "Transverse colon", COLON, "R"),
    ("C18.6", "하행결장의 악성 신생물", "DES", "Descending colon", COLON, "L"),
    ("C18.7", "구불결장의 악성 신생물", "SIG", "Sigmoid colon", COLON, "L"),
    ("C19", "직장구불결장이행부의 악성 신생물", "RSJ", "Rectosigmoid junction", RECTOSIG, "L"),
    ("C20", "직장의 악성 신생물", "REC", "Rectum", RECTUM, "L"),
]
SITE_P = [0.08, 0.17, 0.08, 0.07, 0.25, 0.05, 0.30]
STAGES = ["I", "II", "III", "IV"]
STAGE_P = [0.20, 0.25, 0.33, 0.22]
TSIZE = {"T1": (0.8, 2.0), "T2": (2.0, 4.0), "T3": (3.0, 6.0), "T4a": (4.5, 8.0), "T4b": (5.0, 9.0)}
HIST = {"8140/3": "Adenocarcinoma, NOS", "8480/3": "Mucinous adenocarcinoma", "8490/3": "Signet ring cell carcinoma"}
GRADE = {"G1": "Well differentiated", "G2": "Moderately differentiated", "G3": "Poorly differentiated"}
DEPTH = {"T1": ("SM", "Submucosa"), "T2": ("MP", "Muscularis propria"), "T3": ("SS", "Subserosa / perirectal fat"),
         "T4a": ("SE", "Serosa (visceral peritoneum)"), "T4b": ("AO", "Adjacent organ")}
GROSS = [("UF", "Ulcerofungating"), ("UI", "Ulceroinfiltrative"), ("PL", "Polypoid"), ("IF", "Infiltrative")]
MET_SITES = [("C22", "Liver"), ("C34", "Lung"), ("C48", "Peritoneum"), ("C77", "Distant lymph node"), ("C41", "Bone")]
MET_P = [0.5, 0.2, 0.15, 0.1, 0.05]
DRUG_META = {  # concept: (ATC, RxNorm code, route)
    1320011: ("L01XA03", "32592", "IV"), 955632: ("L01BC02", "4492", "IV"), 1337620: ("L01BC06", "194000", "PO"),
    1367268: ("L01CE02", "51499", "IV"), 1397599: ("L01FG01", "253337", "IV"),
}
CC_TEXT = {"R": ["Iron deficiency anemia found on health check-up", "Vague right lower quadrant abdominal pain for 3 months", "Weight loss 5 kg over 2 months and fatigue"],
           "L": ["Hematochezia for 2 months", "Change of bowel habit (constipation) for 3 months", "Abdominal distension and decreased stool caliber"],
           "REC": ["Hematochezia and tenesmus for 2 months", "Blood-tinged stool with mucus for 6 weeks", "Anal pain and frequent defecation for 1 month"],
           "SCR": ["Asymptomatic, screening colonoscopy positive", "Positive fecal immunochemical test, asymptomatic"]}

COLONO_REPORT = ("Colonoscopy: {desc} mass at {site}, {size} cm in size, occupying about {circ}% of the lumen{obst}. "
                 "Multiple biopsies taken. Impression: {site} cancer, r/o adenocarcinoma. Biopsy pending.")
BX_REPORT = "Colon, {site}, endoscopic biopsy: {hist}, {grade}. Tumor budding: {bud}."
CT_REPORT = ("CT abdomen and pelvis (contrast). {desc} wall thickening of the {site} ({size} cm) with {node}. {met} "
             "Impression: {site} cancer, c{t}{n}{m}.")
MRI_REPORT = ("Rectal MRI. Tumor lower margin {anvg} cm from anal verge ({anju} cm from anorectal junction), located {circ}. "
              "mrT{t}, mrN{n}. Shortest distance to mesorectal fascia {mrf} mm. EMVI {emvi}. Mesorectal LN {mln}. Extramesorectal LN {eln}.")
MRI_RESTAGE = "Rectal MRI after CCRT. Interval decrease of tumor. mrTRG {trg}. Residual tumor {res} cm from anal verge. MRF {mrf}."
SGPT_REPORT = ("{organ}, {op}: {hist}, {grade}. Tumor size {size} cm, gross type {gross}. Depth of invasion: {depth}. "
               "Lymphatic invasion {lvi}, venous invasion {vi}, perineural invasion {pni}. Radial margin {rm}. "
               "Lymph nodes: {pos}/{tot} positive. {tme}Pathologic stage {tnm}.")
IHC_REPORT = "Immunohistochemistry (MMR proteins): MLH1 {mlh1}, MSH2 {msh2}, MSH6 {msh6}, PMS2 {pms2}. Interpretation: {mmr}."
MOL_REPORT = "Molecular pathology: KRAS {kras}; NRAS {nras}; BRAF {braf}; MSI (PCR) {msi}."


def generate(ctx: Ctx, n=100):
    for _ in range(n):
        gender = FEMALE if ctx.bern(0.42) else MALE
        age = int(ctx.normal(65, 10, 30, 90, 0))
        index = D(2019, 1, 1) + dt.timedelta(days=ctx.randint(0, 365 * 5 + 150))
        p = ctx.person(gender, age, index)
        kcd, knnm, site_cd, site_nm, dx_concept, side = ctx.choice(SITES, p=SITE_P)
        rectal = kcd == "C20"
        stage = ctx.choice(STAGES, p=STAGE_P)
        t, nn, m = _ctnm(ctx, stage, rectal)
        size = round(ctx.rand(*TSIZE[t]), 1)
        hist_cd = ctx.choice(list(HIST), p=[0.85, 0.12, 0.03])
        grade = ctx.choice(list(GRADE), p=[0.15, 0.7, 0.15])
        ecog = ctx.choice([0, 1, 2, 3], p=[0.4, 0.4, 0.15, 0.05])
        obstruction = ctx.bern(0.10) if t in ("T3", "T4a", "T4b") else False
        perforation = (not obstruction) and t in ("T4a", "T4b") and ctx.bern(0.1)
        p.patient_fields = dict(clcn_diag_kncd=kcd, clcn_diag_knnm=knnm, care_site_id=1,
                                bwpf_yn_unid_spcd="Y" if perforation else "N", bwpf_yn_unid_spnm="예" if perforation else "아니오",
                                inob_yn_unid_spcd="Y" if obstruction else "N", inob_yn_unid_spnm="예" if obstruction else "아니오",
                                dsch_ymd=index)

        # ---- 1) 진단: 대장내시경 생검 (외래)
        dx_vid = ctx.visit(p, index, OUTPATIENT)
        ctx.condition(p, index, dx_concept, vid=dx_vid)
        htn = ctx.bern(0.35); dm = ctx.bern(0.2); hl = ctx.bern(0.15); uc = ctx.bern(0.02)
        if htn: ctx.condition(p, index, 320128, vid=dx_vid)
        if dm: ctx.condition(p, index, 201826, vid=dx_vid)
        if hl: ctx.condition(p, index, 432867, vid=dx_vid)
        if uc: ctx.condition(p, index, 81893, vid=dx_vid)
        ctx.procedure(p, index, 4179986, vid=dx_vid)
        circ = ctx.randint(25, 95) if t != "T1" else ctx.randint(10, 30)
        cc_pool = CC_TEXT["REC"] if rectal else CC_TEXT[side]
        cc_txt = ctx.choice(CC_TEXT["SCR"]) if (stage == "I" and ctx.bern(0.6)) else ctx.choice(cc_pool)
        ctx.note(p, index, COLONO_REPORT.format(desc=ctx.choice(["Ulcerofungating", "Ulceroinfiltrative", "Polypoid"]), site=site_nm, size=size, circ=circ,
                                                 obst=", scope could not pass the lesion" if obstruction else ""), note_type=32831, note_class=36716177, vid=dx_vid)
        bx_read = ctx.days(index, ctx.randint(2, 4))
        bud = ctx.choice(["low", "intermediate", "high"])
        _report(ctx, p, bx_read, BX_REPORT.format(site=site_nm, hist=HIST[hist_cd], grade=GRADE[grade].lower(), bud=bud), 44814640, 36716165)
        ctx.disease_row(p, dx_vid, bpsy_ymd=index, bpsy_read_ymd=bx_read, bpsy_site_cd=site_cd, bpsy_site_nm=site_nm,
                        bpsy_cotm_dtlc_spcd=None if rectal else site_cd, bpsy_cotm_dtlc_spnm=None if rectal else site_nm,
                        bpsy_rctm_dtl_site_cont=(f"{ctx.choice(['Lower', 'Mid', 'Upper'])} rectum" if rectal else None),
                        bpsy_mthd_kncd="COLONO-BX", bpsy_mthd_knnm="대장내시경 생검", htlg_diag_cd=hist_cd, htlg_diag_nm=HIST[hist_cd],
                        bpsy_rslt_cont=f"{HIST[hist_cd]}, {GRADE[grade].lower()}")
        ctx.disease_row(p, dx_vid, cc_rcrd_ymd=index, cc_cont=cc_txt, cc_src_spcd="OPD")
        # 병력 / 가족력 / 신체계측 / 진단
        prev_ca = ctx.bern(0.06); abd_surg = ctx.bern(0.15); polyp = ctx.bern(0.2)
        ctx.disease_row(p, dx_vid, rcrd_ymd=index, mhis_yn_noans_spcd="Y" if (htn or dm or hl or uc or prev_ca or abd_surg or polyp) else "N",
                        mhis_yn_noans_spnm="예" if (htn or dm or hl or uc or prev_ca or abd_surg or polyp) else "아니오",
                        mhis_htn_yn_noans_spcd=_yn(htn), mhis_htn_yn_noans_spnm=_ynm(htn), mhis_dbt_yn_noans_spcd=_yn(dm), mhis_dbt_yn_noans_spnm=_ynm(dm),
                        mhis_lvds_yn_noans_spcd="N", mhis_lvds_yn_noans_spnm="아니오", mhis_tb_yn_noans_spcd=_yn(ctx.bern(0.05)), mhis_tb_yn_noans_spnm=None,
                        mhis_ht_diss_yn_noans_spcd=_yn(ctx.bern(0.05)), mhis_cncr_yn_noans_spcd=_yn(prev_ca), mhis_cncr_yn_noans_spnm=_ynm(prev_ca),
                        mhis_cncr_kncd="C16" if prev_ca else None, mhis_cncr_knnm="Stomach cancer" if prev_ca else None,
                        mhis_clrc_diss_spcd="U" if uc else ("P" if polyp else "N"), mhis_clrc_diss_spnm="궤양성 대장염" if uc else ("대장 용종" if polyp else "없음"),
                        mhis_absg_yn_noans_spcd=_yn(abd_surg), mhis_absg_yn_noans_spnm=_ynm(abd_surg), mhis_absg_cont=ctx.choice(["Appendectomy", "Cholecystectomy", "Cesarean section" if gender == FEMALE else "Herniorrhaphy"]) if abd_surg else None,
                        etc_mhis_yn_noans_spcd=_yn(hl), etc_mhis_yn_noans_spnm=_ynm(hl), etc_mhis_diss_cont="Hyperlipidemia" if hl else None,
                        ohad_hstr_yn_noans_spcd=_yn(ctx.bern(0.4)), ohad_hstr_yn_noans_spnm=None, dsch_stcd="1", dsch_stnm="호전", ecog_cd=str(ecog), ecog_nm=f"ECOG {ecog}")
        fam = ctx.bern(0.25); fam_crc = fam and ctx.bern(0.5); hered = fam_crc and ctx.bern(0.15)
        ctx.disease_row(p, dx_vid, fmht_rcrd_ymd=index, fmht_yn_noans_spcd=_yn(fam), fmht_yn_noans_spnm=_ynm(fam),
                        pt_fm_rlcd=ctx.choice(["F", "M", "S"]) if fam else None, pt_fm_rlnm=None,
                        fmhs_cncr_yn_noans_spcd=_yn(fam), fmhs_cncr_yn_noans_spnm=_ynm(fam),
                        fmht_cncr_kncd=("C18" if fam_crc else ctx.choice(["C16", "C22", "C50"])) if fam else None,
                        fmht_cncr_knnm=("Colorectal cancer" if fam_crc else "Other cancer") if fam else None,
                        fmhs_etc_yn_noans_spcd="N", fmhs_etc_yn_noans_spnm="아니오",
                        fmht_here_clcn_spcd=_yn(hered), fmht_here_clcn_spnm="예" if hered else "아니오",
                        fmht_here_clcn_clsf_etc_cont="Lynch syndrome (suspected, Amsterdam II criteria)" if hered else None)
        ht = ctx.normal(168 if gender == MALE else 156, 6, 145, 190); wt = ctx.normal(67 if gender == MALE else 57, 9, 38, 110)
        bmi = round(wt / (ht / 100) ** 2, 1)
        ctx.measure(p, index, 3036277, ht, vid=dx_vid); ctx.measure(p, index, 3025315, wt, vid=dx_vid); ctx.measure(p, index, 3038553, bmi, vid=dx_vid)
        ctx.observation(p, index, 4257895, vid=dx_vid, value_number=ecog, value_string=f"ECOG {ecog}")
        ctx.disease_row(p, dx_vid, anth_rcrd_ymd=index, ht_msrm_vl=ht, wt_msrm_vl=wt, bmi_vl=bmi)
        smct = ("363351006", "Malignant tumor of rectum") if rectal else (("363414004", "Malignant tumor of rectosigmoid junction") if kcd == "C19" else ("363406005", "Malignant tumor of colon"))
        ctx.disease_row(p, dx_vid, diag_rgst_ymd=index, diag_cd="CRC-" + site_cd, diag_nm=f"{site_nm} cancer", diag_kcd_cd=kcd, diag_kcd_nm=knnm,
                        diag_smct_cd=smct[0], diag_smct_nm=smct[1])

        # ---- 병기 결정 검사 (CT / MRI / CEA)
        ct_day = ctx.days(index, ctx.randint(3, 8))
        wvid = ctx.visit(p, ct_day, OUTPATIENT)
        ctx.procedure(p, ct_day, 4207701, vid=wvid)
        met_cd, met_nm = (ctx.choice(MET_SITES, p=MET_P) if stage == "IV" else (None, None))
        node_txt = "enlarged regional lymph nodes" if nn != "N0" else "no significant regional lymphadenopathy"
        met_txt = f"Multiple metastatic nodules in the {met_nm.lower()}." if met_nm else "No distant metastasis."
        _report(ctx, p, ct_day, CT_REPORT.format(desc="Circumferential" if circ > 60 else "Eccentric", site=site_nm.lower(), size=size, node=node_txt, met=met_txt, t=t[1:], n=nn[1:], m=m[1:]), 44814637, 36716164, vid=wvid)
        ctx.disease_row(p, wvid, imex_ymd=ct_day, imex_kncd="CT-AP-C", imex_knnm="Abdomen and pelvis CT with contrast", imex_smct_cd="418891003", imex_smct_nm="CT of abdomen and pelvis with contrast",
                        imex_rslt_cont=f"{site_nm} cancer, c{t}{nn}{m}. {met_txt}")
        mri = None
        if rectal or kcd == "C19":
            mri = _rectal_mri(ctx, p, ct_day, wvid, t, nn, rectal)
        base_labs = ctx.labs(p, ct_day, [3000963, 3010813, 3017732, 3024929, 3016723, 3013721, 3006923, 3020491, 3024128], vid=wvid)
        cea = ctx.lab_value(3028641, shift={"I": -3, "II": 0, "III": 4, "IV": 40}[stage], sd_scale={"IV": 4}.get(stage, 1.0), lo=0.3)
        ctx.measure(p, ct_day, 3028641, cea, vid=wvid)
        ctx.disease_row(p, wvid, cexm_ymd=ct_day, cexm_kncd="L5321", cexm_knnm="CEA", cexm_loinc_cd="2039-6", cexm_loinc_nm="Carcinoembryonic Ag [Mass/volume] in Serum or Plasma",
                        cexm_rslt_cont=str(cea), cexm_rslt_unit_cont="ng/mL")
        ctx.disease_row(p, wvid, cexm_ymd=ct_day, cexm_kncd="L3011", cexm_knnm="CBC", cexm_loinc_cd="58410-2", cexm_loinc_nm="CBC panel - Blood by Automated count",
                        cexm_rslt_cont=f"Hb {base_labs[3000963]} g/dL, WBC {base_labs[3010813]}, PLT {base_labs[3024929]}", cexm_rslt_unit_cont="g/dL")
        stag_day = ct_day
        if stage == "IV" and ctx.bern(0.6):
            stag_day = ctx.days(ct_day, ctx.randint(2, 6)); pv = ctx.visit_on(p, stag_day)
            ctx.procedure(p, stag_day, 4305790, vid=pv)
            ctx.disease_row(p, pv, imex_ymd=stag_day, imex_kncd="PET-WB", imex_knnm="Whole body PET-CT", imex_smct_cd="443271005", imex_smct_nm="PET-CT",
                            imex_rslt_cont=f"Hypermetabolic primary {site_nm.lower()} lesion with {met_nm.lower()} metastasis.")
        prty = ("OBS", "Obstructing mass") if obstruction else (("PRF", "Perforated mass") if perforation else ctx.choice([("ULC", "Ulcerative mass"), ("POL", "Polypoid mass"), ("ANN", "Annular mass")]))
        ctx.disease_row(p, ctx.visit_on(p, stag_day), diag_stag_rcrd_ymd=stag_day, clnc_tnm_stag_vl=f"c{t}{nn}{m}", clnc_t_stag_vl="c" + t, clnc_n_stag_vl=nn, clnc_m_stag_vl=m,
                        clnc_tumr_prty_cd=prty[0], clnc_tumr_prty_nm=prty[1])
        if met_cd:
            ctx.disease_row(p, ctx.visit_on(p, stag_day), mtdg_ymd=stag_day, mtst_site_cd=met_cd, mtst_site_nm=met_nm)
        # IHC (MMR) / 분자병리
        imem_day = ctx.days(index, 2); imem_read = ctx.days(imem_day, ctx.randint(2, 5))
        dmmr = ctx.bern(0.15 if stage != "IV" else 0.05)
        lost = ctx.choice(["MLH1/PMS2", "MSH2/MSH6", "MSH6", "PMS2"], p=[0.6, 0.25, 0.1, 0.05]) if dmmr else None
        stains = {g: ("loss" if (lost and g in lost.split("/")) else "intact") for g in ("MLH1", "MSH2", "MSH6", "PMS2")}
        _report(ctx, p, imem_read, IHC_REPORT.format(mlh1=stains["MLH1"], msh2=stains["MSH2"], msh6=stains["MSH6"], pms2=stains["PMS2"],
                                                    mmr=f"MMR-deficient (loss of {lost})" if dmmr else "MMR-proficient"), 44814640, 36716165)
        ctx.disease_row(p, ctx.visit_on(p, imem_day), imem_ymd=imem_day, impt_read_ymd=imem_read, imem_kncd="IHC-MMR", imem_knnm="MMR protein IHC (MLH1/MSH2/MSH6/PMS2)",
                        imem_opn_cd="dMMR" if dmmr else "pMMR", imem_opn_nm="MMR deficient" if dmmr else "MMR proficient",
                        imem_rslt_cont=f"MLH1 {stains['MLH1']}, MSH2 {stains['MSH2']}, MSH6 {stains['MSH6']}, PMS2 {stains['PMS2']}")
        mlem_day = ctx.days(index, ctx.randint(5, 10)); mlem_read = ctx.days(mlem_day, ctx.randint(5, 12))
        kras = ctx.bern(0.45); nras = (not kras) and ctx.bern(0.05); braf = (not kras and not nras) and ctx.bern(0.2 if dmmr else 0.06)
        msi = "MSI-H" if dmmr else ("MSI-L" if ctx.bern(0.05) else "MSS")
        kras_txt = ctx.choice(["G12D", "G12V", "G13D", "G12C"]) if kras else "wild type"
        mvid = ctx.visit_on(p, mlem_day)
        _report(ctx, p, mlem_read, MOL_REPORT.format(kras=kras_txt, nras="G12D" if nras else "wild type", braf="V600E" if braf else "wild type", msi=msi), 44814640, 36716165)
        for gene, res, cont in (("KRAS", "MUT" if kras else "WT", f"KRAS {kras_txt}"), ("NRAS", "MUT" if nras else "WT", "NRAS " + ("G12D" if nras else "wild type")),
                                ("BRAF", "MUT" if braf else "WT", "BRAF " + ("V600E" if braf else "wild type")), ("MSI", msi, f"MSI status {msi}")):
            ctx.disease_row(p, mvid, mlem_ymd=mlem_day, mlpt_read_ymd=mlem_read, mlem_kncd=f"MOL-{gene}", mlem_knnm=f"{gene} {'mutation test (PCR)' if gene != 'MSI' else 'analysis (PCR, 5 markers)'}",
                            mlem_opn_cd=res, mlem_opn_nm=cont, mlem_rslt_cont=cont)

        # ---- 2) 치료
        last_ctx_date = max(stag_day, mlem_read)
        surgery_day = None
        antp_ids = []
        had_oxali = False
        ccrt = rectal and stage in ("II", "III") and ecog <= 2
        pt, pn, pm = t, nn, "M0"
        if stage in ("I", "II", "III") and ecog <= 2:
            if ccrt:
                s = ctx.days(last_ctx_date, ctx.randint(10, 21))
                aid, e, cyc = ctx.antp(p, 1, "Capecitabine (preoperative CCRT)", [1337620], s, 2, 1, 1, ecog=ecog, response="NE", cycle_days=21)
                antp_ids.append(aid); _drug_rows(ctx, p, cyc, [1337620], 21)
                _chemo_monitoring(ctx, p, cyc, aid, [1337620], ae_p=0.3)
                rvid = ctx.visit_on(p, s)
                ctx.procedure(p, s, 4181206, vid=rvid)
                ctx.disease_row(p, rvid, rdt_prsc_ymd=s, rdt_kncd="RT-IMRT", rdt_knnm="세기조절 방사선치료", rdt_prps_cd="NEO", rdt_prps_nm="수술 전 (neoadjuvant)",
                                rdt_site_cd="PELV", rdt_site_nm="골반 (직장 및 직장간막)", rd_gy=1.8, rd_impl_nt=28, rd_totl_gy=50.4)
                ctx.antp_update(aid, treatment_outcome=0, best_overall_response_source_value=ctx.choice(["PR", "SD", "CR"], p=[0.6, 0.25, 0.15]))
                # 재병기 MRI
                rs_day = ctx.days(e, ctx.randint(35, 50))
                rvid2 = ctx.visit_on(p, rs_day)
                ctx.procedure(p, rs_day, 4123795, vid=rvid2)
                trg = ctx.choice(["1", "2", "3", "4"], p=[0.15, 0.35, 0.35, 0.15])
                res_anvg = mri["anvg"] if mri else round(ctx.rand(3, 10), 2)
                _report(ctx, p, rs_day, MRI_RESTAGE.format(trg=trg, res=res_anvg, mrf="clear" if trg in ("1", "2", "3") else "threatened"), 44814637, 36716164, vid=rvid2)
                ctx.disease_row(p, rvid2, imex_ymd=rs_day, imex_kncd="MRI-PEL", imex_knnm="Pelvis MRI (rectal cancer restaging)", imex_smct_cd="241629003", imex_smct_nm="MRI of pelvis",
                                tumr_rspn_grcd="mrTRG" + trg, tumr_rspn_grnm={"1": "Complete response", "2": "Good response", "3": "Moderate response", "4": "Slight response"}[trg],
                                lstm_anvg_dst_vl=res_anvg, lstm_anju_dst_vl=max(0.0, round(res_anvg - ctx.rand(1.5, 3.0), 2)), rtcn_loca_dst_vl=res_anvg,
                                tumr_msfc_shrt_dst_vl=round(ctx.rand(1, 12), 1), imex_rslt_cont=f"mrTRG {trg} after CCRT")
                surgery_day = ctx.days(rs_day, ctx.randint(7, 21))
                # 병리 다운스테이징
                if trg == "1": pt, pn = "T0", "N0"
                elif trg == "2": pt = {"T4b": "T3", "T4a": "T3", "T3": "T2", "T2": "T1"}.get(t, t); pn = "N0" if ctx.bern(0.7) else "N1a"
                else: pt = t if ctx.bern(0.7) else {"T4b": "T4a", "T4a": "T3", "T3": "T3", "T2": "T2"}[t]; pn = nn if ctx.bern(0.6) else ctx.choice(["N0", "N1a", "N1b"])
            else:
                surgery_day = ctx.days(last_ctx_date, ctx.randint(10, 30))
                pt = t if ctx.bern(0.8) else ctx.choice(["T2", "T3", "T4a"])
                pn = nn if ctx.bern(0.75) else ctx.choice(["N0", "N1a", "N1b", "N2a"])
            surgery_day, dsch, ostomy_info = _surgery(ctx, p, surgery_day, kcd, site_cd, site_nm, side, rectal, mri, obstruction, perforation, t, "CUR")
            last_ctx_date = dsch
            pos_ln, tot_ln = _sgpt(ctx, p, surgery_day, site_cd, site_nm, rectal, kcd, hist_cd, grade, pt, pn, pm, ccrt, size)
            path_stage = "III" if pn != "N0" else ("II" if pt in ("T3", "T4a", "T4b") else "I")
            # 보조항암
            if (path_stage == "III" or (path_stage == "II" and ctx.bern(0.3))) and ecog <= 2:
                s = ctx.days(surgery_day, ctx.randint(28, 50))
                line = len(antp_ids) + 1
                if ctx.bern(0.6):
                    aid, e, cyc = ctx.antp(p, line, "FOLFOX", [1320011, 955632], s, ctx.randint(8, 12), 2, 1, ecog=ecog, response="NE", cycle_days=14)
                    drugs, cd = [1320011, 955632], 14
                else:
                    aid, e, cyc = ctx.antp(p, line, "CAPOX", [1320011, 1337620], s, ctx.randint(4, 8), 2, 1, ecog=ecog, response="NE", cycle_days=21)
                    drugs, cd = [1320011, 1337620], 21
                antp_ids.append(aid); had_oxali = True; last_ctx_date = e
                _drug_rows(ctx, p, cyc, drugs, cd)
                _chemo_monitoring(ctx, p, cyc, aid, drugs)
                ctx.antp_update(aid, treatment_outcome=0)
            # 장루 복원
            if ostomy_info and ostomy_info["temporary"] and ctx.bern(0.8):
                rd = ctx.days(max(ctx.days(surgery_day, 90), ctx.days(last_ctx_date, 30)), ctx.randint(0, 90))
                if rd <= ctx.today:
                    rvid = ctx.visit(p, rd, INPATIENT, los=5)
                    ctx.disease_row(p, rvid, ostm_reop_ymd=rd, ostm_reop_cd="O2851", ostm_reop_nm="장루 복원술", ostm_reop_spcd="IR" if ostomy_info["kind"] == "ILEO" else "CR",
                                    ostm_reop_spnm="회장루 복원" if ostomy_info["kind"] == "ILEO" else "결장루 복원",
                                    ostm_reop_loca_spcd="RLQ" if ostomy_info["kind"] == "ILEO" else "LLQ", ostm_reop_loca_spnm="우하복부" if ostomy_info["kind"] == "ILEO" else "좌하복부")
                    ctx.labs(p, ctx.days(rd, 1), [3000963, 3010813, 3016723], vid=rvid)
                    last_ctx_date = max(last_ctx_date, ctx.days(rd, 5))
        elif stage == "IV":
            if obstruction and ctx.bern(0.7):
                sd = ctx.days(last_ctx_date, ctx.randint(3, 14))
                surgery_day, dsch, _ = _surgery(ctx, p, sd, kcd, site_cd, site_nm, side, rectal, mri, obstruction, perforation, t, "PAL", met=(met_cd, met_nm))
                _sgpt(ctx, p, surgery_day, site_cd, site_nm, rectal, kcd, hist_cd, grade, t, nn, "M1", False, size)
                last_ctx_date = dsch
            s = ctx.days(last_ctx_date, ctx.randint(10, 25))
            if ecog <= 2:
                drugs = [1320011, 955632, 1397599]
                aid, e, cyc = ctx.antp(p, len(antp_ids) + 1, "FOLFOX + Bevacizumab", drugs, s, max(1, _cap_cycles(ctx, s, ctx.randint(8, 12), 14)), 3, 2, ecog=ecog,
                                       response=ctx.choice(["PR", "SD", "PD"], p=[0.5, 0.35, 0.15]), cycle_days=14)
                antp_ids.append(aid); had_oxali = True; last_ctx_date = e
                _drug_rows(ctx, p, cyc, drugs, 14)
                _chemo_monitoring(ctx, p, cyc, aid, drugs)
                if ctx.bern(0.55):
                    pd_day = ctx.days(e, ctx.randint(20, 120))
                    if pd_day <= ctx.today:
                        pvid = ctx.visit_on(p, pd_day)
                        ctx.procedure(p, pd_day, 4207701, vid=pvid)
                        new_cd, new_nm = ctx.choice(MET_SITES, p=MET_P)
                        _report(ctx, p, pd_day, f"CT abdomen and pelvis: interval increase of {met_nm.lower()} metastases and new {new_nm.lower()} lesions. Progressive disease.", 44814637, 36716164, vid=pvid)
                        ctx.disease_row(p, pvid, imex_ymd=pd_day, imex_kncd="CT-AP-C", imex_knnm="Abdomen and pelvis CT with contrast", imex_smct_cd="418891003", imex_smct_nm="CT of abdomen and pelvis with contrast",
                                        imex_rslt_cont="Progressive disease")
                        ctx.disease_row(p, pvid, mtdg_ymd=pd_day, mtst_site_cd=new_cd, mtst_site_nm=new_nm)
                        ctx.antp_update(aid, treatment_outcome=0, days_to_progression=pd_day, progression_or_recurrence_anatomic_site=new_nm)
                        last_ctx_date = pd_day
                        s2 = ctx.days(pd_day, ctx.randint(7, 21))
                        n2 = _cap_cycles(ctx, s2, ctx.randint(3, 8), 14)
                        if ctx.bern(0.7) and n2 > 0:
                            drugs2 = [1367268, 955632, 1397599]
                            aid2, e2, cyc2 = ctx.antp(p, len(antp_ids) + 1, "FOLFIRI + Bevacizumab", drugs2, s2, n2, 3, 2, ecog=min(ecog + 1, 3),
                                                      response=ctx.choice(["SD", "PD", "PR"], p=[0.45, 0.4, 0.15]), cycle_days=14)
                            antp_ids.append(aid2); last_ctx_date = e2
                            _drug_rows(ctx, p, cyc2, drugs2, 14)
                            _chemo_monitoring(ctx, p, cyc2, aid2, drugs2)
                            ctx.antp_update(aid2, treatment_outcome=0)
                        if ctx.bern(0.5):
                            _death(ctx, p, ctx.days(last_ctx_date, ctx.randint(15, 180)))
                    else:
                        ctx.antp_update(aid, treatment_outcome=1 if e >= ctx.days(ctx.today, -60) else 0)
                else:
                    ctx.antp_update(aid, treatment_outcome=1 if e >= ctx.days(ctx.today, -60) else 0)
            else:
                # 전신상태 불량: 최적 지지요법
                ctx.observation(p, s, 4257895, vid=ctx.visit_on(p, s), value_number=ecog, value_string=f"ECOG {ecog}, best supportive care")
                if ctx.bern(0.6):
                    _death(ctx, p, ctx.days(s, ctx.randint(30, 240)))
        else:
            # I~III 이나 ECOG 불량: 수술 불가, 경과관찰
            ctx.observation(p, last_ctx_date, 4257895, vid=ctx.visit_on(p, last_ctx_date), value_number=ecog, value_string=f"ECOG {ecog}, not a surgical candidate")

        # ---- 3) 추적 및 재발
        if p.death_date is None:
            fu = ctx.days(last_ctx_date, 180)
            recurred = False; k = 0
            rec_p = {"I": 0.01, "II": 0.025, "III": 0.05, "IV": 0.0}[stage]   # 방문당 재발 확률 (5년 누적 약 5/15/30%)
            while fu <= ctx.today and k < 10 and p.death_date is None:
                fvid = ctx.visit_on(p, fu)
                ctx.procedure(p, fu, 4207701, vid=fvid)
                fcea = ctx.lab_value(3028641, shift=-3, lo=0.3)
                ctx.measure(p, fu, 3028641, fcea, vid=fvid)
                ctx.disease_row(p, fvid, cexm_ymd=fu, cexm_kncd="L5321", cexm_knnm="CEA", cexm_loinc_cd="2039-6", cexm_loinc_nm="Carcinoembryonic Ag [Mass/volume] in Serum or Plasma",
                                cexm_rslt_cont=str(fcea), cexm_rslt_unit_cont="ng/mL")
                recur_now = surgery_day is not None and stage != "IV" and not recurred and ctx.bern(rec_p)
                ctx.disease_row(p, fvid, imex_ymd=fu, imex_kncd="CT-AP-C", imex_knnm="Abdomen and pelvis CT with contrast", imex_smct_cd="418891003", imex_smct_nm="CT of abdomen and pelvis with contrast",
                                imex_rslt_cont="Suspicious recurrence" if recur_now else "No evidence of recurrence")
                if recur_now:
                    recurred = True
                    if ctx.bern(0.25):
                        site_r = ("C20" if rectal else "C18", "Anastomotic site (local recurrence)"); distant = False
                    else:
                        site_r = ctx.choice(MET_SITES, p=MET_P); distant = True
                    _report(ctx, p, fu, f"CT abdomen and pelvis: new {site_r[1].lower()} lesion, suspicious for recurrence. CEA {fcea} ng/mL.", 44814637, 36716164, vid=fvid)
                    ctx.disease_row(p, fvid, rldg_ymd=fu, rlps_site_cd=site_r[0], rlps_site_nm=site_r[1])
                    if distant:
                        ctx.disease_row(p, fvid, mtdg_ymd=fu, mtst_site_cd=site_r[0], mtst_site_nm=site_r[1])
                    s3 = ctx.days(fu, ctx.randint(10, 30))
                    n3 = _cap_cycles(ctx, s3, ctx.randint(6, 12), 14)
                    if ecog <= 2 and n3 > 0:
                        line = len(antp_ids) + 1
                        if had_oxali:
                            drugs3, reg = [1367268, 955632, 1397599], "FOLFIRI + Bevacizumab"
                        else:
                            drugs3, reg = [1320011, 955632, 1397599], "FOLFOX + Bevacizumab"
                        aid3, e3, cyc3 = ctx.antp(p, line, reg, drugs3, s3, n3, 3, 2, ecog=ecog, response=ctx.choice(["PR", "SD", "PD"]), cycle_days=14)
                        antp_ids.append(aid3)
                        _drug_rows(ctx, p, cyc3, drugs3, 14)
                        _chemo_monitoring(ctx, p, cyc3, aid3, drugs3)
                        ctx.antp_update(aid3, treatment_outcome=1 if e3 >= ctx.days(ctx.today, -60) else 0)
                        fu = e3
                        if ctx.bern(0.35):
                            _death(ctx, p, ctx.days(e3, ctx.randint(30, 240)))
                fu = ctx.days(fu, ctx.randint(170, 190)); k += 1
        if antp_ids:
            _set_patient(ctx, p, antp_id=antp_ids[0])
        ctx.finalize_person(p)


# ----------------------------------------------------------------------------- helpers
def _yn(b):
    return "Y" if b else "N"


def _ynm(b):
    return "예" if b else "아니오"


def _set_patient(ctx, p, **kw):
    """환자 불변 필드 갱신: 이미 생성된 행에도 반영."""
    p.patient_fields.update(kw)
    for r in ctx.rows[ctx.disease]:
        if r["person_id"] == p.person_id:
            r.update(kw)


def _report(ctx, p, date, text, note_type, note_class, vid=None):
    """NOTE + 특화 테이블 note 그룹 행."""
    vid = vid or ctx.visit_on(p, date)
    nid = ctx.note(p, date, text, note_type=note_type, note_class=note_class, vid=vid)
    ctx.disease_row(p, vid, note_id=nid, note_date=date, note_type_concept_id=note_type, note_text=text)
    return nid


def _ctnm(ctx, stage, rectal):
    if stage == "I":
        return ctx.choice(["T1", "T2"], p=[0.4, 0.6]), "N0", "M0"
    if stage == "II":
        return ctx.choice(["T3", "T4a", "T4b"], p=[0.75, 0.2, 0.05]), "N0", "M0"
    if stage == "III":
        return ctx.choice(["T2", "T3", "T4a", "T4b"], p=[0.1, 0.6, 0.2, 0.1]), ctx.choice(["N1a", "N1b", "N2a", "N2b"], p=[0.3, 0.3, 0.25, 0.15]), "M0"
    return ctx.choice(["T3", "T4a", "T4b"], p=[0.6, 0.3, 0.1]), ctx.choice(["N1b", "N2a", "N2b"]), ctx.choice(["M1a", "M1b"], p=[0.6, 0.4])


def _rectal_mri(ctx, p, day, vid, t, nn, rectal):
    ctx.procedure(p, day, 4123795, vid=vid)
    anvg = round(ctx.rand(2.0, 12.0), 2) if rectal else round(ctx.rand(12.0, 16.0), 2)
    anju = max(0.0, round(anvg - ctx.rand(1.5, 3.0), 2))
    mrf = round(ctx.rand(0, 3) if t == "T4b" else ctx.rand(0.5, 15), 1)
    emvi = t in ("T3", "T4a", "T4b") and ctx.bern(0.35)
    mln = nn != "N0"; eln = mln and ctx.bern(0.2)
    circ_cd, circ_nm, ansp = ctx.choice([("ANT", "Anterior", "11 to 1 o'clock"), ("POST", "Posterior", "5 to 7 o'clock"), ("LLAT", "Left lateral", "2 to 4 o'clock"),
                                         ("RLAT", "Right lateral", "8 to 10 o'clock"), ("CIRC", "Circumferential", "Whole circumference")])
    if anvg < 5: fp = ("BL", "Below anterior peritoneal reflection")
    elif anvg < 10: fp = ("AT", "At the level of anterior peritoneal reflection")
    else: fp = ("AB", "Above anterior peritoneal reflection")
    t4b = ctx.choice([("PRO", "Prostate / seminal vesicle"), ("VAG", "Vagina / uterus"), ("BLD", "Urinary bladder"), ("SAC", "Sacrum")]) if t == "T4b" else (None, None)
    if t4b[0] == "VAG" and p.gender == MALE: t4b = ("PRO", "Prostate / seminal vesicle")
    if t4b[0] == "PRO" and p.gender == FEMALE: t4b = ("VAG", "Vagina / uterus")
    depth = round(ctx.rand(1, 15), 1) if t in ("T3", "T4a", "T4b") else None
    _report(ctx, p, day, MRI_REPORT.format(anvg=anvg, anju=anju, circ=circ_nm.lower(), t=t[1:], n=nn[1:], mrf=mrf, emvi="positive" if emvi else "negative",
                                           mln="present" if mln else "absent", eln="present" if eln else "absent"), 44814637, 36716164, vid=vid)
    ctx.disease_row(p, vid, imex_ymd=day, imex_kncd="MRI-PEL", imex_knnm="Pelvis MRI (rectal cancer protocol)", imex_smct_cd="241629003", imex_smct_nm="MRI of pelvis",
                    lstm_anvg_dst_vl=anvg, lstm_anju_dst_vl=anju, rtcn_loca_dst_vl=anvg, tumr_msfc_shrt_dst_vl=mrf,
                    tumr_emvi_ex_yn_spcd=_yn(emvi), tumr_emvi_ex_yn_spnm="양성" if emvi else "음성",
                    tumr_msrt_ln_mtst_ex_yn_spcd=_yn(mln), tumr_msrt_ln_mtst_ex_yn_spnm="있음" if mln else "없음",
                    tumr_exms_ln_mtst_ex_yn_spcd=_yn(eln), tumr_exms_ln_mtst_ex_yn_spnm="있음" if eln else "없음",
                    tumr_circ_loca_spcd=circ_cd, tumr_circ_loca_spnm=circ_nm, tumr_ansp_exts_cont=ansp, frnt_prtm_tumr_rlcd=fp[0], frnt_prtm_tumr_rlnm=fp[1],
                    tmin_mxdp_vl=depth, t4b_inva_orgn_spcd=t4b[0], t4b_inva_orgn_spnm=t4b[1],
                    imex_rslt_cont=f"mrT{t[1:]}N{nn[1:]}, MRF {'involved' if mrf < 1 else 'clear'}, EMVI {'+' if emvi else '-'}")
    return dict(anvg=anvg, anju=anju, mrf=mrf)


def _surgery(ctx, p, day, kcd, site_cd, site_nm, side, rectal, mri, obstruction, perforation, t, purpose, met=(None, None)):
    """수술 입원 + oprt 행. 반환 (수술일, 퇴원일, 장루정보)."""
    los = ctx.randint(6, 10) if purpose == "CUR" else ctx.randint(8, 14)
    svid = ctx.visit(p, day, INPATIENT, los=los)
    low = rectal and mri is not None and mri["anvg"] < 5
    if rectal:
        apr = low and ctx.bern(0.5)
        ctx.procedure(p, day, 4148096, vid=svid)
        op_cd, op_nm = ("APR", "Abdominoperineal resection") if apr else ("LAR", "Low anterior resection")
        oprt_kncd = "Q2611" if apr else "Q2602"
    else:
        apr = False
        ctx.procedure(p, day, 4050470, vid=svid)
        if kcd == "C19": op_cd, op_nm, oprt_kncd = "AR", "Anterior resection", "Q2601"
        elif side == "R": op_cd, op_nm, oprt_kncd = "RHC", "Right hemicolectomy", "Q2591"
        elif site_cd == "DES": op_cd, op_nm, oprt_kncd = "LHC", "Left hemicolectomy", "Q2592"
        else: op_cd, op_nm, oprt_kncd = "AR", "Anterior resection (sigmoidectomy)", "Q2601"
    lap = ctx.bern(0.8) and not perforation
    conv = lap and ctx.bern(0.08)
    conv_rsn = ctx.choice([("ADH", "Severe adhesion"), ("BLD", "Bleeding"), ("T4", "Bulky tumor / adjacent organ invasion")]) if conv else (None, None)
    # 장루
    ostomy_info = None
    if apr:
        ost = ("Y", ("2", "Permanent end colostomy (APR)")); ostomy_info = dict(temporary=False, kind="COLO")
    elif rectal and ctx.bern(0.8 if low else 0.4):
        ost = ("Y", ("1", "Anastomosis protection (diverting ileostomy)")); ostomy_info = dict(temporary=True, kind="ILEO")
    elif (obstruction or perforation) and ctx.bern(0.5):
        ost = ("Y", ("3", "Obstruction / perforation (Hartmann)")); ostomy_info = dict(temporary=True, kind="COLO")
    else:
        ost = ("N", (None, None))
    ebl = int(ctx.normal(150 if lap and not conv else 350, 120, 20, 2000, 0))
    ebl_cd = "1" if ebl < 100 else ("2" if ebl <= 500 else "3")
    left_side = rectal or side == "L"
    ima = ctx.choice([("H", "High ligation (at origin)"), ("L", "Low ligation (below left colic artery)")], p=[0.7, 0.3]) if left_side else (None, None)
    if apr:
        anes = (None, None); anes_detl = (None, None); ansc = None
    else:
        anes = ctx.choice([("ST", "Stapled"), ("HS", "Hand-sewn")], p=[0.85, 0.15])
        anes_detl = ctx.choice([("EEA", "End-to-end"), ("SSA", "Side-to-side"), ("ESA", "End-to-side")], p=[0.6, 0.3, 0.1]) if anes[0] == "ST" else ("EEA", "End-to-end")
        ansc = round(ctx.rand(2.0, 8.0), 1) if rectal else (round(ctx.rand(10.0, 15.0), 1) if kcd == "C19" else None)
    curdg = ("R2", "R2 (macroscopic residual)") if purpose == "PAL" else (("R1", "R1 (microscopic residual)") if t == "T4b" and ctx.bern(0.2) else ("R0", "R0 (complete resection)"))
    compl = ctx.bern(0.15)
    dsch = ctx.days(day, los)
    row = dict(oprt_ymd=day, oprt_kncd=oprt_kncd, oprt_knnm=op_nm, oprt_prps_cd=purpose, oprt_prps_nm="근치적" if purpose == "CUR" else "고식적",
               oprt_mtcd=("LAP" if lap else "OPEN"), oprt_mtnm=(("복강경 " if lap else "개복 ") + op_nm), oprt_tumr_loca_cd=site_cd, oprt_tumr_loca_nm=site_nm,
               obst_trtm_spcd="Y" if obstruction else "N", obst_trtm_spnm="스텐트 삽입 후 수술" if obstruction else "해당 없음",
               lapr_conv_yn_unid_spcd=_yn(conv) if lap else None, lapr_conv_yn_unid_spnm=(_ynm(conv) if lap else None),
               lapr_conv_resn_spcd=conv_rsn[0], lapr_conv_resn_spnm=conv_rsn[1],
               ostm_frmt_yn_unid_spcd=ost[0], ostm_frmt_yn_unid_spnm="예" if ost[0] == "Y" else "아니오", ostm_frsn_spcd=ost[1][0], ostm_frsn_spnm=ost[1][1],
               ima_ligt_loca_spcd=ima[0], ima_ligt_loca_spnm=ima[1],
               spfl_mobl_yn_unid_spcd=_yn(left_side and ctx.bern(0.4)) if left_side else "N", spfl_mobl_yn_unid_spnm=None,
               curdg_cd=curdg[0], curdg_nm=curdg[1], ansc_loca_dst_vl=ansc, anes_mtcd=anes[0], anes_mtnm=anes[1], anes_mthd_detl_spcd=anes_detl[0], anes_mthd_detl_spnm=anes_detl[1],
               ebl_qty_spcd=ebl_cd, ebl_qty_spnm={"1": "<100 mL", "2": "100-500 mL", "3": ">500 mL"}[ebl_cd], ebl_qty=ebl,
               afop_asmt_item_cd="CUR" if purpose == "CUR" else "PAL", afop_asmt_item_nm="근치적 절제 평가" if purpose == "CUR" else "고식적 절제 평가",
               afoc_trtm_mtcd=("CONS" if compl else None), afoc_trtm_mtnm=("보존적 치료 (항생제/금식)" if compl else None))
    if met[0]:
        row.update(inap_dsnt_mtst_site_cd=met[0], inap_dsnt_mtst_site_nm=met[1])
    ctx.disease_row(p, svid, **row)
    _set_patient(ctx, p, dsch_ymd=dsch)
    ctx.labs(p, ctx.days(day, 1), [3000963, 3010813, 3016723, 3020460], vid=svid)
    if compl:
        ctx.ae(p, ctx.days(day, ctx.randint(2, 5)), 437663, ctx.randint(1, 2), vid=svid)   # postoperative fever
        ctx.condition(p, ctx.days(day, 2), 437663, vid=svid)
    _report(ctx, p, dsch, f"Discharge summary. {op_nm} ({'laparoscopic' if lap else 'open'}{', converted to open' if conv else ''}) on {day.isoformat()} for {site_nm.lower()} cancer. "
                          f"EBL {ebl} mL. {'Diverting ileostomy formed. ' if ost[1][0] == '1' else ''}Postoperative course {'complicated by fever, treated conservatively' if compl else 'uneventful'}. Discharged on POD {los}.",
            44814641, 36716213, vid=svid)
    return day, dsch, ostomy_info


def _sgpt(ctx, p, surgery_day, site_cd, site_nm, rectal, kcd, hist_cd, grade, pt, pn, pm, after_ccrt, csize):
    path_day = ctx.days(surgery_day, ctx.randint(0, 2))
    read_day = ctx.days(path_day, ctx.randint(3, 7))
    svid = ctx.visit_on(p, path_day)
    psize = 0.0 if pt == "T0" else round(csize * ctx.rand(0.7, 1.15), 1)
    tot_ln = ctx.randint(12, 40)
    pos_ln = {"N0": 0, "N1a": 1, "N1b": ctx.randint(2, 3), "N2a": ctx.randint(4, 6), "N2b": ctx.randint(7, 12)}[pn]
    pos_ln = min(pos_ln, tot_ln)
    lvi = pn != "N0" and ctx.bern(0.7) or ctx.bern(0.2); vi = ctx.bern(0.25); pni = ctx.bern(0.2)
    depth = DEPTH.get(pt, ("NT", "No residual tumor"))
    rm_pos = pt == "T4b" and ctx.bern(0.3)
    tme = ctx.choice([("C", "Complete"), ("NC", "Nearly complete"), ("IC", "Incomplete")], p=[0.75, 0.2, 0.05]) if rectal else (None, None)
    gross = ctx.choice(GROSS)
    n_tumor = 2 if ctx.bern(0.04) else 1
    tnm = f"p{pt}{pn}{pm}"
    organ = "Rectum" if rectal else ("Rectosigmoid colon" if kcd == "C19" else "Colon")
    _report(ctx, p, read_day, SGPT_REPORT.format(organ=organ, op="resection", hist=HIST[hist_cd], grade=GRADE[grade].lower(), size=psize, gross=gross[1].lower(), depth=depth[1],
                                                 lvi="present" if lvi else "absent", vi="present" if vi else "absent", pni="present" if pni else "absent",
                                                 rm="involved" if rm_pos else "not involved", pos=pos_ln, tot=tot_ln,
                                                 tme=f"TME quality: {tme[1].lower()}. " if rectal else "", tnm=("y" if after_ccrt else "") + tnm), 44814640, 36716165, vid=svid)
    ctx.disease_row(p, svid, srgc_ptem_ymd=path_day, sgpt_read_ymd=read_day, sgpt_hvst_site_cont=f"{organ}, {site_nm.lower()}", sgpt_tumr_loca_spcd=site_cd, sgpt_tumr_loca_spnm=site_nm,
                    srgc_ptem_rslt_tumr_cnt=n_tumor, tumr_wdth_lnth_vl=psize, tumr_lgtd_lnth_vl=round(psize * ctx.rand(0.6, 1.0), 1), tumr_hght_vl=round(psize * ctx.rand(0.3, 0.7), 1),
                    tumr_max_diam_vl=psize, gros_tpcd=gross[0], gros_tpnm=gross[1], htlg_diag_cd_po=hist_cd, htlg_diag_nm_po=HIST[hist_cd], htlg_grcd=grade, htlg_grnm=GRADE[grade],
                    lymp_inva_ex_yn_spcd=_yn(lvi), lymp_inva_ex_yn_spnm="있음" if lvi else "없음", vasc_inva_ex_yn_spcd=_yn(vi), vasc_inva_ex_yn_spnm="있음" if vi else "없음",
                    nerv_prex_ex_yn_spcd=_yn(pni), nerv_prex_ex_yn_spnm="있음" if pni else "없음", inva_dgre_cd=depth[0], inva_dgre_nm=depth[1],
                    radi_rsmg_invl_yn_spcd=_yn(rm_pos), radi_rsmg_invl_yn_spnm="침범" if rm_pos else "침범 없음", tme_qlt_dgre_spcd=tme[0], tme_qlt_dgre_spnm=tme[1],
                    afop_path_tnm_stag_vl=tnm, afop_path_t_stag_vl="p" + pt, afop_path_n_stag_vl=pn, afop_path_m_stag_vl=pm, totl_ln_cnt=tot_ln, pstv_ln_cnt=pos_ln,
                    htlg_diag_etc_cont=("Pathologic complete response after CCRT" if pt == "T0" else None))
    return pos_ln, tot_ln


def _drug_rows(ctx, p, cycle_dates, drugs, cd):
    """특화 테이블 drug 그룹: 사이클/약제별 1행 (drug_prsc_ymd = DRUG_EXPOSURE 시작일)."""
    for d in cycle_dates:
        vid = ctx.visit_on(p, d)
        for c in drugs:
            dc = CONCEPTS["drugs"][c]
            atc, rx, route = DRUG_META[c]
            days = 14 if dc["route"] == "PO" else 1
            if p.death_date is not None and ctx.days(d, days - 1) > p.death_date:
                days = max(1, (p.death_date - d).days + 1)
            ctx.disease_row(p, vid, drug_prsc_ymd=d, drug_clcd=atc, drug_clnm="항암제 (ATC " + atc + ")", drin_cd=str(c), drin_nm=dc["name"],
                            drug_rxnm_cd=rx, drug_rxnm_nm=dc["name"], amount_value=dc["dose"], amount_unit_concept_id=dc["unit"],
                            drug_prsc_capa=dc["dose"], drug_prsc_capa_unit_cd=dc["dose_unit_label"], drug_prsc_capa_unit_nm=dc["dose_unit_label"],
                            drug_prsc_dcnt=days, drug_mdct_dtrn_mcnt=round(days / 30.0, 2), drug_injc_pth_cd=route, drug_injc_pth_nm="정맥주사" if route == "IV" else "경구")


def _cap_cycles(ctx, start, cycles, cd):
    """마지막 사이클 + 관찰(이상사례) 기간이 검증일을 넘지 않도록 사이클 수 제한. 0 이면 요법 생략."""
    return max(0, min(cycles, (ctx.today - start).days // cd))


def _death(ctx, p, dd):
    if dd > ctx.today:
        return
    ctx.set_death(p, dd)
    ctx.visit(p, ctx.days(dd, -2), INPATIENT, los=2)
    ctx.disease_row(p, ctx.visit_on(p, dd), death_date=dd)
    _set_patient(ctx, p, death_date=dd)


def _chemo_monitoring(ctx, p, cycle_dates, aid, drugs, ae_p=0.45):
    """사이클마다 CBC/신장/간기능, 일부 사이클에 이상사례. oxaliplatin 은 말초신경병증, irinotecan/capecitabine 은 설사 가중."""
    concepts = [27674, 196523, 301794, 439777, 4223659, 4166735, 140214, 4304213, 4141062, 4265412, 432791]
    w = [0.15, 0.10, 0.15, 0.10, 0.12, 0.05, 0.02, 0.03, 0.08, 0.06, 0.08]
    if 1320011 in drugs: w[5] += 0.30
    if 1367268 in drugs or 1337620 in drugs: w[1] += 0.15
    if 1337620 in drugs: w[6] += 0.08   # hand-foot syndrome 을 rash 로 대표
    s = sum(w); w = [x / s for x in w]
    for i, d in enumerate(cycle_dates):
        vid = ctx.visit_on(p, d)
        shifts = {3017732: -1.5 if i > 0 else 0, 3000963: -1.0 if i > 0 else 0}
        ctx.labs(p, d, [3000963, 3010813, 3017732, 3024929, 3016723, 3013721, 3006923], vid=vid, shifts=shifts)
        if i > 0 and ctx.bern(ae_p):
            ae_day = ctx.days(d, ctx.randint(3, 12))
            if p.death_date is not None and ae_day > p.death_date:
                continue
            concept = ctx.choice(concepts, p=w)
            lo, hi = CONCEPTS["adverse_events"][concept]["typical_grade"]
            grade = ctx.randint(lo, hi)
            avid = ctx.visit(p, ae_day, ER if grade >= 3 else OUTPATIENT)
            ctx.ae(p, ae_day, concept, grade, antp_id=aid, vid=avid, action=2 if grade >= 3 else 1)
            ctx.condition(p, ae_day, concept, vid=avid)
            if concept in (301794, 4304213):
                ctx.drug(p, ae_day, 1301125, 3, vid=avid, freq=1)
            if concept in (196523, 432791) and grade >= 2:
                ctx.drug(p, ae_day, 35201159, 3, vid=avid, freq=2)

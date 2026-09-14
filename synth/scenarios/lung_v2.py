# -*- coding: utf-8 -*-
"""폐암 코호트 시나리오 (v2 저장 구조).

여정은 v1(`lung.py`)과 같다. 달라지는 것은 적는 자리다.

  v1                                   v2
  LUNG_CANCER 한 테이블에 전부          OMOP 14개 + 확장 4개로 나뉜다
  흡연·ECOG·신체계측이 특화 테이블       OBSERVATION·MEASUREMENT (코어 파생 변수 자리)
  생검·수술병리가 특화 테이블            SPECIMEN + PATHOLOGY_REPORT + PATHOLOGY_TUMOR
  유전자검사가 특화 테이블               BIOMARKER
  영상 소견이 특화 테이블                LUNG_EXAM
  항암요법이 ANTP_THERAPY               EPISODE + EPISODE_EVENT(약물)

값이 있는 컬럼(`*_concept_id`)은 값 집합의 코드를 `ctx.cs()` 로 바꿔 넣는다.
없는 코드를 쓰면 생성이 바로 멈추므로, 코드표와 어긋난 데이터가 나오지 않는다.
"""
import datetime as dt

from framework_v2 import D, FEMALE, INPATIENT, MALE, OUTPATIENT, CtxV2

LC = 4115276                      # Malignant tumor of lung
SCLC, NSCLC = 258375, 4311499
HIST = {1: ("Adenocarcinoma", "8140/3"), 2: ("Squamous cell carcinoma", "8070/3"),
        4: ("Small cell carcinoma", "8041/3"), 3: ("Large cell carcinoma", "8012/3")}
STAGES = ["IA", "IB", "IIA", "IIB", "IIIA", "IIIB", "IV"]
STAGE_P = [0.16, 0.10, 0.07, 0.07, 0.12, 0.08, 0.40]
TNM = {"IA": ("T1b", "N0", "M0"), "IB": ("T2a", "N0", "M0"), "IIA": ("T2b", "N0", "M0"), "IIB": ("T3", "N0", "M0"),
       "IIIA": ("T3", "N2", "M0"), "IIIB": ("T4", "N2", "M0"), "IV": ("T2a", "N2", "M1b")}
TSIZE = {"T1b": (1.1, 2.0), "T2a": (3.1, 4.0), "T2b": (4.1, 5.0), "T3": (5.1, 7.0), "T4": (7.1, 9.0)}
LOBE = [("RUL", "우상엽"), ("RML", "우중엽"), ("RLL", "우하엽"), ("LUL", "좌상엽"), ("LLL", "좌하엽")]
MET = [("LIVER", "간"), ("BONE", "골"), ("BRAIN", "뇌"), ("ADRENAL", "부신")]
LABS = [3000963, 3010813, 3017732, 3024929, 3016723, 3013721, 3006923, 3020491, 3022250]
DIFF = {"well": "WD", "moderately": "MD", "poorly": "PD"}

CT_REPORT = ("Chest CT (contrast). {lobe} 에 {size} cm 크기의 spiculated mass. {node}. {met} "
             "Impression: Lung cancer, {lobe}, c{t}{n}{m}.")
PATH_REPORT = ("Lung, {lobe}, {method}: {hist}. Tumor size {size} cm. Differentiation: {diff}. "
               "Visceral pleural invasion: {vpi}. Lymph nodes: {ln}. Pathologic stage p{t}{n}{m}.")
MOL_REPORT = "Molecular pathology (NGS panel): EGFR {egfr}; ALK IHC {alk}; KRAS {kras}; PD-L1 TPS {pdl1}%."


def generate(ctx: CtxV2, n=100):
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
        size = round(ctx.rand(*TSIZE[t]), 1)
        smoker = ctx.bern(0.75 if gender == MALE else 0.15)
        cur_smok = smoker and ctx.bern(0.5)
        egfr = (hist == 1) and ctx.bern(0.45 if gender == FEMALE else 0.3)
        diff = ctx.choice(["well", "moderately", "poorly"])

        # ---- 1) 진단 입원 (3일)
        dx_vid = ctx.visit(p, index, INPATIENT, los=3)
        dx_cond = ctx.condition(p, index, LC, vid=dx_vid, source=f"C34.{1 if 'U' in lobe_cd else 3}")
        ctx.condition(p, index, SCLC if hist == 4 else NSCLC, vid=dx_vid)
        if smoker and ctx.bern(0.4):
            ctx.condition(p, index, 255573, vid=dx_vid)                      # COPD
        if ctx.bern(0.35):
            ctx.condition(p, index, 320128, vid=dx_vid)                      # 고혈압
        if ctx.bern(0.2):
            ctx.condition(p, index, 201826, vid=dx_vid)                      # 제2형 당뇨병
        # 질환 에피소드 — 이 환자의 암 경과 전체를 묶는 지붕
        disease_ep = ctx.episode(p, index, None, ctx.seeds["episode_disease"], LC)
        ctx.episode_event(disease_ep, dx_cond, ctx.seeds["field_condition"])

        ct_day, bx_day, pet_day = index, ctx.days(index, 1), ctx.days(index, 2)
        ctx.procedure(p, ct_day, 4059400, vid=dx_vid, source="CT-CHEST-C")
        ctx.procedure(p, bx_day, 4032404, vid=dx_vid, source="BRONCH-BX")
        ctx.procedure(p, pet_day, 4305790, vid=dx_vid, source="PET-WB")
        labs = ctx.labs(p, index, LABS, vid=dx_vid)
        ht = ctx.normal(170 if gender == MALE else 157, 6, 145, 190)
        wt = ctx.normal(66 if gender == MALE else 56, 9, 38, 110)
        bmi = round(wt / (ht / 100) ** 2, 1)
        for concept, val in ((3036277, ht), (3025315, wt), (3038553, bmi)):
            ctx.measure(p, index, concept, val, vid=dx_vid)
        ecog = ctx.choice([0, 1, 2, 3], p=[0.3, 0.45, 0.2, 0.05])
        ctx.observation(p, index, 4257895, vid=dx_vid, value_number=ecog, value_string=f"ECOG {ecog}")
        # 흡연은 v1 에서 특화 테이블 컬럼이었으나 v2 는 코어 파생 변수 자리(OBSERVATION)로 온다
        ctx.observation(p, index, 4275495, vid=dx_vid,
                        value_string="Current smoker" if cur_smok else ("Ex-smoker" if smoker else "Never smoker"))
        if smoker:
            ctx.observation(p, index, 4298794, vid=dx_vid, value_number=round(ctx.rand(0.5, 2.0), 1))   # 1일 흡연량(갑)
            ctx.observation(p, index, 37017670, vid=dx_vid, value_number=ctx.randint(10, 50))           # 총 흡연기간(년)
            if not cur_smok:
                ctx.observation(p, index, 4052030, vid=dx_vid, value_number=index.year - ctx.randint(1, 15))

        met_cd, met_nm = (ctx.choice(MET) if stage == "IV" else (None, None))
        node_txt = "Mediastinal lymphadenopathy" if nn != "N0" else "No significant lymphadenopathy"
        ctx.note(p, ct_day, CT_REPORT.format(lobe=lobe_nm, size=size, node=node_txt,
                                             met=f"Metastasis to {met_nm}." if met_nm else "No distant metastasis.",
                                             t=t, n=nn, m=m), vid=dx_vid)
        # 영상 소견 — 폐 전용 확장 테이블
        ctx.ext("LUNG_EXAM", p, vid=dx_vid, exam_date=ct_day, imaging_tumor_max_diameter_cm=size,
                nodule_radiologic_type_concept_id=ctx.cs("CL_NODULE_RADIOLOGIC_TYPE",
                                                         ctx.choice(["SOLID", "PART_SOLID", "GGN"], p=[0.7, 0.2, 0.1])),
                imaging_diagnostic_classification_concept_id=ctx.cs("CL_IMAGING_DIAGNOSTIC_CLASSIFICATION",
                                                                    ctx.choice(["4A", "4B", "4C", "5"], p=[0.2, 0.3, 0.3, 0.2])),
                ctr_ratio=round(ctx.rand(0.5, 1.0), 2))

        # 생검 검체와 병리 보고 — v1 은 특화 테이블 한 행이었다
        bx_spec = ctx.specimen(p, bx_day, 4002054, vid=dx_vid, source=f"LUNG-{lobe_cd}")
        bx_path = ctx.ext("PATHOLOGY_REPORT", p, vid=dx_vid, specimen_id=bx_spec, specimen_date=bx_day,
                          report_type_concept_id=ctx.cs("CL_PATHOLOGY_REPORT_TYPE", "BIOPSY"),
                          biopsy_method_concept_id=ctx.cs("CL_BIOPSY_METHOD", "ENDOSCOPIC"),
                          biopsy_method_source_value="기관지내시경 생검",
                          biopsy_site_concept_id=ctx.cs("CL_BIOPSY_SITE", "PRIMARY"),
                          biopsy_site_detail_concept_id=ctx.cs("CL_BIOPSY_SITE_DETAIL", lobe_cd),
                          biopsy_site_detail_source_value=lobe_nm,
                          biopsy_histologic_diagnosis_source_value=HIST[hist][0],
                          biopsy_differentiation_concept_id=ctx.cs("CL_BIOPSY_DIFFERENTIATION", DIFF[diff]),
                          biopsy_differentiation_source_value=f"{diff} differentiated",
                          primary_histology_source_value=HIST[hist][1])
        ctx.ext("PATHOLOGY_TUMOR", p, pathology_report_id=bx_path, tumor_count=1,
                pathologic_tumor_max_diameter_cm=size)
        ctx.note(p, bx_day, PATH_REPORT.format(lobe=lobe_nm, method="bronchoscopic biopsy", hist=HIST[hist][0],
                                               size=size, diff=diff, vpi="not assessable", ln="not assessable",
                                               t=t, n=nn, m=m),
                 note_type=44814640, note_class=36716165, vid=dx_vid)

        # 병기는 MEASUREMENT 로 앉는다(서식 STAGING 의 attr_default)
        for concept, val in ((4092588, f"c{t}{nn}{m}"),):
            ctx.measure(p, pet_day, 4092588, vid=dx_vid, source=val)
        if met_cd:
            ctx.observation(p, pet_day, 4258841, vid=dx_vid, value_string=met_nm, source=met_cd)

        # ---- 유전자·면역조직화학 (비소세포만)
        pdl1 = None
        if hist != 4:
            gmt_day = ctx.days(index, ctx.randint(5, 12))
            gvid = ctx.visit_on(p, gmt_day)
            pdl1 = ctx.choice([0, 1, 5, 25, 50, 80])
            alk = ctx.bern(0.04) and not egfr
            kras = (not egfr and not alk) and ctx.bern(0.2)
            ctx.note(p, gmt_day, MOL_REPORT.format(egfr="exon 19 deletion" if egfr else "wild type",
                                                   alk="positive" if alk else "negative",
                                                   kras="G12C" if kras else "wild type", pdl1=pdl1),
                     note_type=44814640, note_class=36716165, vid=gvid)
            for gene, res in (("EGFR", "exon19del" if egfr else "WT"), ("ALK", "POS" if alk else "NEG"),
                              ("KRAS", "G12C" if kras else "WT")):
                ctx.ext("BIOMARKER", p, vid=gvid, specimen_id=bx_spec, test_date=gmt_day,
                        ihc_test_concept_id=ctx.cs("BIOMARKER_RESULT", "미시행"), ihc_test_source_value="-",
                        molecular_pathology_test_concept_id=ctx.cs("BIOMARKER_RESULT", "양성" if res not in ("WT", "NEG") else "음성"),
                        molecular_pathology_test_source_value="NGS panel",
                        mutation_test_method_concept_id=ctx.cs("BIOMARKER_RESULT", "양성" if res not in ("WT", "NEG") else "음성"),
                        mutation_test_method_source_value="Next generation sequencing",
                        mutation_test_gene_source_value=f"{gene} ({res})")
            ctx.ext("BIOMARKER", p, vid=gvid, specimen_id=bx_spec, test_date=gmt_day,
                    ihc_test_concept_id=ctx.cs("BIOMARKER_RESULT", "양성" if pdl1 >= 1 else "음성"),
                    ihc_test_source_value=f"PD-L1 IHC 22C3 TPS {pdl1}%",
                    molecular_pathology_test_concept_id=ctx.cs("BIOMARKER_RESULT", "미시행"),
                    molecular_pathology_test_source_value="-",
                    mutation_test_method_concept_id=ctx.cs("BIOMARKER_RESULT", "미시행"),
                    mutation_test_method_source_value="-", mutation_test_gene_source_value="-")
            ctx.measure(p, gmt_day, 36768668, pdl1, vid=gvid, source="PD-L1 TPS")

        # ---- 폐기능검사 (수술 대상)
        if stage in ("IA", "IB", "IIA", "IIB", "IIIA"):
            pft_day = ctx.days(index, ctx.randint(7, 14))
            pv = ctx.visit_on(p, pft_day)
            ctx.measure(p, pft_day, 3011505, ctx.normal(85, 15, 35, 130), vid=pv, source="FEV1 %pred")
            ctx.measure(p, pft_day, 3009941, ctx.normal(80, 15, 30, 130), vid=pv, source="DLCO %pred")

        # ---- 2) 수술
        surgery_day = None
        if stage in ("IA", "IB", "IIA", "IIB", "IIIA") and ecog <= 2:
            surgery_day = ctx.days(index, ctx.randint(21, 45))
            svid = ctx.visit(p, surgery_day, INPATIENT, los=7)
            proc = ctx.procedure(p, surgery_day, 4033181, vid=svid, source="폐엽절제술")
            ctx.episode_event(disease_ep, proc, ctx.seeds["field_procedure"])
            path_day = ctx.days(surgery_day, ctx.randint(3, 7))
            pt = t if ctx.bern(0.8) else ctx.choice(list(TSIZE))
            # 병리 크기는 영상 크기 언저리에서 나온다(둘이 크게 벌어지면 그 자체가 확인 대상이다)
            psize = round(min(max(size * ctx.rand(0.75, 1.25), 0.5), size + 2.5), 1)
            pn = nn if ctx.bern(0.75) else ctx.choice(["N0", "N1", "N2"])
            tot_ln = ctx.randint(8, 30)
            pos_ln = 0 if pn == "N0" else ctx.randint(1, min(6, tot_ln))
            vpi = ctx.bern(0.3)
            op_spec = ctx.specimen(p, surgery_day, 4002054, vid=svid, source=f"LOBECTOMY-{lobe_cd}")
            op_path = ctx.ext("PATHOLOGY_REPORT", p, vid=svid, specimen_id=op_spec, specimen_date=surgery_day,
                              report_type_concept_id=ctx.cs("CL_PATHOLOGY_REPORT_TYPE", "SURGICAL"),
                              surgical_specimen_site_concept_id=ctx.cs("CL_SURGICAL_SPECIMEN_SITE", "PRIMARY"),
                              surgical_specimen_site_source_value=lobe_nm,
                              surgical_histologic_diagnosis_source_value=HIST[hist][0],
                              biopsy_histologic_diagnosis_source_value=None,
                              primary_histology_source_value=HIST[hist][1],
                              vpi_grade_concept_id=ctx.cs("CL_VPI_GRADE", "PL1" if vpi else "PL0"),
                              stas_yn=1 if ctx.bern(0.2) else 0,
                              obstructive_pneumonia_atelectasis_yn=1 if ctx.bern(0.15) else 0,
                              adenocarcinoma_predominant_subtype_concept_id=(
                                  ctx.cs("CL_ADENOCARCINOMA_PREDOMINANT_SUBTYPE",
                                         ctx.choice(["ACINAR", "PAPILLARY", "SOLID", "LEPIDIC", "MICROPAPILLARY"]))
                                  if hist == 1 else None),
                              lymph_nodes_examined=tot_ln, lymph_nodes_positive=pos_ln)
            ctx.ext("PATHOLOGY_TUMOR", p, pathology_report_id=op_path, tumor_count=1,
                    pathologic_tumor_max_diameter_cm=psize)
            ctx.note(p, path_day, PATH_REPORT.format(lobe=lobe_nm, method="lobectomy", hist=HIST[hist][0],
                                                     size=psize, diff=diff, vpi="present" if vpi else "absent",
                                                     ln=f"{pos_ln}/{tot_ln} positive", t=pt, n=pn, m="M0"),
                     note_type=44814640, note_class=36716165, vid=svid)
            ctx.measure(p, path_day, 4092588, vid=svid, source=f"p{pt}{pn}M0")

        # ---- 3) 항암요법 (에피소드 + 약물)
        first_tx = ctx.days(surgery_day or index, ctx.randint(21, 45))
        plan = _regimen(stage, hist, egfr)
        line = 0
        for regimen_name, drugs, cycles, interval in plan:
            line += 1
            start = first_tx if line == 1 else ctx.days(first_tx, 21 * cycles * (line - 1))
            if p.death_date and start > p.death_date:
                break
            end = ctx.days(start, interval * (cycles - 1) + 20)
            ep = ctx.episode(p, start, end, ctx.seeds["episode_regimen"], LC, number=line, parent=disease_ep)
            for c in range(cycles):
                cday = ctx.days(start, interval * c)
                if p.death_date and cday > p.death_date:
                    break
                cvid = ctx.visit_on(p, cday)
                for drug_concept in drugs:
                    did = ctx.drug(p, cday, drug_concept, days=1 if interval > 7 else 7, vid=cvid,
                                   source=regimen_name)
                    ctx.episode_event(ep, did, ctx.seeds["field_drug"])
                ctx.labs(p, cday, LABS[:5], vid=cvid)
                if ctx.bern(0.25):                       # 이상사례
                    ae = ctx.condition(p, cday, ctx.choice([4160887, 378253, 440674]), vid=cvid,
                                       source=f"CTCAE grade {ctx.randint(1, 3)}")
                    ctx.episode_event(ep, ae, ctx.seeds["field_condition"])
            # 반응평가
            rday = ctx.days(start, interval * cycles)
            if not (p.death_date and rday > p.death_date):
                rvid = ctx.visit_on(p, rday)
                ctx.procedure(p, rday, 4059400, vid=rvid, source="CT-CHEST-C")
                ctx.measure(p, rday, 36769180, vid=rvid,
                            source=ctx.choice(["CR", "PR", "SD", "PD"], p=[0.05, 0.35, 0.4, 0.2]))

        # ---- 4) 추적과 사망
        # 사망일은 오늘을 넘길 수 없다(넘으면 아직 생존한 것이다)
        if stage == "IV" and ctx.bern(0.45):
            d = ctx.days(index, ctx.randint(200, 1100))
            if d <= ctx.today: ctx.set_death(p, d)
        elif stage in ("IIIA", "IIIB") and ctx.bern(0.2):
            d = ctx.days(index, ctx.randint(400, 1500))
            if d <= ctx.today: ctx.set_death(p, d)
        for k in range(1, 9):
            fday = ctx.days(index, 90 * k)
            if fday > ctx.today or (p.death_date and fday > p.death_date):
                break
            fvid = ctx.visit(p, fday, OUTPATIENT)
            ctx.procedure(p, fday, 4059400, vid=fvid, source="CT-CHEST-C")
            ctx.ext("LUNG_EXAM", p, vid=fvid, exam_date=fday,
                    imaging_tumor_max_diameter_cm=round(max(0.0, size * ctx.rand(0.3, 1.2)), 1),
                    nodule_radiologic_type_concept_id=ctx.cs("CL_NODULE_RADIOLOGIC_TYPE", "SOLID"),
                    imaging_diagnostic_classification_concept_id=ctx.cs("CL_IMAGING_DIAGNOSTIC_CLASSIFICATION", "6"),
                    ctr_ratio=round(ctx.rand(0.5, 1.0), 2))
        ctx.finalize_person(p)


def _regimen(stage, hist, egfr):
    """병기·조직형·변이에 따른 치료 줄기. (이름, 약물 concept, 주기 수, 간격일)"""
    if stage in ("IA", "IB"):
        return []
    if stage in ("IIA", "IIB", "IIIA"):
        return [("cisplatin/pemetrexed", [1397141, 1436678], 4, 21)]
    if stage == "IIIB":
        return [("carboplatin/paclitaxel + RT", [1320011, 1378382], 6, 7)]
    if egfr:
        return [("osimertinib", [35604205], 12, 28), ("docetaxel", [1378382], 4, 21)]
    return [("pembrolizumab + carbo/pem", [45775965, 1320011, 1436678], 4, 21),
            ("docetaxel", [1378382], 4, 21)]

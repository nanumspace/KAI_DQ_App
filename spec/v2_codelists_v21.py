# -*- coding: utf-8 -*-
"""사전 v2.1 · 값 집합(코드표) 채우기 + K-AI 어휘 표준 매핑.

배치표(1단계)에서 만든 62개 빈 값 집합에 실제 값을 채운다. 두 가지 원천을 쓴다.
  - LOINC: 로컬 파일(/Users/min/Research/standard_terminology/LOINC/Loinc_2.80/LoincTableCore/LoincTableCore.csv)에서
    grep 으로 직접 확인한 코드만 LOINC_CODES/PFT_ITEMS/ALCOHOL_ITEMS 에 넣었다.
  - SNOMED CT: snowstorm MCP 용어 서버(snomedct/MAIN)로 항목을 검색해 FSN·활성 여부를 확인한 코드만 쓴다.
    SNOMED_CODES 딕셔너리에 (코드표, 코드) → concept_id 로 넣으면 build_spec_v2.py 가 그 값만 SNOMED 로 승격한다.
    2026-09-12 현재 COMORBIDITY_SET(과거력 진단 20종)이 채워졌고, VALUE_SETS 쪽 코드표는 아직 KAI 임시 코드다.
    남은 항목은 spec/v2/spec_v2_report.md 의 "SNOMED 확인 대기" 절에 나열된다.

값의 임상 근거는 각 절 주석에 표기했다(AJCC 8판, WHO/ICC, RECIST 1.1, Lugano/Cheson, ITBCC 2016, MERCURY, EASL-EASD-EASO 2023 MASLD 등).
팀 검토 후 코드·라벨을 바꾸려면 이 파일만 고치고 build_spec_v2.py 를 다시 실행한다.
"""

# ================================================================ 값 집합(코드표): codelist_id -> [(code, ko, en), ...]
VALUE_SETS = {
    # ---------------- 병리·검체 공통
    "CL_BIOPSY_METHOD": [
        ("CORE", "코어 생검(총생검)", "Core needle biopsy"), ("FNA", "세침흡인검사", "Fine needle aspiration"),
        ("EXCISION", "절제생검", "Excisional biopsy"), ("INCISION", "절개생검", "Incisional biopsy"),
        ("PUNCH", "펀치생검", "Punch biopsy"), ("ENDOSCOPIC", "내시경 생검", "Endoscopic biopsy"),
        ("EBUS", "기관지초음파 세침흡인(EBUS-TBNA)", "EBUS-guided transbronchial needle aspiration"),
        ("IMAGE_GUIDED", "영상유도 생검(CT/US)", "Image-guided (CT/US) biopsy"),
        ("VACUUM", "진공보조 생검", "Vacuum-assisted biopsy"), ("SURGICAL", "수술적 생검", "Surgical biopsy"), ("OTHER", "기타", "Other"),
    ],
    "CL_BIOPSY_ADEQUACY": [
        ("ADEQUATE", "적정", "Adequate"), ("INADEQUATE", "부적정·검체 부족", "Inadequate/insufficient"), ("NONDIAGNOSTIC", "비진단적", "Non-diagnostic"),
    ],
    "CL_BIOPSY_DIFFERENTIATION": [  # WHO 등급 (조직학적 분화도)
        ("WD", "고분화(Grade 1)", "Well differentiated (G1)"), ("MD", "중분화(Grade 2)", "Moderately differentiated (G2)"),
        ("PD", "저분화(Grade 3)", "Poorly differentiated (G3)"), ("UD", "미분화·역형성(Grade 4)", "Undifferentiated/anaplastic (G4)"),
        ("GX", "평가 불가", "Not assessable (GX)"),
    ],
    "CL_SURGICAL_HISTOLOGIC_GRADE": [
        ("G1", "Grade 1 (고분화)", "Grade 1 (well differentiated)"), ("G2", "Grade 2 (중분화)", "Grade 2 (moderately differentiated)"),
        ("G3", "Grade 3 (저분화)", "Grade 3 (poorly differentiated)"), ("G4", "Grade 4 (미분화)", "Grade 4 (undifferentiated)"), ("GX", "평가 불가", "Not assessable"),
    ],
    "CL_BIOPSY_LATERALITY": [("RIGHT", "우측", "Right"), ("LEFT", "좌측", "Left"), ("BILATERAL", "양측", "Bilateral"), ("NA", "해당없음", "Not applicable")],
    "CL_SURGICAL_SPECIMEN_LATERALITY": [("RIGHT", "우측", "Right"), ("LEFT", "좌측", "Left"), ("BILATERAL", "양측", "Bilateral"), ("NA", "해당없음(정중)", "Not applicable/midline")],
    "CL_BIOPSY_SITE": [  # 원발/국소/원격 구분 (일반)
        ("PRIMARY", "원발 부위", "Primary tumor site"), ("REGIONAL_NODE", "국소 림프절", "Regional lymph node"),
        ("DISTANT", "원격 전이 부위", "Distant metastatic site"), ("OTHER", "기타(직접 기재)", "Other (specify)"),
    ],
    "CL_SURGICAL_SPECIMEN_SITE": [
        ("PRIMARY", "원발 부위", "Primary tumor site"), ("REGIONAL_NODE", "국소 림프절", "Regional lymph node"),
        ("MARGIN", "절제연", "Resection margin"), ("OTHER", "기타(직접 기재)", "Other (specify)"),
    ],
    "CL_BIOPSY_SITE_DETAIL": [  # 폐엽 + 대장 분절 공용 (질환별로 해당 값만 사용)
        ("RUL", "우상엽", "Right upper lobe"), ("RML", "우중엽", "Right middle lobe"), ("RLL", "우하엽", "Right lower lobe"),
        ("LUL", "좌상엽", "Left upper lobe"), ("LLL", "좌하엽", "Left lower lobe"),
        ("CECUM", "맹장", "Cecum"), ("ASC_COLON", "상행결장", "Ascending colon"), ("HEP_FLEX", "간만곡부", "Hepatic flexure"),
        ("TRANS_COLON", "횡행결장", "Transverse colon"), ("SPL_FLEX", "비만곡부", "Splenic flexure"), ("DESC_COLON", "하행결장", "Descending colon"),
        ("SIGMOID", "S상결장", "Sigmoid colon"), ("RECTUM", "직장", "Rectum"),
    ],
    "CL_GROSS_TYPE": [  # Borrmann 분류 (위장관 종양 육안형)
        ("TYPE1", "제1형(용종형)", "Type 1 (polypoid)"), ("TYPE2", "제2형(경계명확 궤양형)", "Type 2 (fungating/ulcerative, sharp margin)"),
        ("TYPE3", "제3형(침윤성 궤양형)", "Type 3 (ulcerative infiltrative)"), ("TYPE4", "제4형(미만성 침윤형)", "Type 4 (diffusely infiltrative, linitis plastica)"),
        ("TYPE5", "제5형(분류불능)", "Type 5 (unclassifiable)"),
    ],
    "CL_DCIS_NUCLEAR_GRADE": [("LOW", "저등급(Grade 1)", "Low grade (Grade 1)"), ("INTERMEDIATE", "중등도(Grade 2)", "Intermediate grade (Grade 2)"), ("HIGH", "고등급(Grade 3)", "High grade (Grade 3)")],
    "CL_ADENOCARCINOMA_PREDOMINANT_SUBTYPE": [  # IASLC/WHO 폐선암 아형
        ("LEPIDIC", "인설상형(lepidic)", "Lepidic"), ("ACINAR", "선방형(acinar)", "Acinar"), ("PAPILLARY", "유두형(papillary)", "Papillary"),
        ("MICROPAPILLARY", "미세유두형(micropapillary)", "Micropapillary"), ("SOLID", "고형형(solid)", "Solid"),
        ("MUCINOUS", "점액형(invasive mucinous)", "Invasive mucinous"), ("COLLOID", "교질형(colloid)", "Colloid"),
        ("FETAL", "태아형(fetal)", "Fetal"), ("ENTERIC", "장형(enteric)", "Enteric"),
    ],
    "CL_TUMOR_BUDDING_GRADE": [  # ITBCC 2016 consensus (대장암)
        ("BD1", "Bd1(저등급, 0~4개)", "Bd1 - low (0-4 buds)"), ("BD2", "Bd2(중등도, 5~9개)", "Bd2 - intermediate (5-9 buds)"), ("BD3", "Bd3(고등급, ≥10개)", "Bd3 - high (≥10 buds)"),
    ],
    "CL_VPI_GRADE": [  # IASLC 장측흉막침범 등급 (폐암)
        ("PL0", "PL0(침범 없음)", "PL0 - no invasion beyond elastic layer"), ("PL1", "PL1(탄력층 넘어 침범)", "PL1 - invasion beyond elastic layer"),
        ("PL2", "PL2(장측흉막 표면 침범)", "PL2 - invasion to visceral pleural surface"), ("PL3", "PL3(벽측흉막 침범)", "PL3 - invasion into parietal pleura"),
    ],
    "CL_CRM_STATUS": [("NEGATIVE", "음성(>1mm)", "Negative (>1 mm clearance)"), ("POSITIVE", "양성(≤1mm)", "Positive (≤1 mm clearance)"), ("NA", "평가 불가", "Not assessable")],
    "CL_RESECTION_MARGIN_STATUS": [("R0", "R0(음성)", "R0 - margin negative"), ("R1", "R1(현미경적 잔존)", "R1 - microscopic residual"), ("R2", "R2(육안적 잔존)", "R2 - macroscopic residual"), ("RX", "평가 불가", "RX - cannot be assessed")],
    "CL_RESIDUAL_TUMOR_R_CLASS": [("R0", "R0(잔존 없음)", "R0 - no residual tumor"), ("R1", "R1(현미경적 잔존)", "R1 - microscopic residual"), ("R2", "R2(육안적 잔존)", "R2 - macroscopic residual"), ("RX", "평가 불가", "RX - cannot be assessed")],
    "CL_RESECTION_COMPLETENESS": [("CURATIVE", "근치적 절제(R0)", "Curative resection (R0)"), ("NONCURATIVE", "비근치적 절제(R1/R2)", "Non-curative resection (R1/R2)"), ("UNDETERMINED", "미확정", "Undetermined")],
    "CL_TME_QUALITY": [("COMPLETE", "완전(Grade 3)", "Complete (Grade 3)"), ("NEARLY_COMPLETE", "거의 완전(Grade 2)", "Nearly complete (Grade 2)"), ("INCOMPLETE", "불완전(Grade 1)", "Incomplete (Grade 1)")],
    "CL_INVASION_DEPTH": [  # 대장암 벽 침윤 깊이
        ("TIS", "상피내(Tis)", "In situ (Tis)"), ("T1", "점막하층(T1)", "Submucosa (T1)"), ("T2", "고유근층(T2)", "Muscularis propria (T2)"),
        ("T3", "장막하·주위지방(T3)", "Subserosa/pericolic fat (T3)"), ("T4A", "장측복막(T4a)", "Visceral peritoneum (T4a)"), ("T4B", "주위 장기 침범(T4b)", "Adjacent organ invasion (T4b)"),
    ],
    "CL_PERITONEAL_CYTOLOGY_RESULT": [("POSITIVE", "양성", "Positive"), ("NEGATIVE", "음성", "Negative"), ("INDETERMINATE", "판정 불가·미시행", "Indeterminate/not performed")],
    "CL_STOMA_REASON": [
        ("DIVERTING", "전환·보호 장루", "Diverting/protective stoma"), ("OBSTRUCTION", "장폐색", "Obstruction"),
        ("PERFORATION", "천공", "Perforation"), ("LEAK_PREVENTION", "문합부 누출 예방", "Anastomotic leak prevention"),
        ("PERMANENT", "영구 장루(APR 등)", "Permanent stoma (e.g. APR)"), ("OTHER", "기타", "Other"),
    ],
    "CL_ANASTOMOSIS_METHOD": [("STAPLED", "문합기 사용", "Stapled"), ("HAND_SEWN", "수기 봉합", "Hand-sewn"), ("HYBRID", "문합기+수기 병용", "Stapled + hand-sewn hybrid")],
    "CL_IMA_LIGATION_LEVEL": [("HIGH", "고위 결찰(대동맥 기시부)", "High ligation (at aortic origin)"), ("LOW", "저위 결찰(좌결장동맥 원위부)", "Low ligation (distal to left colic artery)")],
    "CL_WATCH_AND_WAIT_STATUS": [
        ("ONGOING", "경과관찰 중", "On active surveillance"), ("REGROWTH", "국소 재성장", "Local regrowth"),
        ("CONVERTED_SURGERY", "수술로 전환", "Converted to surgery"), ("SUSTAINED_CCR", "지속적 임상완전관해", "Sustained clinical complete response"),
    ],
    # ---------------- 영상
    "CL_IMAGING_DIAGNOSTIC_CLASSIFICATION": [  # BI-RADS(유방) 기준. 폐암에 재사용 시 2.2 에서 Lung-RADS 로 분리 검토
        ("0", "0(추가 영상 필요)", "0 - Incomplete, need additional imaging"), ("1", "1(음성)", "1 - Negative"), ("2", "2(양성 소견)", "2 - Benign"),
        ("3", "3(양성 추정)", "3 - Probably benign"), ("4A", "4A(낮은 악성 의심)", "4A - Low suspicion"), ("4B", "4B(중등도 악성 의심)", "4B - Moderate suspicion"),
        ("4C", "4C(높은 악성 의심)", "4C - High suspicion"), ("5", "5(악성 고도 의심)", "5 - Highly suggestive of malignancy"), ("6", "6(조직검사 확인된 악성)", "6 - Known biopsy-proven malignancy"),
    ],
    "CL_NODULE_RADIOLOGIC_TYPE": [("SOLID", "고형(solid)", "Solid"), ("PART_SOLID", "부분고형(part-solid)", "Part-solid"), ("GGN", "간유리음영(pure GGN)", "Pure ground-glass")],
    "CL_MRI_ANTERIOR_PERITONEAL_RELATION": [("ABOVE", "복막반전부 위", "Above peritoneal reflection"), ("AT", "복막반전부", "At peritoneal reflection"), ("BELOW", "복막반전부 아래", "Below peritoneal reflection")],
    "CL_MRI_CIRCUMFERENTIAL_EXTENT": [("LT25", "<25%", "<25%"), ("25_50", "25~50%", "25-50%"), ("50_75", "50~75%", "50-75%"), ("GT75", ">75%", ">75%"), ("CIRC", "전둘레(360°)", "Circumferential (360°)")],
    "CL_MRI_CIRCUMFERENTIAL_LOCATION": [("ANTERIOR", "전방", "Anterior"), ("POSTERIOR", "후방", "Posterior"), ("LEFT_LAT", "좌측방", "Left lateral"), ("RIGHT_LAT", "우측방", "Right lateral"), ("CIRC", "전둘레", "Circumferential")],
    "CL_MRI_T4B_INVADED_ORGAN": [
        ("PROSTATE", "전립선", "Prostate"), ("SEMINAL_VESICLE", "정낭", "Seminal vesicle"), ("VAGINA", "질", "Vagina"), ("UTERUS", "자궁", "Uterus"),
        ("BLADDER", "방광", "Bladder"), ("PELVIC_SIDEWALL", "골반측벽", "Pelvic sidewall"), ("SACRUM", "천골", "Sacrum"), ("OTHER", "기타 인접 장기", "Other adjacent organ"),
    ],
    "CL_MRI_TUMOR_REGRESSION_GRADE": [  # MERCURY mrTRG
        ("MRTRG1", "mrTRG1(완전반응)", "mrTRG1 - complete response"), ("MRTRG2", "mrTRG2", "mrTRG2"), ("MRTRG3", "mrTRG3", "mrTRG3"),
        ("MRTRG4", "mrTRG4", "mrTRG4"), ("MRTRG5", "mrTRG5(반응 없음)", "mrTRG5 - no response"),
    ],
    # ---------------- 진단·병기 공통
    "CL_DIAGNOSIS_STATUS": [("CONFIRMED", "확진", "Confirmed"), ("SUSPECTED", "의증", "Suspected"), ("RECURRENT", "재발성", "Recurrent"), ("EXCLUDED", "배제됨", "Excluded/ruled out")],
    "CL_DIAGNOSIS_SUBTYPE": [  # 대장암 세부 진단명 (WHO 조직학)
        ("ADENO_NOS", "선암종(NOS)", "Adenocarcinoma, NOS"), ("MUCINOUS", "점액성 선암종", "Mucinous adenocarcinoma"),
        ("SIGNET_RING", "인환세포암종", "Signet ring cell carcinoma"), ("NEUROENDOCRINE", "신경내분비암종", "Neuroendocrine carcinoma"),
        ("SCC", "편평상피세포암종", "Squamous cell carcinoma"), ("OTHER", "기타", "Other"),
    ],
    "CL_LOBULAR_INFLAMMATION_GRADE": [("0", "0(없음)", "0 - none"), ("1", "1(경도, <2 병소/배율시야)", "1 - mild (<2 foci/200x field)"), ("2", "2(중등도, 2~4 병소/배율시야)", "2 - moderate (2-4 foci/200x field)"), ("3", "3(중증, >4 병소/배율시야)", "3 - severe (>4 foci/200x field)")],  # NASH CRN
    "CL_BALLOONING_GRADE": [("0", "0(없음)", "0 - none"), ("1", "1(소수)", "1 - few balloon cells"), ("2", "2(다수/현저)", "2 - many/prominent balloon cells")],  # NASH CRN
    "CL_MASLD_DIAGNOSIS_BASIS": [  # 2023 AASLD/EASL MASLD 명명법 합의
        ("BIOPSY", "간생검 확인", "Liver biopsy confirmed"), ("IMAGING", "영상 지방간 소견 + 심장대사 위험인자", "Imaging steatosis + cardiometabolic risk factor"),
        ("LFT_RISK", "간효소 상승 + 위험인자", "Elevated liver enzymes with risk factors"), ("SCORE", "비침습 점수 기반(FIB-4/NFS 등)", "Non-invasive score-based (FIB-4/NFS etc.)"),
    ],
    "CL_LYMPHOMA_CATEGORY": [("HL", "호지킨림프종", "Hodgkin lymphoma"), ("NHL_B", "비호지킨림프종-B세포", "Non-Hodgkin lymphoma, B-cell"), ("NHL_T", "비호지킨림프종-T/NK세포", "Non-Hodgkin lymphoma, T/NK-cell")],
    "CL_CELL_LINEAGE": [("B_CELL", "B세포", "B-cell"), ("T_CELL", "T세포", "T-cell"), ("NK_CELL", "NK세포", "NK-cell"), ("HRS", "호지킨/리드-스턴버그세포", "Hodgkin/Reed-Sternberg cell"), ("UNCERTAIN", "불명확·혼합", "Uncertain/mixed")],
    "CL_HISTOLOGIC_SUBTYPE": [  # WHO/ICC 림프종 아형(대표)
        ("DLBCL", "미만성 거대B세포림프종(DLBCL, NOS)", "Diffuse large B-cell lymphoma, NOS"), ("FL", "여포림프종", "Follicular lymphoma"),
        ("MCL", "외투세포림프종", "Mantle cell lymphoma"), ("MZL", "변연부림프종", "Marginal zone lymphoma"), ("BL", "버킷림프종", "Burkitt lymphoma"),
        ("CHL", "고전적 호지킨림프종", "Classic Hodgkin lymphoma"), ("NLPHL", "결절성 림프구우세형 호지킨림프종", "Nodular lymphocyte-predominant Hodgkin lymphoma"),
        ("PTCL_NOS", "말초T세포림프종(NOS)", "Peripheral T-cell lymphoma, NOS"), ("ALCL", "역형성대세포림프종", "Anaplastic large cell lymphoma"),
        ("NKTCL", "비강형 NK/T세포림프종", "Extranodal NK/T-cell lymphoma, nasal type"), ("OTHER", "기타·미분류", "Other/not otherwise specified"),
    ],
    "CL_PRIMARY_SITE": [("RUL", "우상엽", "Right upper lobe"), ("RML", "우중엽", "Right middle lobe"), ("RLL", "우하엽", "Right lower lobe"), ("LUL", "좌상엽", "Left upper lobe"), ("LLL", "좌하엽", "Left lower lobe"), ("MAIN_BRONCHUS", "주기관지", "Main bronchus"), ("OVERLAPPING", "중복 병변", "Overlapping lesion"), ("UNSPECIFIED", "불명확", "Unspecified")],
    "CL_PRIMARY_SIDEDNESS": [("RIGHT", "우측(맹장~횡행결장)", "Right-sided (cecum to transverse colon)"), ("LEFT", "좌측(비만곡부~S상결장)", "Left-sided (splenic flexure to sigmoid)"), ("RECTUM", "직장", "Rectum"), ("MULTIPLE", "다발성·양측성", "Multiple/synchronous")],
    "CL_PRIMARY_INVOLVED_SITE": [
        ("NODAL", "림프절(말초)", "Nodal, peripheral"), ("MEDIASTINAL", "종격동", "Mediastinal"), ("WALDEYER", "발다이어고리", "Waldeyer's ring"),
        ("EXTRANODAL_GI", "결절외-위장관", "Extranodal - GI tract"), ("EXTRANODAL_SKIN", "결절외-피부", "Extranodal - skin"),
        ("EXTRANODAL_CNS", "결절외-중추신경계", "Extranodal - CNS"), ("EXTRANODAL_BONE", "결절외-골", "Extranodal - bone"), ("EXTRANODAL_OTHER", "결절외-기타", "Extranodal - other"),
    ],
    "CL_CLINICAL_TUMOR_FEATURE": [
        ("PALPABLE", "촉지되는 종괴", "Palpable mass"), ("NONPALPABLE", "비촉지(영상 발견)", "Non-palpable (imaging detected)"),
        ("SKIN_INVOLVEMENT", "피부·흉벽 침범", "Skin/chest wall involvement"), ("INFLAMMATORY", "염증성 소견", "Inflammatory features"),
        ("OBSTRUCTION", "폐색", "Obstruction"), ("PERFORATION", "천공", "Perforation"), ("BLEEDING", "출혈", "Bleeding"), ("INCIDENTAL", "무증상·우연 발견", "Asymptomatic/incidental"),
    ],
    "CL_DISTANT_METASTASIS_SITE": [("LIVER", "간", "Liver"), ("LUNG", "폐", "Lung"), ("BONE", "골", "Bone"), ("BRAIN", "뇌", "Brain"), ("ADRENAL", "부신", "Adrenal gland"), ("PERITONEUM", "복막", "Peritoneum"), ("DISTANT_NODE", "원격 림프절", "Distant lymph node"), ("OTHER", "기타", "Other")],
    "CL_EXTRANODAL_SITES": [("GI", "위장관", "GI tract"), ("BONE_MARROW", "골수", "Bone marrow"), ("CNS", "중추신경계", "CNS"), ("SKIN", "피부", "Skin"), ("LUNG", "폐", "Lung"), ("LIVER", "간", "Liver"), ("BONE", "골", "Bone"), ("TESTIS", "고환", "Testis"), ("OTHER", "기타", "Other")],
    "CL_STAGING_METHOD": [
        ("CLINICAL", "임상적(진찰·영상)", "Clinical (exam/imaging)"), ("PATHOLOGIC", "병리적(수술 후)", "Pathologic (post-surgical)"),
        ("PET_CT", "PET-CT 기반", "PET-CT based"), ("BONE_MARROW", "골수생검 기반", "Bone marrow biopsy-based"), ("COMBINED", "임상+병리 병합", "Combined clinical + pathologic"),
    ],
    # ---------------- 생식·산과 (유방암)
    "CL_CONCEPTION_METHOD": [("NATURAL", "자연 임신", "Natural conception"), ("IVF", "체외수정(IVF)", "In vitro fertilization"), ("IUI", "자궁내 인공수정(IUI)", "Intrauterine insemination"), ("OTHER_ART", "기타 보조생식술", "Other assisted reproduction")],
    "CL_PREGNANCY_OUTCOME": [("LIVE_BIRTH", "출산(생존아)", "Live birth"), ("STILLBIRTH", "사산", "Stillbirth"), ("MISCARRIAGE", "자연유산", "Spontaneous abortion"), ("INDUCED_ABORTION", "인공유산", "Induced abortion"), ("ECTOPIC", "자궁외임신", "Ectopic pregnancy"), ("ONGOING", "임신 중", "Ongoing pregnancy")],
    "CL_FERTILITY_PRESERVATION_TYPE": [("OOCYTE", "난자 동결보존", "Oocyte cryopreservation"), ("EMBRYO", "배아 동결보존", "Embryo cryopreservation"), ("OVARIAN_TISSUE", "난소조직 동결보존", "Ovarian tissue cryopreservation"), ("GNRH_AGONIST", "GnRH 작용제 난소기능 억제", "GnRH agonist ovarian suppression"), ("OTHER", "기타", "Other")],
    "CL_MENOPAUSAL_STATUS_AT_DIAGNOSIS": [("PRE", "폐경 전", "Premenopausal"), ("PERI", "폐경이행기", "Perimenopausal"), ("POST", "폐경 후", "Postmenopausal"), ("UNKNOWN", "미확인", "Unknown/not assessed")],
    "CL_MENSES_REGULARITY_AFTER_CHEMO": [("REGULAR", "규칙적", "Regular"), ("IRREGULAR", "불규칙적", "Irregular"), ("AMENORRHEA", "무월경", "Amenorrhea")],
    "CL_MARITAL_STATUS_DETAIL": [("NEVER_MARRIED", "미혼", "Never married"), ("MARRIED", "기혼", "Married"), ("DIVORCED", "이혼", "Divorced"), ("WIDOWED", "사별", "Widowed"), ("SEPARATED", "별거", "Separated"), ("OTHER", "기타·동거 등", "Cohabiting/other")],
    # ---------------- 이상사례
    "CL_COMPLICATION_TREATMENT": [
        ("OBSERVATION", "보존적 관찰", "Conservative/observation"), ("MEDICAL", "약물 치료", "Medical management"),
        ("ENDOSCOPIC", "내시경적 시술", "Endoscopic intervention"), ("REOPERATION", "재수술", "Reoperation/surgical intervention"), ("DRAINAGE", "경피적 배액", "Percutaneous drainage"),
    ],
    "CL_ACTION_TAKEN_CONCEPT_ID": [  # ICH E2B 조치 범주
        ("NO_CHANGE", "용량 변경 없음", "Dose not changed"), ("REDUCED", "용량 감량", "Dose reduced"), ("INTERRUPTED", "투여 중단(일시)", "Dose interrupted/withheld"),
        ("WITHDRAWN", "투여 영구 중단", "Drug withdrawn permanently"), ("DELAYED", "치료 연기", "Treatment delayed"), ("NA", "해당없음", "Not applicable"),
    ],
    "CL_OUTCOME_CONCEPT_ID": [  # ICH E2B 결과 범주
        ("RECOVERED", "회복", "Recovered/resolved"), ("RECOVERED_SEQUELAE", "후유증 동반 회복", "Recovered with sequelae"),
        ("NOT_RECOVERED", "미회복·진행중", "Not recovered/ongoing"), ("FATAL", "사망", "Fatal"), ("UNKNOWN", "불명", "Unknown"),
    ],
    "CL_ADVERSE_EVENT_TYPE_CONCEPT_ID": [  # 기록 출처 유형 (TYPE_REGISTRY/TYPE_EHR/TYPE_DERIVED 씨앗과 동일한 뜻)
        ("REGISTRY", "등록 서식 입력", "Registry (CRF entry)"), ("EHR", "전자의무기록", "EHR"), ("DERIVED", "파생", "Derived"),
    ],
}
# 예/아니오(is_serious) 는 새 값을 만들지 않고 기존 YN 값 집합을 그대로 가리킨다.
ALIAS_CODELIST = {"CL_IS_SERIOUS": "YN"}

# ================================================================ SNOMED CT 매핑 (MCP 용어 서버로 확인된 값만)
# key: (codelist_id, code) -> (SNOMED concept_id, SNOMED 계층=semantic tag).
# 계층을 함께 적는 이유: OMOP domain 은 값이 '무엇인가'에 따라 정해지는데, 그 판단 근거가 계층이다.
# build_spec_v2.py 의 SNOMED_TAG_DOMAIN 이 계층 -> domain 을 맡는다. 새 매핑을 넣을 때 계층을
# 빠뜨리거나 모르는 값을 쓰면 빌드가 경고를 낸다.
# 2026-09-12 세션에서 snowstorm MCP(https://snomedbrowser.org/snowstorm/snomed-ct, 편집판 snomedct/MAIN)로
# 항목별 검색(snowstorm_search_concepts)을 돌려 FSN·활성 여부를 눈으로 확인한 값만 넣는다.
# build_spec_v2.py 가 여기 있는 값의 vocabulary 를 KAI -> SNOMED 로 승격한다.
SNOMED_CODES = {
    # ---- COMORBIDITY_SET (과거력 진단 20종). 괄호 안은 확인한 FSN.
    ("COMORBIDITY_SET", "HTN"): ("38341003", "disorder"),                  # Hypertensive disorder, systemic arterial (disorder)
    ("COMORBIDITY_SET", "T2DM"): ("44054006", "disorder"),                 # Diabetes mellitus type 2 (disorder)
    ("COMORBIDITY_SET", "DYSLIPIDEMIA"): ("55822004", "disorder"),         # Hyperlipidemia (disorder)
    ("COMORBIDITY_SET", "CVD"): ("414545008", "disorder"),                 # Ischemic heart disease (disorder)
    ("COMORBIDITY_SET", "CEREBROVASCULAR"): ("62914000", "disorder"),      # Cerebrovascular disease (disorder)
    ("COMORBIDITY_SET", "CKD"): ("709044004", "disorder"),                 # Chronic kidney disease (disorder)
    ("COMORBIDITY_SET", "PANCREATIC"): ("3855007", "disorder"),            # Disorder of pancreas (disorder)
    ("COMORBIDITY_SET", "HBV"): ("61977001", "disorder"),                  # Chronic type B viral hepatitis (disorder)
    ("COMORBIDITY_SET", "HCV"): ("128302006", "disorder"),                 # Chronic hepatitis C (disorder)
    ("COMORBIDITY_SET", "HIV"): ("86406008", "disorder"),                  # Human immunodeficiency virus infection (disorder)
    ("COMORBIDITY_SET", "TB"): ("56717001", "disorder"),                   # Tuberculosis (disorder)
    ("COMORBIDITY_SET", "HEART_DISEASE"): ("56265001", "disorder"),        # Heart disease (disorder) — CVD(허혈성)보다 상위 개념
    ("COMORBIDITY_SET", "OTHER_RESPIRATORY"): ("50043002", "disorder"),    # Disorder of respiratory system (disorder)
    ("COMORBIDITY_SET", "COLORECTAL_DISEASE"): ("128524007", "disorder"),  # Disorder of colon (disorder)
    ("COMORBIDITY_SET", "KIDNEY_DISEASE"): ("90708001", "disorder"),       # Kidney disease (disorder) — CKD 를 포함하는 상위 개념
    ("COMORBIDITY_SET", "LIVER_DISEASE"): ("235856003", "disorder"),       # Disorder of liver (disorder)
    ("COMORBIDITY_SET", "HYPOTHYROIDISM"): ("40930008", "disorder"),       # Hypothyroidism (disorder)
    ("COMORBIDITY_SET", "BARIATRIC_SURGERY_HX"): ("608848006", "situation"),  # History of bariatric surgical procedure (situation)
    ("COMORBIDITY_SET", "HEREDITARY_CRC"): ("315058005", "disorder"),      # Hereditary nonpolyposis colon cancer (disorder)
    ("COMORBIDITY_SET", "CANCER_HX"): ("266987004", "situation"),           # History of malignant neoplasm (situation)
    # ---- 해부학 부위 (body structure). 폐엽·대장 분절은 여러 코드표가 같은 concept 을 공유한다.
    #      폐: <<39607008 |Lung structure| 를 ECL 로 펼쳐 "lobe of lung" 으로 걸러 확인.
    ("CL_PRIMARY_SITE", "RUL"): ("42400003", "body structure"),                  # Structure of upper lobe of right lung
    ("CL_PRIMARY_SITE", "RML"): ("72481006", "body structure"),                  # Structure of middle lobe of right lung
    ("CL_PRIMARY_SITE", "RLL"): ("266005", "body structure"),                    # Structure of lower lobe of right lung
    ("CL_PRIMARY_SITE", "LUL"): ("44714003", "body structure"),                  # Structure of upper lobe of left lung
    ("CL_PRIMARY_SITE", "LLL"): ("41224006", "body structure"),                  # Structure of lower lobe of left lung
    ("CL_PRIMARY_SITE", "MAIN_BRONCHUS"): ("102297006", "body structure"),       # Main bronchus structure
    # OVERLAPPING·UNSPECIFIED 는 부위가 아니라 기재 상태라 KAI 코드로 남긴다.

    #      대장: <<245425000 |Region of colon| 를 펼쳐 분절 concept 을 확인(맹장·직장은 이 하위가 아니라 따로 조회).
    ("CL_BIOPSY_SITE_DETAIL", "RUL"): ("42400003", "body structure"),            # Structure of upper lobe of right lung
    ("CL_BIOPSY_SITE_DETAIL", "RML"): ("72481006", "body structure"),            # Structure of middle lobe of right lung
    ("CL_BIOPSY_SITE_DETAIL", "RLL"): ("266005", "body structure"),              # Structure of lower lobe of right lung
    ("CL_BIOPSY_SITE_DETAIL", "LUL"): ("44714003", "body structure"),            # Structure of upper lobe of left lung
    ("CL_BIOPSY_SITE_DETAIL", "LLL"): ("41224006", "body structure"),            # Structure of lower lobe of left lung
    ("CL_BIOPSY_SITE_DETAIL", "CECUM"): ("32713005", "body structure"),          # Cecum structure
    ("CL_BIOPSY_SITE_DETAIL", "ASC_COLON"): ("9040008", "body structure"),       # Ascending colon structure
    ("CL_BIOPSY_SITE_DETAIL", "HEP_FLEX"): ("48338005", "body structure"),       # Structure of right colic flexure (간만곡부)
    ("CL_BIOPSY_SITE_DETAIL", "TRANS_COLON"): ("485005", "body structure"),      # Transverse colon structure
    ("CL_BIOPSY_SITE_DETAIL", "SPL_FLEX"): ("72592005", "body structure"),       # Structure of left colic flexure (비만곡부)
    ("CL_BIOPSY_SITE_DETAIL", "DESC_COLON"): ("32622004", "body structure"),     # Descending colon structure
    ("CL_BIOPSY_SITE_DETAIL", "SIGMOID"): ("60184004", "body structure"),        # Sigmoid colon structure
    ("CL_BIOPSY_SITE_DETAIL", "RECTUM"): ("34402009", "body structure"),         # Rectum structure

    ("CL_DISTANT_METASTASIS_SITE", "LIVER"): ("10200004", "body structure"),     # Liver structure
    ("CL_DISTANT_METASTASIS_SITE", "LUNG"): ("39607008", "body structure"),      # Lung structure
    ("CL_DISTANT_METASTASIS_SITE", "BONE"): ("272673000", "body structure"),     # Bone structure
    ("CL_DISTANT_METASTASIS_SITE", "BRAIN"): ("12738006", "body structure"),     # Brain structure
    ("CL_DISTANT_METASTASIS_SITE", "ADRENAL"): ("23451007", "body structure"),   # Adrenal structure
    ("CL_DISTANT_METASTASIS_SITE", "PERITONEUM"): ("15425007", "body structure"),  # Structure of serous membrane of peritoneum
    ("CL_DISTANT_METASTASIS_SITE", "DISTANT_NODE"): ("59441001", "body structure"),  # Structure of lymph node — "원격"은 부위 concept 에 담기지 않는다(주 참조)

    ("CL_EXTRANODAL_SITES", "GI"): ("122865005", "body structure"),              # Gastrointestinal tract structure
    ("CL_EXTRANODAL_SITES", "BONE_MARROW"): ("14016003", "body structure"),      # Bone marrow structure
    ("CL_EXTRANODAL_SITES", "CNS"): ("21483005", "body structure"),              # Structure of central nervous system
    ("CL_EXTRANODAL_SITES", "SKIN"): ("39937001", "body structure"),             # Skin structure
    ("CL_EXTRANODAL_SITES", "LUNG"): ("39607008", "body structure"),             # Lung structure
    ("CL_EXTRANODAL_SITES", "LIVER"): ("10200004", "body structure"),            # Liver structure
    ("CL_EXTRANODAL_SITES", "BONE"): ("272673000", "body structure"),            # Bone structure
    ("CL_EXTRANODAL_SITES", "TESTIS"): ("40689003", "body structure"),           # Testis structure

    ("CL_PRIMARY_INVOLVED_SITE", "NODAL"): ("59441001", "body structure"),       # Structure of lymph node
    ("CL_PRIMARY_INVOLVED_SITE", "MEDIASTINAL"): ("72410000", "body structure"),  # Mediastinal structure
    ("CL_PRIMARY_INVOLVED_SITE", "WALDEYER"): ("17861009", "body structure"),    # Structure of pharyngeal lymphoid ring (발다이어고리)
    ("CL_PRIMARY_INVOLVED_SITE", "EXTRANODAL_GI"): ("122865005", "body structure"),   # Gastrointestinal tract structure
    ("CL_PRIMARY_INVOLVED_SITE", "EXTRANODAL_SKIN"): ("39937001", "body structure"),  # Skin structure
    ("CL_PRIMARY_INVOLVED_SITE", "EXTRANODAL_CNS"): ("21483005", "body structure"),   # Structure of central nervous system
    ("CL_PRIMARY_INVOLVED_SITE", "EXTRANODAL_BONE"): ("272673000", "body structure"),  # Bone structure

    # ---- 측성 (qualifier value). 두 코드표가 같은 값을 쓴다.
    ("CL_BIOPSY_LATERALITY", "RIGHT"): ("24028007", "qualifier value"),           # Right (qualifier value)
    ("CL_BIOPSY_LATERALITY", "LEFT"): ("7771000", "qualifier value"),             # Left (qualifier value)
    ("CL_BIOPSY_LATERALITY", "BILATERAL"): ("51440002", "qualifier value"),       # Right and left (qualifier value) — 동의어 Bilateral
    ("CL_BIOPSY_LATERALITY", "NA"): ("385432009", "qualifier value"),             # Not applicable (qualifier value)
    ("CL_SURGICAL_SPECIMEN_LATERALITY", "RIGHT"): ("24028007", "qualifier value"),
    ("CL_SURGICAL_SPECIMEN_LATERALITY", "LEFT"): ("7771000", "qualifier value"),
    ("CL_SURGICAL_SPECIMEN_LATERALITY", "BILATERAL"): ("51440002", "qualifier value"),
    ("CL_SURGICAL_SPECIMEN_LATERALITY", "NA"): ("385432009", "qualifier value"),

    # ---- 생검 방법 (procedure). <<86273004 |Biopsy| 를 ECL 로 펼쳐 방법별로 확인.
    ("CL_BIOPSY_METHOD", "CORE"): ("9911007", "procedure"),                 # Core needle biopsy
    ("CL_BIOPSY_METHOD", "FNA"): ("48635004", "procedure"),                 # Fine needle biopsy (동의어 Fine needle aspiration)
    ("CL_BIOPSY_METHOD", "EXCISION"): ("8889005", "procedure"),             # Excisional biopsy
    ("CL_BIOPSY_METHOD", "INCISION"): ("70871006", "procedure"),            # Incisional biopsy
    ("CL_BIOPSY_METHOD", "PUNCH"): ("68660007", "procedure"),               # Punch biopsy
    ("CL_BIOPSY_METHOD", "ENDOSCOPIC"): ("53767003", "procedure"),          # Endoscopic biopsy
    ("CL_BIOPSY_METHOD", "EBUS"): ("1389225003", "procedure"),              # Transbronchial needle aspiration biopsy using endobronchial ultrasound guidance
    ("CL_BIOPSY_METHOD", "VACUUM"): ("786883001", "procedure"),             # Vacuum assisted biopsy
    ("CL_BIOPSY_METHOD", "SURGICAL"): ("119283008", "procedure"),           # Open biopsy — "수술적 생검"에 가장 가까운 상위 개념
    # IMAGE_GUIDED: SNOMED 의 영상유도 생검은 전부 방법·부위가 붙은 하위 개념뿐이고
    # (예: 442787002 은 세침흡인 전용) 부위 없는 일반 개념이 없어 KAI 로 남긴다.

    # ---- 검체 적정성 (finding)
    ("CL_BIOPSY_ADEQUACY", "ADEQUATE"): ("125152006", "finding"),         # Specimen satisfactory for evaluation
    ("CL_BIOPSY_ADEQUACY", "INADEQUATE"): ("125154007", "finding"),       # Specimen unsatisfactory for evaluation
    ("CL_BIOPSY_ADEQUACY", "NONDIAGNOSTIC"): ("112631006", "finding"),    # Specimen unsatisfactory for diagnosis

    # ---- 조직학적 분화도 (qualifier value). 두 코드표가 같은 G1~G4 를 쓴다. GX(평가 불가)는 행정값이라 KAI.
    ("CL_BIOPSY_DIFFERENTIATION", "WD"): ("1155701009", "qualifier value"),       # G1: Well differentiated histologic grade
    ("CL_BIOPSY_DIFFERENTIATION", "MD"): ("1155703007", "qualifier value"),       # G2: Moderately differentiated histologic grade
    ("CL_BIOPSY_DIFFERENTIATION", "PD"): ("1155704001", "qualifier value"),       # G3: Poorly differentiated histologic grade
    ("CL_BIOPSY_DIFFERENTIATION", "UD"): ("1155702002", "qualifier value"),       # G4: Undifferentiated histologic grade
    ("CL_SURGICAL_HISTOLOGIC_GRADE", "G1"): ("1155701009", "qualifier value"),
    ("CL_SURGICAL_HISTOLOGIC_GRADE", "G2"): ("1155703007", "qualifier value"),
    ("CL_SURGICAL_HISTOLOGIC_GRADE", "G3"): ("1155704001", "qualifier value"),
    ("CL_SURGICAL_HISTOLOGIC_GRADE", "G4"): ("1155702002", "qualifier value"),

    # ---- 조직형 (morphologic abnormality). 팀 결정: 아형 필드는 진단명(disorder)이 아니라
    #      조직형 계층을 쓴다(OMOP Oncology 의 ICD-O-3 조직형과 결이 맞다). <<108369006 |Neoplasm| 하위에서 확인.
    ("CL_DIAGNOSIS_SUBTYPE", "ADENO_NOS"): ("1187332001", "morphologic abnormality"),     # Adenocarcinoma
    ("CL_DIAGNOSIS_SUBTYPE", "MUCINOUS"): ("72495009", "morphologic abnormality"),        # Mucinous adenocarcinoma
    ("CL_DIAGNOSIS_SUBTYPE", "SIGNET_RING"): ("87737001", "morphologic abnormality"),     # Signet ring cell carcinoma
    ("CL_DIAGNOSIS_SUBTYPE", "NEUROENDOCRINE"): ("1286767006", "morphologic abnormality"),  # Neuroendocrine carcinoma
    ("CL_DIAGNOSIS_SUBTYPE", "SCC"): ("1162767002", "morphologic abnormality"),           # Squamous cell carcinoma

    ("CL_HISTOLOGIC_SUBTYPE", "DLBCL"): ("1172695008", "morphologic abnormality"),        # Diffuse large B cell lymphoma
    ("CL_HISTOLOGIC_SUBTYPE", "FL"): ("55150002", "morphologic abnormality"),             # Follicular lymphoma
    ("CL_HISTOLOGIC_SUBTYPE", "MCL"): ("74654000", "morphologic abnormality"),            # Malignant mantle cell lymphoma
    ("CL_HISTOLOGIC_SUBTYPE", "MZL"): ("128803008", "morphologic abnormality"),           # Marginal zone B-cell lymphoma
    ("CL_HISTOLOGIC_SUBTYPE", "BL"): ("77381001", "morphologic abnormality"),             # Burkitt lymphoma
    ("CL_HISTOLOGIC_SUBTYPE", "CHL"): ("762691001", "morphologic abnormality"),           # Classical Hodgkin lymphoma
    ("CL_HISTOLOGIC_SUBTYPE", "PTCL_NOS"): ("1163404000", "morphologic abnormality"),     # Peripheral T-cell lymphoma
    ("CL_HISTOLOGIC_SUBTYPE", "ALCL"): ("53237008", "morphologic abnormality"),           # Anaplastic large cell lymphoma, T cell and null cell type
    ("CL_HISTOLOGIC_SUBTYPE", "NKTCL"): ("128805001", "morphologic abnormality"),         # NK/T-cell lymphoma, nasal and nasal-type
    # NLPHL(결절성 림프구우세형): 조직형 계층에 개념이 없다(disorder 만 존재) — 계층을 섞지 않으려고 KAI 로 남긴다.

    ("CL_LYMPHOMA_CATEGORY", "HL"): ("1163005009", "morphologic abnormality"),            # Hodgkin lymphoma
    # NHL_B·NHL_T: 조직형 계층의 Non-Hodgkin lymphoma(1172592001)는 B/T 를 나누지 않아 두 값이 한 concept 에
    # 뭉친다. 계열은 CL_CELL_LINEAGE 로 따로 받으므로 여기서는 KAI 로 남긴다.

    # ---- 폐선암 우세 아형 (IASLC/WHO). "우세 아형"은 패턴 우세도라 SNOMED 에 그대로 대응하는 개념이 적다.
    ("CL_ADENOCARCINOMA_PREDOMINANT_SUBTYPE", "PAPILLARY"): ("4797003", "morphologic abnormality"),       # Papillary adenocarcinoma
    ("CL_ADENOCARCINOMA_PREDOMINANT_SUBTYPE", "MICROPAPILLARY"): ("733878002", "morphologic abnormality"),  # Micropapillary adenocarcinoma
    ("CL_ADENOCARCINOMA_PREDOMINANT_SUBTYPE", "MUCINOUS"): ("72495009", "morphologic abnormality"),      # Mucinous adenocarcinoma
    ("CL_ADENOCARCINOMA_PREDOMINANT_SUBTYPE", "FETAL"): ("128893004", "morphologic abnormality"),        # Fetal adenocarcinoma
    # LEPIDIC·ENTERIC: 조직형 계층에 개념이 없다.
    # ACINAR: 검색되는 Acinar cell carcinoma(45410002)는 췌장·타액선 종양이라 폐 선방형과 다른 개체다.
    # SOLID: Solid carcinoma(81920005)는 부위 불문 일반 개념이라 "고형 우세 선암"과 범위가 다르다.
    # COLLOID: SNOMED 이 colloid 를 Mucinous adenocarcinoma 의 동의어로 두어 MUCINOUS 와 한 코드에 뭉친다.
    # 넷 다 뜻이 어긋나거나 값끼리 충돌해 KAI 로 남긴다.

    # ---- 절제연
    ("CL_CRM_STATUS", "POSITIVE"): ("384620009", "finding"),              # Surgical circumferential margin involved by malignant neoplasm (0-1 mm) — 값 정의(≤1mm)와 일치
    # CRM NEGATIVE: "침범 없음"에 해당하는 개념이 없다(침범 concept 만 존재).
    # CL_RESECTION_MARGIN_STATUS·CL_RESIDUAL_TUMOR_R_CLASS 의 R0/R1/R2: SNOMED 의 절제연 개념
    # (384689007 등)은 침범 여부만 말하고 현미경적/육안적을 나누지 않아 R1 과 R2 가 한 코드에 뭉친다.
    # AJCC R 분류는 코드 자체가 표준이므로 KAI 로 유지한다.

    # ---- 직장암 MRI T4b 침범 장기 (body structure)
    ("CL_MRI_T4B_INVADED_ORGAN", "PROSTATE"): ("41216001", "body structure"),        # Structure of prostate
    ("CL_MRI_T4B_INVADED_ORGAN", "SEMINAL_VESICLE"): ("64739004", "body structure"),  # Seminal vesicle structure
    ("CL_MRI_T4B_INVADED_ORGAN", "VAGINA"): ("76784001", "body structure"),          # Vaginal structure
    ("CL_MRI_T4B_INVADED_ORGAN", "UTERUS"): ("35039007", "body structure"),          # Uterine structure
    ("CL_MRI_T4B_INVADED_ORGAN", "BLADDER"): ("89837001", "body structure"),         # Urinary bladder structure
    ("CL_MRI_T4B_INVADED_ORGAN", "SACRUM"): ("54735007", "body structure"),          # Bone structure of sacrum
    # PELVIC_SIDEWALL(골반측벽): 골반강·복막강 개념만 있고 "측벽" 자체를 가리키는 부위 concept 이 없다.

    # ---- 결절 영상 유형
    ("CL_NODULE_RADIOLOGIC_TYPE", "GGN"): ("1217294009", "finding"),          # Ground glass lung opacity
    # SOLID·PART_SOLID: 결절의 고형 성분 정도를 말하는 개념이 없다(간유리음영만 있다).

    # ---- 폐경 상태 (finding)
    ("CL_MENOPAUSAL_STATUS_AT_DIAGNOSIS", "PRE"): ("22636003", "finding"),    # Premenopausal state
    ("CL_MENOPAUSAL_STATUS_AT_DIAGNOSIS", "PERI"): ("161541000119104", "finding"),  # Perimenopausal state
    ("CL_MENOPAUSAL_STATUS_AT_DIAGNOSIS", "POST"): ("76498008", "finding"),   # Postmenopausal state

    # ---- 항암 후 월경 (finding)
    ("CL_MENSES_REGULARITY_AFTER_CHEMO", "IRREGULAR"): ("80182007", "finding"),  # Irregular periods
    ("CL_MENSES_REGULARITY_AFTER_CHEMO", "AMENORRHEA"): ("14302001", "finding"),  # Amenorrhea
    # REGULAR: 검색되는 248965005 는 "월경 규칙성 소견"이라는 상위 개념이지 "규칙적"이라는 값이 아니다.

    # ---- 임신 결과
    ("CL_PREGNANCY_OUTCOME", "LIVE_BIRTH"): ("281050002", "finding"),         # Livebirth
    ("CL_PREGNANCY_OUTCOME", "STILLBIRTH"): ("237364002", "finding"),         # Stillbirth
    ("CL_PREGNANCY_OUTCOME", "MISCARRIAGE"): ("17369002", "disorder"),         # Miscarriage (동의어 Spontaneous abortion)
    ("CL_PREGNANCY_OUTCOME", "INDUCED_ABORTION"): ("57797005", "disorder"),    # Induced termination of pregnancy
    ("CL_PREGNANCY_OUTCOME", "ECTOPIC"): ("34801009", "disorder"),             # Ectopic pregnancy
    ("CL_PREGNANCY_OUTCOME", "ONGOING"): ("77386006", "finding"),             # Pregnancy

    # ---- 수정 방법 (procedure)
    ("CL_CONCEPTION_METHOD", "IVF"): ("52637005", "procedure"),                 # Test tube ovum fertilization
    ("CL_CONCEPTION_METHOD", "IUI"): ("265064001", "procedure"),                # Intrauterine artificial insemination
    # NATURAL: 후보가 1300203003 "자연 수정으로 생긴 임신"(finding)뿐이라 시술(procedure)인 다른 값들과
    # 의미 층이 어긋난다. 한 코드표에 finding 과 procedure 를 섞지 않으려고 KAI 로 남긴다.

    # ---- 가임력 보존 (procedure)
    ("CL_FERTILITY_PRESERVATION_TYPE", "OOCYTE"): ("440645004", "procedure"),   # Cryopreservation of oocyte
    ("CL_FERTILITY_PRESERVATION_TYPE", "OVARIAN_TISSUE"): ("439790009", "procedure"),  # Cryopreservation of ovarian tissue
    # EMBRYO(배아 동결보존): 개념이 없다. GNRH_AGONIST 는 시술이 아니라 약물 요법이라 약물 계열로 받는다.

    # ---- 혼인 상태 (finding)
    ("CL_MARITAL_STATUS_DETAIL", "NEVER_MARRIED"): ("125725006", "finding"),  # Marital status: single, never married
    ("CL_MARITAL_STATUS_DETAIL", "MARRIED"): ("87915002", "finding"),         # Married
    ("CL_MARITAL_STATUS_DETAIL", "DIVORCED"): ("20295000", "finding"),        # Divorced
    ("CL_MARITAL_STATUS_DETAIL", "WIDOWED"): ("33553000", "finding"),         # Widowed
    # SEPARATED(별거): 후보가 430617007 "가집행 판결에 의한 법적 별거"뿐이라 사실상의 별거까지 담는
    # 우리 값보다 좁다.

    # ---- 세포 계열 (cell)
    ("CL_CELL_LINEAGE", "B_CELL"): ("112130006", "cell"),                  # B lymphocyte
    ("CL_CELL_LINEAGE", "T_CELL"): ("57184004", "cell"),                   # T lymphocyte
    ("CL_CELL_LINEAGE", "NK_CELL"): ("259717003", "cell"),                 # Natural killer cell
    ("CL_CELL_LINEAGE", "HRS"): ("32915009", "cell"),                      # Reed-Sternberg cell

    # ---- 진단 상태 (qualifier value). 셋 다 <<36692007 |Known| 계열이라 층이 일관된다.
    ("CL_DIAGNOSIS_STATUS", "CONFIRMED"): ("410605003", "qualifier value"),           # Confirmed present
    ("CL_DIAGNOSIS_STATUS", "SUSPECTED"): ("415684004", "qualifier value"),           # Suspected
    ("CL_DIAGNOSIS_STATUS", "EXCLUDED"): ("410516002", "qualifier value"),            # Known absent
    # RECURRENT(재발성): 후보 58184002 는 qualifier 가 아니라 disorder 라 위 셋과 층이 다르다.

    # ---- 임상 종양 소견. 이 코드표는 한 축의 열거가 아니라 여러 종류의 임상 양상을 모은 것이라
    #      finding 과 disorder 가 섞이는 것이 값의 성격 자체다(수정 방법처럼 한 축을 재는 경우와 다르다).
    ("CL_CLINICAL_TUMOR_FEATURE", "PALPABLE"): ("443607001", "finding"),      # Palpable mass (finding)
    ("CL_CLINICAL_TUMOR_FEATURE", "INFLAMMATORY"): ("254840009", "disorder"),  # Inflammatory carcinoma of breast (disorder)
    ("CL_CLINICAL_TUMOR_FEATURE", "OBSTRUCTION"): ("81060008", "disorder"),    # Intestinal obstruction (disorder)
    ("CL_CLINICAL_TUMOR_FEATURE", "PERFORATION"): ("56905009", "disorder"),    # Perforation of intestine (disorder)
    ("CL_CLINICAL_TUMOR_FEATURE", "BLEEDING"): ("74474003", "disorder"),       # Gastrointestinal hemorrhage (disorder)
    # NONPALPABLE(비촉지)·SKIN_INVOLVEMENT(피부·흉벽 침범): 대응 개념이 없다.
    # INCIDENTAL(우연 발견): 검색되는 것이 전립선 전용 소견뿐이다.

    # ---- 합병증 처치 (procedure)
    ("CL_COMPLICATION_TREATMENT", "MEDICAL"): ("416608005", "procedure"),       # Drug therapy
    ("CL_COMPLICATION_TREATMENT", "ENDOSCOPIC"): ("363687006", "procedure"),    # Endoscopic procedure
    # DRAINAGE: 경피적 배액은 부위별 개념(간·복수·담낭…)만 있고 부위 없는 일반 개념이 없다.
    # REOPERATION: 후보 261554009 는 procedure 가 아니라 qualifier value 라 나머지와 층이 어긋난다.
    # OBSERVATION(보존적 관찰): 대응 개념이 없다.

    # ---- DCIS 핵등급 (finding). 유방 DCIS 전용 개념이 세 등급 모두 있다.
    ("CL_DCIS_NUCLEAR_GRADE", "LOW"): ("369781009", "finding"),               # DCIS nuclear pleomorphism, grade 1
    ("CL_DCIS_NUCLEAR_GRADE", "INTERMEDIATE"): ("369782002", "finding"),      # DCIS nuclear pleomorphism, grade 2
    ("CL_DCIS_NUCLEAR_GRADE", "HIGH"): ("369783007", "finding"),              # DCIS nuclear pleomorphism, grade 3

    # ---- 검체 부위 구분 (body structure)
    ("CL_BIOPSY_SITE", "REGIONAL_NODE"): ("312500006", "body structure"),            # Regional lymph node structure
    ("CL_SURGICAL_SPECIMEN_SITE", "REGIONAL_NODE"): ("312500006", "body structure"),
    # PRIMARY(원발 부위)·DISTANT(원격 전이 부위): SNOMED 의 원발·전이 개념(372087000 등)은 부위가
    # 아니라 진단(disorder)이라 "어느 부위에서 뗀 검체인가"라는 이 필드의 뜻과 맞지 않는다.
    # MARGIN(절제연): 절제연을 가리키는 부위 concept 이 없다.

    # ---- 경과관찰
    ("CL_WATCH_AND_WAIT_STATUS", "ONGOING"): ("424313000", "regime/therapy"),        # Active surveillance (regime/therapy)
    # REGROWTH·CONVERTED_SURGERY·SUSTAINED_CCR: 경과의 상태를 가리키는 개념이 없다.

    # ---- 아직 KAI 로 남는 것들(확인 결과 대응 개념이 없거나 값이 뭉친다)
    # CL_STAGING_METHOD: 축이 "무엇을 근거로 병기를 매겼나"인데 SNOMED 에는 근거 개념이 없고
    #   PET-CT(450436003)·골수생검(234326005) 같은 시술 concept 만 있다. 다섯 값 중 둘만 시술로
    #   올리면 코드표의 축이 섞이므로 전부 KAI 로 둔다.
    # CL_LYMPHOMA_CATEGORY(NHL_B·NHL_T): B 계열은 Mature (peripheral) B-cell neoplasm(414654003)이
    #   있으나 형질세포종까지 품는 더 넓은 개념이고, T 계열은 대응 개념이 아예 없다. 계열 정보는
    #   CL_CELL_LINEAGE 로 이미 받는다.
    # CL_PERITONEAL_CYTOLOGY_RESULT: 악성세포 유무 개념이 흉수 등 검체별로만 있고 복강 세척액용이 없다.
    # CL_TME_QUALITY: 395136002 는 전직장간막절제 "시술"이지 그 질 등급이 아니다.
    # CL_IMA_LIGATION_LEVEL: 하장간막동맥 결찰 시술 concept 만 있고 고위/저위라는 수준 값이 없다.
    # CL_IMAGING_DIAGNOSTIC_CLASSIFICATION(BI-RADS): SNOMED 에 척도(1348266008)와 평가 항목
    #   (146611000146107)은 있으나 범주 0~6 을 가리키는 값 concept 이 없다. 척도 concept 은 값이
    #   아니라 "이 필드가 무슨 척도인가"를 말하므로 필드 수준 메타로 두는 편이 맞다.
    # CL_ACTION_TAKEN_CONCEPT_ID·CL_OUTCOME_CONCEPT_ID: ICH E2B 규제 범주라 SNOMED 대응이 없다.
    # CL_GROSS_TYPE(Borrmann)·CL_TUMOR_BUDDING_GRADE(ITBCC)·CL_MRI_TUMOR_REGRESSION_GRADE(mrTRG)
    #   ·CL_VPI_GRADE·NASH CRN 등급: 출판 합의 척도지만 SNOMED 에 값 concept 이 없다.
}
# 주의: CL_DISTANT_METASTASIS_SITE 의 DISTANT_NODE 는 "원격 림프절"인데 SNOMED 에는 그 뜻의
# 단일 부위 concept 이 없어 Structure of lymph node(59441001) 로만 매핑했다. 국소/원격 구분은
# 부위 concept 이 아니라 병기 필드에서 읽어야 한다.
# 주의: BARIATRIC_SURGERY_HX·CANCER_HX 두 개는 (disorder) 가 아니라 (situation) 계층이다.
# 과거력 자체를 가리키는 개념이라 의미가 맞지만, OMOP 로 내보낼 때 domain 이 Condition 이 아니라
# Observation 으로 잡히는 것이 표준이므로 3단계(적재기)에서 domain 재지정을 검토한다.

# ================================================================ 척도(assessment scale) — 값이 아니라 코드표·필드를 설명한다
# BI-RADS 처럼 범주(0~6) 하나하나를 가리키는 SNOMED 개념은 없는데 "그 필드가 무슨 척도인가"를 가리키는
# 개념은 있는 경우가 있다. 이런 개념은 값 집합의 항목이 아니라 코드표 자신(=필드의 메타)에 붙인다.
# key: codelist_id -> (SNOMED concept_id, 영문명). <<273249006 |Assessment scales| 하위에서 확인했다.
SNOMED_SCALES = {
    "CL_IMAGING_DIAGNOSTIC_CLASSIFICATION": ("1348266008", "Breast Imaging and Reporting and Data System"),
    "BIRADS_DENSITY": ("1348266008", "Breast Imaging and Reporting and Data System"),  # 유방 밀도 범주도 BI-RADS 체계다
    "ECOG": ("273437007", "ECOG scale for physical assessment"),
    "DEAUVILLE": ("708895006", "Deauville five point scale"),
    "CTCAE_GRADE": ("711434002", "Common Terminology Criteria for Adverse Events"),
    "CHILD_PUGH": ("3191000175106", "Child-Pugh score"),
    "RCB_CLASS": ("445050009", "Residual cancer burden index"),
    "STAGE_GROUP_AJCC8": ("897275008", "American Joint Committee on Cancer, Cancer Staging Manual, 8th edition neoplasm staging system"),
}
# 찾았으나 붙이지 않은 것:
#   Clavien-Dindo 분류(789278003) — 대응하는 코드표가 아직 없다(합병증 "등급" 필드가 없다).
#   Lugano 분류 — SNOMED 것은 성인 호지킨·소아 호지킨처럼 질환별로 나뉘어 있어(1297085001 등)
#   호지킨·비호지킨을 함께 쓰는 STAGE_LUGANO 에 그대로 붙이면 범위가 좁아진다.
# 없는 것: RECIST, METAVIR, NAS(NAFLD 활성도), Wagner, 당뇨망막병증 중증도, CKD 병기.

# ================================================================ LOINC (로컬 파일에서 grep 으로 확인)
LOINC_SOURCE = "/Users/min/Research/standard_terminology/LOINC/Loinc_2.80/LoincTableCore/LoincTableCore.csv (2.80)"
# 개별 FIELD concept(측정값)에 표준 코드를 부여. key: 필드명 -> (loinc_code, 영문명)
LOINC_FIELD_CODES = {
    "hba1c_percent": ("4548-4", "Hemoglobin A1c/Hemoglobin.total in Blood"),
    "fpg_mg_dl": ("1558-6", "Fasting glucose [Mass/volume] in Serum or Plasma"),
    "random_glucose_mg_dl": ("2345-7", "Glucose [Mass/volume] in Serum or Plasma"),
    "postprandial_glucose_mg_dl": ("1521-4", "Glucose [Mass/volume] in Serum or Plasma --2 hours post meal"),
    "ogtt_2h_glucose_mg_dl": ("1521-4", "Glucose [Mass/volume] in Serum or Plasma --2 hours post meal"),
    "c_peptide_ng_ml": ("1986-9", "C peptide [Mass/volume] in Serum or Plasma"),
    "fasting_insulin_uiu_ml": ("20448-7", "Insulin [Units/volume] in Serum or Plasma"),
    "homa_ir": ("47214-2", "Homeostasis model assessment (HOMA) in Serum or Plasma"),
    "fructosamine_umol_l": ("33805-3", "Fructosamine [Mass/volume] in Serum or Plasma"),
    "gad_antibody_result": ("101233-5", "Glutamate decarboxylase 65 Ab [Presence] in Serum by Immunoblot"),
    "uacr_mg_g": ("14959-1", "Microalbumin/Creatinine [Mass Ratio] in Urine"),
    "ki67_percent": ("29593-1", "Cells.Ki-67 nuclear Ag/Cells in Tissue by Immune stain"),
    "pdl1_result": ("105304-0", "Tumor cells.PD-L1/Viable tumor cells in Tissue by Immune stain"),
}
# PFT_ITEM: 검사 항목 자체가 LOINC 코드를 가리키는 목록(값이 아니라 항목 concept 참조)
PFT_ITEMS = [
    ("FEV1", "1초간노력성호기량(FEV1)", "Volume expired during 1.0 s of forced expiration", "20150-9"),
    ("FVC", "노력성폐활량(FVC)", "Forced vital capacity", "19870-5"),
    ("FEV1_FVC", "FEV1/FVC 비", "FEV1/FVC ratio", "19926-5"),
    ("DLCO", "폐확산능(DLCO)", "Diffusion capacity, carbon monoxide", "19911-7"),
]
# ALCOHOL: 음주 이력 항목도 항목 concept 참조 목록
ALCOHOL_ITEMS = [
    ("AUDIT_TOTAL", "AUDIT 총점", "Total score [AUDIT]", "75624-7"),
    ("DRINKS_PER_DAY", "1일 음주량(잔)", "Alcoholic drinks per day", "74013-4"),
    ("DRINKS_PER_WEEK", "주간 음주량(잔)", "Alcoholic drinks per week", "105992-2"),
]

# ================================================================ 콤보 목록(개별 값이 아니라 표준 개념 참조) — SNOMED/ATC 확인 대기
# COMORBIDITY_SET: 과거력 진단명 목록. 네 번째 자리는 쓰지 않고(None), 실제 SNOMED concept_id 는 위 SNOMED_CODES 에 둔다.
COMORBIDITY_ITEMS = [
    ("HTN", "고혈압", "Hypertensive disorder", None), ("T2DM", "제2형 당뇨병", "Type 2 diabetes mellitus", None),
    ("DYSLIPIDEMIA", "이상지질혈증", "Hyperlipidemia", None), ("CVD", "심혈관질환", "Ischemic heart disease", None),
    ("CEREBROVASCULAR", "뇌혈관질환", "Cerebrovascular disease", None), ("CKD", "만성콩팥병", "Chronic kidney disease", None),
    ("PANCREATIC", "췌장질환", "Disorder of pancreas", None), ("HBV", "B형간염", "Chronic viral hepatitis B", None),
    ("HCV", "C형간염", "Chronic viral hepatitis C", None), ("HIV", "HIV 감염", "HIV infection", None),
    ("TB", "결핵", "Tuberculosis", None), ("HEART_DISEASE", "심장질환", "Heart disease", None),
    ("OTHER_RESPIRATORY", "기타 호흡기질환", "Respiratory disorder", None), ("COLORECTAL_DISEASE", "대장 질환", "Disorder of colon", None),
    ("KIDNEY_DISEASE", "신장 질환", "Disorder of kidney", None), ("LIVER_DISEASE", "간질환", "Liver disease", None),
    ("HYPOTHYROIDISM", "갑상선기능저하증", "Hypothyroidism", None), ("BARIATRIC_SURGERY_HX", "비만대사수술 과거력", "History of bariatric surgery", None),
    ("HEREDITARY_CRC", "유전성 대장암", "Hereditary nonpolyposis colorectal cancer", None), ("CANCER_HX", "암 과거력", "History of malignant neoplasm", None),
]
# DRUG_CLASS_SET: 약물 계열. ATC(WHO Anatomical Therapeutic Chemical) 분류는 안정적 국제 표준이라 MCP 없이도 기재 가능.
DRUG_CLASS_ITEMS = [
    ("INSULIN", "인슐린", "Insulin", "A10A"), ("METFORMIN", "메트포르민", "Metformin", "A10BA02"),
    ("SGLT2I", "SGLT2 억제제", "SGLT2 inhibitor", "A10BK"), ("GLP1RA", "GLP-1 수용체 작용제", "GLP-1 receptor agonist", "A10BJ"),
    ("DPP4I", "DPP-4 억제제", "DPP-4 inhibitor", "A10BH"), ("ANTI_CD20", "Anti-CD20 항체", "Anti-CD20 monoclonal antibody", "L01FA"),
    ("ANTHRACYCLINE", "안트라사이클린", "Anthracycline", "L01DB"), ("BTK_INHIBITOR", "BTK 억제제", "BTK inhibitor", "L01EL"),
    ("CHECKPOINT_INHIBITOR", "면역관문억제제", "Immune checkpoint inhibitor", "L01FF"),
]

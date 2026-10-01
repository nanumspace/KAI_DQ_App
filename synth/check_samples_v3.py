# -*- coding: utf-8 -*-
"""Check clinical and relational invariants of generated v3 clean/Good samples.

Unlike the DQ rules this checker uses independent, patient-level clinical relationships
that the synthetic data previously violated. It never claims to validate real EHR data.
"""
import argparse
import csv
from collections import defaultdict
from datetime import date
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent
PROFILES = yaml.safe_load((ROOT / "spec/v3/cohort_profiles_v3.yaml").read_text(encoding="utf-8"))["cohorts"]


def table(base, cohort, name):
    with (base / cohort / f"{name}.csv").open(newline="", encoding="utf-8-sig") as fh:
        return list(csv.DictReader(fh))


def check(cohort, base, good=False):
    people = table(base, cohort, "PERSON")
    disease = table(base, cohort, cohort)
    visits = table(base, cohort, "VISIT_OCCURRENCE")
    drugs = table(base, cohort, "DRUG_EXPOSURE")
    measures = table(base, cohort, "MEASUREMENT")
    problems = []

    def require(ok, detail):
        if not ok:
            problems.append(detail)

    require(len(people) == (1 if good else 100), "patient count")
    require(len(disease) == len(people), "one disease row per patient")
    known = {p["person_id"] for p in people}
    visit_ids = {v["visit_occurrence_id"] for v in visits}
    visit_owner = {v["visit_occurrence_id"]: v["person_id"] for v in visits}
    sact = table(base, cohort, "SACT") if "SACT" in PROFILES[cohort]["tables"] else []
    sact_owner = {r["sact_id"]: r["person_id"] for r in sact}
    for name in PROFILES[cohort]["tables"]:
        if name == "DRUG_INGREDIENT_STRUCTURE":
            continue
        for row in table(base, cohort, name):
            require(row["person_id"] in known, f"{name}: orphan patient")
            if row.get("visit_occurrence_id"):
                require(row["visit_occurrence_id"] in visit_ids, f"{name}: orphan visit")
                require(visit_owner.get(row["visit_occurrence_id"]) == row["person_id"],
                        f"{name}: visit belongs to another patient")
    for d in drugs:
        require(not d["sact_id"] or d["sact_id"] in sact_owner, "drug: orphan SACT")
        require(not d["sact_id"] or sact_owner.get(d["sact_id"]) == d["person_id"],
                "drug: SACT belongs to another patient")
    if good:
        for r in sact:
            require(any(d["sact_id"] == r["sact_id"] for d in drugs), "SACT without drug")
        ref = table(base, cohort, "DRUG_INGREDIENT_STRUCTURE")
        require(all(r["ingredient_concept_id"] in {d["drug_concept_id"] for d in drugs} for r in ref),
                "unused ingredient reference")
        if cohort in ("LUNG_CANCER", "BREAST_CANCER"):
            procedures = table(base, cohort, "PROCEDURE_OCCURRENCE")
            surgery = {"4033181"} if cohort == "LUNG_CANCER" else {"4118029", "4234573"}
            require(any(r["procedure_concept_id"] in surgery for r in procedures), "Good Sample without resection")
            require(not people[0]["death_date"], "Good Sample without surviving follow-up")

    lab = defaultdict(dict)
    for r in measures:
        cid = r["measurement_concept_id"]
        if cid == "3013721":
            require(float(r["value_as_number"]) > 0, "zero AST")
        if cid in ("3010813", "3017732"):
            key = (r["person_id"], r["visit_occurrence_id"], r["measurement_date"])
            lab[key].setdefault(cid, []).append(float(r["value_as_number"]))
    paired = 0
    for values in lab.values():
        if len(values.get("3010813", [])) == len(values.get("3017732", [])) == 1:
            paired += 1
            require(0 < values["3017732"][0] <= values["3010813"][0], "ANC > WBC or zero ANC")
    if cohort in ("LUNG_CANCER", "BREAST_CANCER", "COLORECTAL_CANCER", "LYMPHOMA"):
        require(paired > 0, "no paired CBC to validate")

    if cohort == "LUNG_CANCER":
        hist = {r["person_id"]: r["histologic_diagnosis"] for r in disease}
        for r in sact:
            name = r["regimen_source_value"]
            if hist[r["person_id"]] == "4":
                require("Pemetrexed" not in name and "Paclitaxel" not in name, "SCLC regimen")
            elif hist[r["person_id"]] == "2":
                require("Pemetrexed" not in name, "squamous pemetrexed")
    if cohort == "LYMPHOMA":
        notes = table(base, cohort, "NOTE")
        for r in notes:
            text = r["note_text"]
            if text.startswith("FDG PET/CT (baseline).") and "Lugano stage IV." in text:
                require("No extranodal involvement." not in text, "stage IV PET without extranodal involvement")
        for r in sact:
            if r["regimen_source_value"] == "ABVD":
                ids = {d["drug_concept_id"] for d in drugs if d["sact_id"] == r["sact_id"]}
                require({"1338512", "1329033", "19008264", "1319193"}.issubset(ids), "incomplete ABVD")
    if cohort == "DIABETES":
        by_index = {(r["person_id"], r["visit_occurrence_id"], r["condition_start_date"]) for r in disease}
        baseline = defaultdict(dict)
        for r in measures:
            key = (r["person_id"], r["visit_occurrence_id"], r["measurement_date"])
            if key in by_index and r["measurement_concept_id"] in ("3004410", "3004501"):
                baseline[r["person_id"]][r["measurement_concept_id"]] = float(r["value_as_number"])
        for pid in known:
            values = baseline[pid]
            require(values.get("3004410", 0) >= 6.5 and values.get("3004501", 0) >= 126,
                    "new T2DM without index glycemic evidence")
    if cohort == "MASLD":
        adverse = table(base, cohort, "ADVERSE_EVENT")
        require(all(r["adverse_event_concept_id"] != "24609" for r in adverse),
                "hypoglycemia without glucose-lowering exposure evidence")
    if cohort in ("MASLD", "DIABETES"):
        by_drug = defaultdict(list)
        for r in drugs:
            by_drug[(r["person_id"], r["drug_concept_id"])].append(r)
        for exposures in by_drug.values():
            ordered = sorted(exposures, key=lambda r: r["drug_exposure_start_date"])
            for earlier, later in zip(ordered, ordered[1:]):
                require(date.fromisoformat(earlier["drug_exposure_end_date"]) < date.fromisoformat(later["drug_exposure_start_date"]),
                        "overlapping same-drug exposures")
    if problems:
        raise AssertionError(f"{cohort} ({base.name}): {len(problems)} checks failed: {dict((p, problems.count(p)) for p in set(problems))}")
    print(f"{cohort} ({base.name}): patients={len(people)}, visits={len(visits)}, paired CBC={paired}, clinical checks OK")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--clean", type=Path, default=ROOT / "synth/output/clean_v3")
    parser.add_argument("--good", type=Path, default=ROOT / "synth/output/good_v3")
    args = parser.parse_args()
    for cohort in PROFILES:
        check(cohort, args.clean)
        check(cohort, args.good, good=True)


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""Tests for the evidence registry validator."""

from __future__ import annotations

import copy
import importlib.util
import json
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
SCRIPT = ROOT / "scripts" / "validate_evidence.py"
SPEC = importlib.util.spec_from_file_location("validate_evidence", SCRIPT)
VALIDATOR = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(VALIDATOR)


def payloads() -> tuple[dict, dict, dict]:
    with (ROOT / "references" / "authority-sources.json").open(encoding="utf-8") as handle:
        authorities = json.load(handle)
    with (ROOT / "references" / "candidate-audits.json").open(encoding="utf-8") as handle:
        candidates = json.load(handle)
    with (ROOT / "references" / "calendar-goldens.json").open(encoding="utf-8") as handle:
        goldens = json.load(handle)
    return authorities, candidates, goldens


class EvidenceValidationTests(unittest.TestCase):
    def test_repository_registries_are_valid(self) -> None:
        self.assertEqual(VALIDATOR.validate_all(*payloads()), [])

    def test_rejects_short_candidate_commit(self) -> None:
        authorities, candidates, goldens = copy.deepcopy(payloads())
        candidates["candidates"][0]["commit"] = "deadbeef"
        errors = VALIDATOR.validate_all(authorities, candidates, goldens)
        self.assertTrue(any("full lowercase 40-character SHA" in error for error in errors))

    def test_rejects_unlicensed_code_import(self) -> None:
        authorities, candidates, goldens = copy.deepcopy(payloads())
        item = next(candidate for candidate in candidates["candidates"] if candidate["code_license"] == "NOASSERTION")
        item["rights"]["code"] = "clear"
        item["reproducibility"] = "verified"
        item["import"]["code"] = True
        errors = VALIDATOR.validate_all(authorities, candidates, goldens)
        self.assertTrue(any("unlicensed code cannot be imported" in error for error in errors))

    def test_rejects_incompatible_code_import(self) -> None:
        authorities, candidates, goldens = copy.deepcopy(payloads())
        item = next(candidate for candidate in candidates["candidates"] if candidate["code_license"] == "AGPL-3.0-only")
        item["rights"]["code"] = "clear"
        item["reproducibility"] = "verified"
        item["import"]["code"] = True
        errors = VALIDATOR.validate_all(authorities, candidates, goldens)
        self.assertTrue(any("distribution policy" in error for error in errors))

    def test_rejected_claims_cannot_be_relabelled_primary(self) -> None:
        authorities, candidates, goldens = copy.deepcopy(payloads())
        item = next(candidate for candidate in candidates["candidates"] if candidate["decision"] == "reject")
        item["decision"] = "primary"
        item["reproducibility"] = "verified"
        item["independence"] = "independent"
        errors = VALIDATOR.validate_all(authorities, candidates, goldens)
        self.assertTrue(any("calculation tier A or B" in error for error in errors))
        self.assertTrue(any("authority sources and independent goldens" in error for error in errors))

    def test_tier_b_requires_clean_clone_verification(self) -> None:
        authorities, candidates, goldens = copy.deepcopy(payloads())
        item = candidates["candidates"][0]
        item["tier_by_claim"]["engineering"] = "B"
        item["reproducibility"] = "upstream-ci-only"
        errors = VALIDATOR.validate_all(authorities, candidates, goldens)
        self.assertTrue(any("Tier B claims require clean-clone verification" in error for error in errors))

    def test_tier_b_calculation_requires_independence_and_evidence(self) -> None:
        authorities, candidates, goldens = copy.deepcopy(payloads())
        item = candidates["candidates"][0]
        item["tier_by_claim"]["calculation"] = "B"
        item["reproducibility"] = "verified"
        item["independence"] = "partial"
        errors = VALIDATOR.validate_all(authorities, candidates, goldens)
        self.assertTrue(any("independent implementation" in error for error in errors))
        self.assertTrue(any("Tier B calculation requires authority sources" in error for error in errors))

    def test_primary_evidence_ids_must_exist(self) -> None:
        authorities, candidates, goldens = copy.deepcopy(payloads())
        item = next(
            candidate
            for candidate in candidates["candidates"]
            if candidate["code_license"] == "MIT" and candidate["rights"]["code"] == "clear"
        )
        item["decision"] = "primary"
        item["reproducibility"] = "verified"
        item["independence"] = "independent"
        item["tier_by_claim"]["calculation"] = "B"
        item["blocked_uses"] = [use for use in item["blocked_uses"] if use != "primary-authority"]
        item["calculation_evidence"] = {
            "claim_system": "calendar",
            "authority_source_ids": ["missing-authority"],
            "independent_golden_ids": ["missing-golden"],
        }
        item["primary_evidence"] = copy.deepcopy(item["calculation_evidence"])
        errors = VALIDATOR.validate_all(authorities, candidates, goldens)
        self.assertTrue(any("unknown authority source" in error for error in errors))
        self.assertTrue(any("unknown independent golden" in error for error in errors))

    def test_missing_authority_tier_is_reported_not_raised(self) -> None:
        authorities, candidates, goldens = copy.deepcopy(payloads())
        authorities["sources"][0].pop("tier")
        errors = VALIDATOR.validate_all(authorities, candidates, goldens)
        self.assertTrue(any("tier must be A or B" in error for error in errors))

    def test_all_registries_require_review_date(self) -> None:
        authorities, candidates, goldens = copy.deepcopy(payloads())
        candidates.pop("reviewed_at")
        errors = VALIDATOR.validate_all(authorities, candidates, goldens)
        self.assertTrue(any("candidate-audits: reviewed_at" in error for error in errors))

    def test_unknown_claim_key_cannot_bypass_calculation_gate(self) -> None:
        authorities, candidates, goldens = copy.deepcopy(payloads())
        item = candidates["candidates"][0]
        item["tier_by_claim"]["calculation-v2"] = item["tier_by_claim"].pop("calculation")
        errors = VALIDATOR.validate_all(authorities, candidates, goldens)
        self.assertTrue(any("approved claim taxonomy" in error for error in errors))

    def test_rejected_candidate_cannot_import_code(self) -> None:
        authorities, candidates, goldens = copy.deepcopy(payloads())
        item = next(candidate for candidate in candidates["candidates"] if candidate["decision"] == "reject")
        item["rights"]["code"] = "clear"
        item["code_license"] = "MIT"
        item["reproducibility"] = "verified"
        item["import"]["code"] = True
        errors = VALIDATOR.validate_all(authorities, candidates, goldens)
        self.assertTrue(any("rejected candidates or claims cannot import" in error for error in errors))

    def test_data_import_requires_separate_licence_and_provenance(self) -> None:
        authorities, candidates, goldens = copy.deepcopy(payloads())
        item = next(candidate for candidate in candidates["candidates"] if candidate["rights"]["data"] == "clear")
        item["import"]["data"] = True
        errors = VALIDATOR.validate_all(authorities, candidates, goldens)
        self.assertTrue(any("data import requires explicit licence and provenance" in error for error in errors))

    def test_code_import_requires_structured_reproduction_evidence(self) -> None:
        authorities, candidates, goldens = copy.deepcopy(payloads())
        item = next(
            candidate
            for candidate in candidates["candidates"]
            if candidate["code_license"] == "MIT"
            and candidate["rights"]["code"] == "clear"
            and candidate["decision"] != "reject"
        )
        item["reproducibility"] = "verified"
        item["import"]["code"] = True
        errors = VALIDATOR.validate_all(authorities, candidates, goldens)
        self.assertTrue(any("structured reproduction evidence" in error for error in errors))

    def test_primary_promotion_is_not_data_driven(self) -> None:
        authorities, candidates, goldens = copy.deepcopy(payloads())
        item = candidates["candidates"][0]
        item["decision"] = "primary"
        errors = VALIDATOR.validate_all(authorities, candidates, goldens)
        self.assertTrue(any("primary promotion is disabled" in error for error in errors))

    def test_cross_system_or_manual_golden_cannot_promote_candidate(self) -> None:
        authorities, candidates, goldens = copy.deepcopy(payloads())
        item = next(candidate for candidate in candidates["candidates"] if candidate["id"] == "h4x0r/stem-branch")
        item["decision"] = "primary"
        item["independence"] = "independent"
        item["tier_by_claim"]["calculation"] = "B"
        item["blocked_uses"] = [use for use in item["blocked_uses"] if use != "primary-authority"]
        evidence = {
            "claim_system": "bazi",
            "authority_source_ids": ["kanripo-sanming-tonghui"],
            "independent_golden_ids": ["hko-uncertain-new-moon-2057"],
        }
        item["calculation_evidence"] = copy.deepcopy(evidence)
        item["primary_evidence"] = copy.deepcopy(evidence)
        errors = VALIDATOR.validate_all(authorities, candidates, goldens)
        self.assertTrue(any("outside claim_system" in error for error in errors))
        self.assertTrue(any("requires executable hard or boundary goldens" in error for error in errors))

    def test_calculation_promotion_requires_single_system_record(self) -> None:
        authorities, candidates, goldens = copy.deepcopy(payloads())
        item = candidates["candidates"][0]
        item["tier_by_claim"]["calculation"] = "B"
        item["reproducibility"] = "verified"
        item["independence"] = "independent"
        item["calculation_evidence"] = {
            "claim_system": "calendar",
            "authority_source_ids": ["gbt-33661-2017"],
            "independent_golden_ids": ["gbt-reference-jiazi-day"],
        }
        errors = VALIDATOR.validate_all(authorities, candidates, goldens)
        self.assertTrue(any("single-system candidate record" in error for error in errors))

    def test_golden_adapter_and_authority_must_match_system(self) -> None:
        authorities, candidates, goldens = copy.deepcopy(payloads())
        case = goldens["cases"][0]
        case["system"] = "qimen"
        errors = VALIDATOR.validate_all(authorities, candidates, goldens)
        self.assertTrue(any("adapter does not match" in error for error in errors))
        self.assertTrue(any("authority source does not cover" in error for error in errors))

    def test_promotion_authority_must_directly_source_golden(self) -> None:
        authorities, candidates, goldens = copy.deepcopy(payloads())
        item = next(candidate for candidate in candidates["candidates"] if candidate["id"] == "h4x0r/stem-branch")
        item["systems"] = ["calendar"]
        item["tier_by_claim"]["calculation"] = "B"
        item["reproducibility"] = "verified"
        item["independence"] = "independent"
        item["calculation_evidence"] = {
            "claim_system": "calendar",
            "authority_source_ids": ["pmo-calendar-2026"],
            "independent_golden_ids": ["gbt-reference-jiazi-day"],
        }
        errors = VALIDATOR.validate_all(authorities, candidates, goldens)
        self.assertTrue(any("directly source each golden" in error for error in errors))

    def test_tier_b_requires_structured_reproduction_evidence(self) -> None:
        authorities, candidates, goldens = copy.deepcopy(payloads())
        item = candidates["candidates"][0]
        item["tier_by_claim"]["engineering"] = "B"
        item["reproducibility"] = "verified"
        errors = VALIDATOR.validate_all(authorities, candidates, goldens)
        self.assertTrue(any("structured reproduction evidence" in error for error in errors))

    def test_calculation_promotion_requires_convention_and_lineage(self) -> None:
        authorities, candidates, goldens = copy.deepcopy(payloads())
        item = next(candidate for candidate in candidates["candidates"] if candidate["id"] == "h4x0r/stem-branch")
        item["systems"] = ["calendar"]
        item["tier_by_claim"]["calculation"] = "B"
        item["reproducibility"] = "verified"
        item["independence"] = "independent"
        item["reproduction_evidence"] = {
            "commit": item["commit"],
            "commands": ["example-test-command"],
            "environment": {"runtime": "example-version"},
            "fixture_provenance": ["registry-linked-goldens"],
            "result": "passed",
            "tested_at": "2026-10-22",
        }
        item["calculation_evidence"] = {
            "claim_system": "calendar",
            "authority_source_ids": ["gbt-33661-2017"],
            "independent_golden_ids": ["gbt-reference-jiazi-day"],
        }
        errors = VALIDATOR.validate_all(authorities, candidates, goldens)
        self.assertTrue(any("complete convention contract" in error for error in errors))
        self.assertTrue(any("dependency lineage" in error for error in errors))

    def test_json_loader_rejects_duplicate_keys(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "duplicate.json"
            path.write_text('{"schema_version": 1, "schema_version": 2}', encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "duplicate JSON key"):
                VALIDATOR.load_json(path)

    def test_rejects_unknown_golden_source(self) -> None:
        authorities, candidates, goldens = copy.deepcopy(payloads())
        goldens["cases"][0]["sources"][0]["source_id"] = "missing-source"
        errors = VALIDATOR.validate_all(authorities, candidates, goldens)
        self.assertTrue(any("unknown authority source" in error for error in errors))

    def test_uncertainty_case_requires_behavior(self) -> None:
        authorities, candidates, goldens = copy.deepcopy(payloads())
        case = next(case for case in goldens["cases"] if case["kind"] == "uncertainty-case")
        case["expected"].pop("behavior")
        errors = VALIDATOR.validate_all(authorities, candidates, goldens)
        self.assertTrue(any("expected must define behavior" in error for error in errors))

    def test_hard_golden_cannot_be_manual_only(self) -> None:
        authorities, candidates, goldens = copy.deepcopy(payloads())
        case = next(case for case in goldens["cases"] if case["kind"] == "hard-golden")
        case["execution"] = {"adapter": "manual-only", "reason": "not wired"}
        errors = VALIDATOR.validate_all(authorities, candidates, goldens)
        self.assertTrue(any("hard and boundary goldens must be executable" in error for error in errors))


if __name__ == "__main__":
    unittest.main()

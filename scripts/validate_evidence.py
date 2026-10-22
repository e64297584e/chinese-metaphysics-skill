#!/usr/bin/env python3
"""Validate authority, candidate-audit, and calendar-golden registries."""

from __future__ import annotations

import json
import re
import sys
from datetime import date
from pathlib import Path
from urllib.parse import urlparse


ROOT = Path(__file__).resolve().parent.parent
AUTHORITY_FILE = ROOT / "references" / "authority-sources.json"
CANDIDATE_FILE = ROOT / "references" / "candidate-audits.json"
GOLDEN_FILE = ROOT / "references" / "calendar-goldens.json"

SHA40 = re.compile(r"^[0-9a-f]{40}$")
SHA256 = re.compile(r"^[0-9a-f]{64}$")
CHECKSUM_LENGTHS = {"md5": 32, "sha256": 64, "sha512": 128}
TIERS = {"A", "B", "C", "D", "Rejected"}
CLAIMS = {"engineering", "calculation", "interpretation"}
SYSTEMS = {"astronomy", "bazi", "calendar", "civil-time", "date-selection", "fengshui", "qimen", "ziwei"}
RIGHTS = {"clear", "limited", "unclear", "not-applicable"}
REPRODUCIBILITY = {"verified", "upstream-ci-only", "not-verified", "blocked"}
INDEPENDENCE = {"independent", "partial", "shared-lineage", "unknown"}
DECISIONS = {"primary", "audit-candidate", "coverage-lead", "methodology-only", "product-reference", "reject"}
GOLDEN_KINDS = {"hard-golden", "boundary-golden", "uncertainty-case"}
GOLDEN_ADAPTERS = {
    "bazi.day-ganzhi",
    "bazi.jie-event-minute",
    "bazi.solar-to-lunar",
    "manual-only",
}
GOLDEN_ADAPTER_SYSTEMS = {
    "bazi.day-ganzhi": "calendar",
    "bazi.jie-event-minute": "calendar",
    "bazi.solar-to-lunar": "calendar",
}
PERMISSIVE_CODE_LICENSES = {"MIT", "Apache-2.0", "BSD-3-Clause"}
REDISTRIBUTABLE_CONTENT_LICENSES = {
    "CC0-1.0",
    "CC-BY-4.0",
    "MIT",
    "Apache-2.0",
    "BSD-3-Clause",
    "public-domain",
}


def load_json(path: Path) -> dict:
    with path.open(encoding="utf-8") as handle:
        payload = json.load(handle, object_pairs_hook=reject_duplicate_keys)
    if not isinstance(payload, dict):
        raise ValueError(f"{path}: top level must be an object")
    return payload


def reject_duplicate_keys(pairs: list[tuple[str, object]]) -> dict:
    result: dict = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f"duplicate JSON key: {key}")
        result[key] = value
    return result


def is_https_url(value: object) -> bool:
    if not isinstance(value, str):
        return False
    parsed = urlparse(value)
    return parsed.scheme == "https" and bool(parsed.netloc)


def require_string(item: dict, key: str, where: str, errors: list[str]) -> None:
    if not isinstance(item.get(key), str) or not item[key].strip():
        errors.append(f"{where}: {key} must be a non-empty string")


def validate_reviewed_at(payload: dict, registry: str) -> list[str]:
    value = payload.get("reviewed_at")
    if not isinstance(value, str):
        return [f"{registry}: reviewed_at must be an ISO date"]
    try:
        reviewed = date.fromisoformat(value)
    except ValueError:
        return [f"{registry}: reviewed_at must be an ISO date"]
    if reviewed > date.today():
        return [f"{registry}: reviewed_at cannot be in the future"]
    return []


def validate_reproduction_evidence(candidate: dict, where: str) -> list[str]:
    evidence = candidate.get("reproduction_evidence")
    if not isinstance(evidence, dict):
        return [f"{where}: Tier B or primary review requires structured reproduction evidence"]
    errors: list[str] = []
    if evidence.get("commit") != candidate.get("commit"):
        errors.append(f"{where}: reproduction evidence commit must match candidate commit")
    commands = evidence.get("commands")
    if not isinstance(commands, list) or not commands or not all(
        isinstance(command, str) and command.strip() for command in commands
    ):
        errors.append(f"{where}: reproduction evidence requires commands")
    environment = evidence.get("environment")
    if not isinstance(environment, dict) or not environment or not all(
        isinstance(key, str) and key and isinstance(value, str) and value
        for key, value in environment.items()
    ):
        errors.append(f"{where}: reproduction evidence requires an explicit environment")
    fixtures = evidence.get("fixture_provenance")
    if not isinstance(fixtures, list) or not fixtures or not all(
        isinstance(item, str) and item.strip() for item in fixtures
    ):
        errors.append(f"{where}: reproduction evidence requires fixture provenance")
    if evidence.get("result") != "passed":
        errors.append(f"{where}: reproduction evidence result must be passed")
    try:
        date.fromisoformat(evidence.get("tested_at", ""))
    except (TypeError, ValueError):
        errors.append(f"{where}: reproduction evidence requires an ISO tested_at date")
    return errors


def validate_calculation_contract(candidate: dict, where: str) -> list[str]:
    contract = candidate.get("convention_contract")
    required = {"calendar", "timezone", "historical_dst", "day_boundary", "profile_id"}
    errors: list[str] = []
    if not isinstance(contract, dict) or not required.issubset(contract) or any(
        not isinstance(contract.get(key), str) or not contract[key].strip() for key in required
    ):
        errors.append(f"{where}: calculation promotion requires a complete convention contract")
    lineage = candidate.get("dependency_lineage")
    if not isinstance(lineage, list) or not lineage or not all(
        isinstance(item, str) and item.strip() for item in lineage
    ):
        errors.append(f"{where}: calculation promotion requires dependency lineage")
    return errors


def validate_authorities(payload: dict) -> tuple[list[str], dict[str, dict]]:
    errors = validate_reviewed_at(payload, "authority-sources")
    if payload.get("schema_version") != 1:
        errors.append("authority-sources: schema_version must be 1")
    sources = payload.get("sources")
    if not isinstance(sources, list) or not sources:
        return errors + ["authority-sources: sources must be a non-empty list"], {}

    by_id: dict[str, dict] = {}
    for index, source in enumerate(sources):
        where = f"authority-sources[{index}]"
        if not isinstance(source, dict):
            errors.append(f"{where}: must be an object")
            continue
        for key in ("id", "scope", "title", "version", "publisher", "rights"):
            require_string(source, key, where, errors)
        source_id = source.get("id")
        if isinstance(source_id, str):
            if source_id in by_id:
                errors.append(f"{where}: duplicate id {source_id}")
            by_id[source_id] = source
        if source.get("tier") not in {"A", "B"}:
            errors.append(f"{where}: tier must be A or B")
        systems = source.get("systems")
        if (
            not isinstance(systems, list)
            or not systems
            or any(system not in SYSTEMS for system in systems)
            or len(systems) != len(set(systems))
        ):
            errors.append(f"{where}: systems must be a non-empty unique list of known systems")
        urls = source.get("canonical_urls")
        if not isinstance(urls, list) or not urls or not all(is_https_url(url) for url in urls):
            errors.append(f"{where}: canonical_urls must contain only HTTPS URLs")
        commit = source.get("commit")
        if commit is not None and (not isinstance(commit, str) or not SHA40.fullmatch(commit)):
            errors.append(f"{where}: commit must be a full lowercase 40-character SHA")
        if isinstance(urls, list) and any(urlparse(url).netloc == "github.com" for url in urls if isinstance(url, str)):
            if not isinstance(commit, str) or not SHA40.fullmatch(commit):
                errors.append(f"{where}: GitHub authority sources require an exact commit")
        checksum = source.get("checksum")
        if checksum is not None:
            if not isinstance(checksum, dict) or set(checksum) != {"algorithm", "artifact", "value"}:
                errors.append(f"{where}: checksum must contain exactly algorithm, artifact, and value")
            else:
                algorithm = checksum.get("algorithm")
                value = checksum.get("value")
                if algorithm not in CHECKSUM_LENGTHS:
                    errors.append(f"{where}: unsupported checksum algorithm")
                elif not isinstance(value, str) or not re.fullmatch(
                    rf"[0-9a-f]{{{CHECKSUM_LENGTHS[algorithm]}}}", value
                ):
                    errors.append(f"{where}: checksum value does not match its algorithm")
                require_string(checksum, "artifact", f"{where}.checksum", errors)
        uses = source.get("permitted_uses")
        blocked = source.get("blocked_uses")
        if not isinstance(uses, list) or not uses or not all(isinstance(use, str) and use for use in uses):
            errors.append(f"{where}: permitted_uses must be a non-empty list")
        if not isinstance(blocked, list) or not all(isinstance(use, str) and use for use in blocked):
            errors.append(f"{where}: blocked_uses must be a list")
    return errors, by_id


def validate_candidates(
    payload: dict,
    authorities: dict[str, dict],
    golden_cases: dict[str, dict],
) -> list[str]:
    errors = validate_reviewed_at(payload, "candidate-audits")
    if payload.get("schema_version") != 1:
        errors.append("candidate-audits: schema_version must be 1")
    candidates = payload.get("candidates")
    if not isinstance(candidates, list) or not candidates:
        return errors + ["candidate-audits: candidates must be a non-empty list"]

    seen: set[str] = set()
    for index, candidate in enumerate(candidates):
        where = f"candidate-audits[{index}]"
        if not isinstance(candidate, dict):
            errors.append(f"{where}: must be an object")
            continue
        for key in ("id", "repository", "commit", "code_license"):
            require_string(candidate, key, where, errors)
        candidate_id = candidate.get("id")
        if isinstance(candidate_id, str):
            if candidate_id in seen:
                errors.append(f"{where}: duplicate id {candidate_id}")
            seen.add(candidate_id)
        if not is_https_url(candidate.get("repository")):
            errors.append(f"{where}: repository must be an HTTPS URL")
        commit = candidate.get("commit")
        if not isinstance(commit, str) or not SHA40.fullmatch(commit):
            errors.append(f"{where}: commit must be a full lowercase 40-character SHA")
        discovery = candidate.get("discovered_via")
        if not isinstance(discovery, list) or not discovery or not all(
            isinstance(item, str) and item for item in discovery
        ):
            errors.append(f"{where}: discovered_via must be a non-empty list")

        rights = candidate.get("rights")
        if not isinstance(rights, dict) or set(rights) != {"code", "data", "text"}:
            errors.append(f"{where}: rights must contain exactly code, data, and text")
            rights = {}
        for key, value in rights.items():
            if value not in RIGHTS:
                errors.append(f"{where}: invalid rights.{key} value {value!r}")

        if candidate.get("reproducibility") not in REPRODUCIBILITY:
            errors.append(f"{where}: invalid reproducibility")
        if candidate.get("independence") not in INDEPENDENCE:
            errors.append(f"{where}: invalid independence")
        systems = candidate.get("systems")
        if (
            not isinstance(systems, list)
            or not systems
            or any(system not in SYSTEMS for system in systems)
            or len(systems) != len(set(systems))
        ):
            errors.append(f"{where}: systems must be a non-empty unique list of known systems")
            systems = []
        tiers = candidate.get("tier_by_claim")
        if not isinstance(tiers, dict) or set(tiers) != CLAIMS:
            errors.append(f"{where}: tier_by_claim must contain exactly the approved claim taxonomy")
            tiers = {}
        elif any(value not in TIERS for value in tiers.values()):
            errors.append(f"{where}: tier_by_claim contains an invalid tier")
        if "B" in tiers.values() and candidate.get("reproducibility") != "verified":
            errors.append(f"{where}: Tier B claims require clean-clone verification")
        if "B" in tiers.values():
            errors.extend(validate_reproduction_evidence(candidate, where))
        if tiers.get("calculation") == "B":
            if len(systems) != 1:
                errors.append(f"{where}: Tier B calculation requires a single-system candidate record")
            if candidate.get("independence") != "independent":
                errors.append(f"{where}: Tier B calculation requires an independent implementation")
            errors.extend(validate_calculation_contract(candidate, where))
            calculation_evidence = candidate.get("calculation_evidence")
            errors.extend(
                validate_evidence_links(
                    calculation_evidence,
                    authorities,
                    golden_cases,
                    set(systems),
                    where,
                    "Tier B calculation",
                )
            )
        if "A" in tiers.values() and candidate.get("decision") != "primary":
            errors.append(f"{where}: Tier A claims require primary review status")
        decision = candidate.get("decision")
        if decision not in DECISIONS:
            errors.append(f"{where}: invalid decision")

        imports = candidate.get("import")
        if not isinstance(imports, dict) or set(imports) != {"code", "data", "text"}:
            errors.append(f"{where}: import must contain exactly code, data, and text")
            imports = {}
        elif any(not isinstance(value, bool) for value in imports.values()):
            errors.append(f"{where}: import values must be booleans")

        for kind in ("code", "data", "text"):
            if imports.get(kind) and rights.get(kind) != "clear":
                errors.append(f"{where}: cannot import {kind} when rights are not clear")
        if (decision == "reject" or "Rejected" in tiers.values()) and any(imports.values()):
            errors.append(f"{where}: rejected candidates or claims cannot import artifacts")
        if imports.get("code"):
            if candidate.get("code_license") == "NOASSERTION":
                errors.append(f"{where}: unlicensed code cannot be imported")
            if candidate.get("code_license") not in PERMISSIVE_CODE_LICENSES:
                errors.append(f"{where}: code import is not approved for this repository's distribution policy")
            if candidate.get("reproducibility") != "verified":
                errors.append(f"{where}: code import requires clean-clone verification")
            errors.extend(validate_reproduction_evidence(candidate, where))
        for kind in ("data", "text"):
            if not imports.get(kind):
                continue
            import_evidence = candidate.get("import_evidence")
            evidence = import_evidence.get(kind) if isinstance(import_evidence, dict) else None
            if not isinstance(evidence, dict):
                errors.append(f"{where}: {kind} import requires explicit licence and provenance")
                continue
            if evidence.get("license") not in REDISTRIBUTABLE_CONTENT_LICENSES:
                errors.append(f"{where}: {kind} import licence is not approved")
            provenance = evidence.get("provenance_urls")
            if not isinstance(provenance, list) or not provenance or not all(
                is_https_url(url) for url in provenance
            ):
                errors.append(f"{where}: {kind} import requires HTTPS provenance URLs")
            require_string(evidence, "artifact_id", f"{where}.import_evidence.{kind}", errors)
            require_string(evidence, "source_revision", f"{where}.import_evidence.{kind}", errors)
            if not isinstance(evidence.get("sha256"), str) or not SHA256.fullmatch(evidence["sha256"]):
                errors.append(f"{where}: {kind} import requires a lowercase SHA-256 artifact hash")
        blocked = candidate.get("blocked_uses")
        if not isinstance(blocked, list):
            errors.append(f"{where}: blocked_uses must be a list")
            blocked = []
        if decision != "primary" and "primary-authority" not in blocked:
            errors.append(f"{where}: non-primary candidates must block primary-authority use")
        if decision == "primary":
            errors.append(
                f"{where}: primary promotion is disabled in registry data and requires a reviewed schema/code change"
            )
            if len(systems) != 1:
                errors.append(f"{where}: primary review requires a single-system candidate record")
            if candidate.get("reproducibility") != "verified":
                errors.append(f"{where}: primary candidate must be clean-clone verified")
            if "B" not in tiers.values():
                errors.extend(validate_reproduction_evidence(candidate, where))
            if tiers.get("calculation") != "B":
                errors.extend(validate_calculation_contract(candidate, where))
            if candidate.get("independence") != "independent":
                errors.append(f"{where}: primary candidate must be independent")
            if tiers.get("calculation") not in {"A", "B"}:
                errors.append(f"{where}: primary candidate requires calculation tier A or B")
            if rights.get("code") != "clear":
                errors.append(f"{where}: primary candidate requires clear code rights")
            if candidate.get("code_license") not in PERMISSIVE_CODE_LICENSES:
                errors.append(f"{where}: primary candidate requires an approved permissive code licence")
            primary_evidence = candidate.get("primary_evidence")
            errors.extend(
                validate_evidence_links(
                    primary_evidence,
                    authorities,
                    golden_cases,
                    set(systems),
                    where,
                    "primary candidate",
                )
            )
            if "primary-authority" in blocked:
                errors.append(f"{where}: primary candidate cannot also block primary-authority use")
        if not isinstance(candidate.get("allowed_uses"), list) or not all(
            isinstance(use, str) and use for use in candidate.get("allowed_uses", [])
        ):
            errors.append(f"{where}: allowed_uses must be a list")
        if (
            not isinstance(candidate.get("notes"), list)
            or not candidate["notes"]
            or not all(isinstance(note, str) and note for note in candidate["notes"])
        ):
            errors.append(f"{where}: notes must be a non-empty list")
    return errors


def validate_evidence_links(
    evidence: object,
    authorities: dict[str, dict],
    golden_cases: dict[str, dict],
    candidate_systems: set[str],
    where: str,
    label: str,
) -> list[str]:
    if not isinstance(evidence, dict):
        return [f"{where}: {label} requires authority sources and independent goldens"]
    authority_ids = evidence.get("authority_source_ids")
    independent_golden_ids = evidence.get("independent_golden_ids")
    claim_system = evidence.get("claim_system")
    if not isinstance(authority_ids, list) or not authority_ids:
        return [f"{where}: {label} requires authority sources and independent goldens"]
    if not isinstance(independent_golden_ids, list) or not independent_golden_ids:
        return [f"{where}: {label} requires authority sources and independent goldens"]

    errors: list[str] = []
    if claim_system not in SYSTEMS or claim_system not in candidate_systems:
        errors.append(f"{where}: {label} claim_system must match a declared candidate system")
    if any(not isinstance(source_id, str) or source_id not in authorities for source_id in authority_ids):
        errors.append(f"{where}: {label} references an unknown authority source")
    if any(not isinstance(case_id, str) or case_id not in golden_cases for case_id in independent_golden_ids):
        errors.append(f"{where}: {label} references an unknown independent golden")
    known_authorities = [authorities[source_id] for source_id in authority_ids if source_id in authorities]
    if claim_system in SYSTEMS:
        if any(claim_system not in source.get("systems", []) for source in known_authorities):
            errors.append(f"{where}: {label} authority source is outside claim_system")
        if not any(
            source.get("tier") == "A" and claim_system in source.get("systems", [])
            for source in known_authorities
        ):
            errors.append(f"{where}: {label} requires a matching Tier A authority")
        known_goldens = [golden_cases[case_id] for case_id in independent_golden_ids if case_id in golden_cases]
        if any(case.get("system") != claim_system for case in known_goldens):
            errors.append(f"{where}: {label} independent golden is outside claim_system")
        if any(
            case.get("kind") not in {"hard-golden", "boundary-golden"}
            or case.get("execution", {}).get("adapter") == "manual-only"
            for case in known_goldens
        ):
            errors.append(f"{where}: {label} requires executable hard or boundary goldens")
        for case in known_goldens:
            case_sources = {
                ref.get("source_id")
                for ref in case.get("sources", [])
                if isinstance(ref, dict)
            }
            if not case_sources.intersection(authority_ids):
                errors.append(f"{where}: {label} authority must directly source each golden")
    return errors


def validate_goldens(payload: dict, authorities: dict[str, dict]) -> list[str]:
    errors = validate_reviewed_at(payload, "calendar-goldens")
    if payload.get("schema_version") != 1:
        errors.append("calendar-goldens: schema_version must be 1")
    cases = payload.get("cases")
    if not isinstance(cases, list) or not cases:
        return errors + ["calendar-goldens: cases must be a non-empty list"]

    seen: set[str] = set()
    required = {
        "id",
        "kind",
        "calendar_semantics",
        "jurisdiction",
        "timezone",
        "time_scale",
        "precision",
        "uncertainty",
    }
    for index, case in enumerate(cases):
        where = f"calendar-goldens[{index}]"
        if not isinstance(case, dict):
            errors.append(f"{where}: must be an object")
            continue
        for key in required:
            require_string(case, key, where, errors)
        case_id = case.get("id")
        if isinstance(case_id, str):
            if case_id in seen:
                errors.append(f"{where}: duplicate id {case_id}")
            seen.add(case_id)
        kind = case.get("kind")
        if kind not in GOLDEN_KINDS:
            errors.append(f"{where}: invalid kind")
        if case.get("system") not in SYSTEMS:
            errors.append(f"{where}: system must name a known system")
        if not isinstance(case.get("input"), dict) or not case["input"]:
            errors.append(f"{where}: input must be a non-empty object")
        if not isinstance(case.get("expected"), dict) or not case["expected"]:
            errors.append(f"{where}: expected must be a non-empty object")
        if kind == "uncertainty-case":
            if case.get("uncertainty") == "none-stated":
                errors.append(f"{where}: uncertainty-case must declare uncertainty")
            if "behavior" not in case.get("expected", {}):
                errors.append(f"{where}: uncertainty-case expected must define behavior")

        execution = case.get("execution")
        if not isinstance(execution, dict) or execution.get("adapter") not in GOLDEN_ADAPTERS:
            errors.append(f"{where}: execution must name a supported adapter")
        else:
            adapter = execution["adapter"]
            if kind in {"hard-golden", "boundary-golden"} and adapter == "manual-only":
                errors.append(f"{where}: hard and boundary goldens must be executable")
            if adapter == "manual-only":
                require_string(execution, "reason", f"{where}.execution", errors)
            elif GOLDEN_ADAPTER_SYSTEMS.get(adapter) != case.get("system"):
                errors.append(f"{where}: execution adapter does not match the golden system")

        source_refs = case.get("sources")
        if not isinstance(source_refs, list) or not source_refs:
            errors.append(f"{where}: sources must be a non-empty list")
            continue
        tiers: set[str] = set()
        for ref_index, ref in enumerate(source_refs):
            ref_where = f"{where}.sources[{ref_index}]"
            if not isinstance(ref, dict):
                errors.append(f"{ref_where}: must be an object")
                continue
            source_id = ref.get("source_id")
            if source_id not in authorities:
                errors.append(f"{ref_where}: unknown authority source {source_id!r}")
            else:
                tier = authorities[source_id].get("tier")
                if isinstance(tier, str):
                    tiers.add(tier)
                if case.get("system") not in authorities[source_id].get("systems", []):
                    errors.append(f"{ref_where}: authority source does not cover the golden system")
            require_string(ref, "locator", ref_where, errors)
        if kind in {"hard-golden", "boundary-golden"} and "A" not in tiers:
            errors.append(f"{where}: hard and boundary goldens require at least one Tier A source")
    return errors


def validate_all(
    authority_payload: dict,
    candidate_payload: dict,
    golden_payload: dict,
) -> list[str]:
    authority_errors, authorities = validate_authorities(authority_payload)
    cases = golden_payload.get("cases")
    golden_cases = (
        {
            case["id"]: case
            for case in cases
            if isinstance(case, dict) and isinstance(case.get("id"), str)
        }
        if isinstance(cases, list)
        else set()
    )
    return (
        authority_errors
        + validate_candidates(candidate_payload, authorities, golden_cases)
        + validate_goldens(golden_payload, authorities)
    )


def main() -> int:
    try:
        authority_payload = load_json(AUTHORITY_FILE)
        candidate_payload = load_json(CANDIDATE_FILE)
        golden_payload = load_json(GOLDEN_FILE)
    except (OSError, json.JSONDecodeError, ValueError) as exc:
        print(f"FAIL evidence registry: {exc}")
        return 1

    errors = validate_all(authority_payload, candidate_payload, golden_payload)
    if errors:
        for error in errors:
            print(f"FAIL {error}")
        return 1
    print(
        "OK evidence registry: "
        f"{len(authority_payload['sources'])} authorities, "
        f"{len(candidate_payload['candidates'])} candidates, "
        f"{len(golden_payload['cases'])} calendar cases"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())

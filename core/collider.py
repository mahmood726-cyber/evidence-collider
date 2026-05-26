import csv
import datetime
import json
import os
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
OUTPUT_PATH = PROJECT_ROOT / "data" / "collider_results.json"
AACT_ENV_VARS = ("EVIDENCE_COLLIDER_AACT_PATH", "AACT_FACILITIES_PATH")
SDI_ENV_VARS = ("EVIDENCE_COLLIDER_SDI_PATH", "IHME_SDI_PATH")


def safe_float(val, fallback=0.0):
    try:
        return float(val)
    except (TypeError, ValueError):
        return fallback


def _candidate_drive_roots():
    roots = []
    for drive in ("C", "D", "F"):
        root = Path(f"{drive}:/")
        if root.exists():
            roots.append(root)
    return roots


def _existing_path(path_like):
    if not path_like:
        return None
    path = Path(path_like).expanduser()
    if path.exists():
        return path
    return None


def _glob_first(patterns):
    for pattern in patterns:
        matches = sorted(PROJECT_ROOT.glob(pattern))
        if matches:
            return matches[0]
    return None


def resolve_aact_path(explicit_path=None):
    explicit = _existing_path(explicit_path)
    if explicit is not None:
        return explicit

    for env_var in AACT_ENV_VARS:
        env_path = _existing_path(os.environ.get(env_var))
        if env_path is not None:
            return env_path

    candidates = []
    for root in _candidate_drive_roots():
        candidates.extend(
            [
                root / "AACT-storage" / "AACT" / "2026-04-12" / "facilities.txt",
                root / "Projects" / "transportability-meta-frontier" / "data" / "aact_subset" / "facilities.txt",
            ]
        )
    for candidate in candidates:
        if candidate.exists():
            return candidate

    discovered = _glob_first(
        [
            "../AACT-storage/AACT/*/facilities.txt",
            "../../AACT-storage/AACT/*/facilities.txt",
            "../../../AACT-storage/AACT/*/facilities.txt",
        ]
    )
    if discovered is not None:
        return discovered.resolve()

    raise FileNotFoundError(
        "AACT facilities.txt not found. Set EVIDENCE_COLLIDER_AACT_PATH or AACT_FACILITIES_PATH."
    )


def resolve_sdi_path(explicit_path=None):
    explicit = _existing_path(explicit_path)
    if explicit is not None:
        return explicit

    for env_var in SDI_ENV_VARS:
        env_path = _existing_path(os.environ.get(env_var))
        if env_path is not None:
            return env_path

    candidates = []
    for root in _candidate_drive_roots():
        candidates.extend(
            [
                root
                / "Projects"
                / "ihme-data-lakehouse"
                / "data"
                / "raw"
                / "ghdx_bulk"
                / "gbd-2023-socio-demographic-index-sdi"
                / "SDI Values_ 1950-2023 [CSV]",
                root
                / "Projects"
                / "ihme-data-lakehouse"
                / "data"
                / "raw"
                / "gbd_covariates"
                / "gbd-2023-socio-demographic-index-sdi"
                / "SDI Values_ 1950-2023 [CSV]",
            ]
        )
    for candidate in candidates:
        if candidate.exists():
            return candidate

    discovered = _glob_first(
        [
            "../Projects/ihme-data-lakehouse/data/raw/*/gbd-2023-socio-demographic-index-sdi/SDI Values_ 1950-2023 [CSV]",
            "../../Projects/ihme-data-lakehouse/data/raw/*/gbd-2023-socio-demographic-index-sdi/SDI Values_ 1950-2023 [CSV]",
            "../../../Projects/ihme-data-lakehouse/data/raw/*/gbd-2023-socio-demographic-index-sdi/SDI Values_ 1950-2023 [CSV]",
        ]
    )
    if discovered is not None:
        return discovered.resolve()

    raise FileNotFoundError(
        "IHME SDI CSV not found. Set EVIDENCE_COLLIDER_SDI_PATH or IHME_SDI_PATH."
    )


def default_output_path():
    return OUTPUT_PATH


def run_collider(aact_path, sdi_path):
    print("--- GSP Collider: Ingesting AACT vs IHME ---")

    trial_counts = {}
    with Path(aact_path).open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle, delimiter="|")
        for row in reader:
            country = row.get("country", "").upper().strip()
            if country:
                trial_counts[country] = trial_counts.get(country, 0) + 1

    collider_results = []
    with Path(sdi_path).open(newline="", encoding="utf-8-sig") as handle:
        reader = csv.DictReader(handle)
        for row in reader:
            if row["year_id"] != "2023" or row["location_name"] == "Global":
                continue

            loc_name = row["location_name"].upper().strip()
            sdi = safe_float(row["mean_value"])
            matches = [country for country in trial_counts if country in loc_name or loc_name in country]
            n_trials = sum(trial_counts[country] for country in matches)
            desert_score = n_trials / (1.0 - sdi + 1e-10)
            collider_results.append(
                {
                    "location": row["location_name"],
                    "sdi": sdi,
                    "n_trials": n_trials,
                    "desert_score": float(desert_score),
                    "status": "DESERT" if desert_score < 10 else "STABLE",
                }
            )

    return sorted(collider_results, key=lambda item: item["desert_score"])


def build_output(results, timestamp=None):
    return {
        "audit": {
            "methodology": "Evidence Collider v1 (GSP-Hardened)",
            "timestamp": timestamp or datetime.datetime.now().isoformat(),
            "n_locations": len(results),
            "sources": ["AACT-facilities", "IHME-SDI-2023"],
        },
        "deserts": results,
    }


def write_output(payload, output_path=None):
    target = Path(output_path) if output_path is not None else default_output_path()
    target.parent.mkdir(parents=True, exist_ok=True)
    with target.open("w", encoding="utf-8") as handle:
        json.dump(payload, handle, indent=2)
    return target


def main(aact_path=None, sdi_path=None, output_path=None):
    resolved_aact = resolve_aact_path(aact_path)
    resolved_sdi = resolve_sdi_path(sdi_path)
    results = run_collider(resolved_aact, resolved_sdi)
    payload = build_output(results)
    target = write_output(payload, output_path=output_path)
    deserts = sum(1 for result in results if result["status"] == "DESERT")
    print(f"Collider complete. Identified {deserts} evidence deserts.")
    print(f"Wrote {target}")
    return target


if __name__ == "__main__":
    main()

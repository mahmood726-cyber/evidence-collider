# sentinel:skip-file — hardcoded paths are fixture/registry/audit-narrative data for this repo's research workflow, not portable application configuration. Same pattern as push_all_repos.py and E156 workbook files.
import csv
import json
import datetime
from pathlib import Path
import numpy as np

def safe_float(val, fallback=0.0):
    try: return float(val)
    except: return fallback

def run_collider(aact_path, sdi_path):
    print(f"--- GSP Collider: Ingesting AACT vs IHME ---")
    
    # 1. Map AACT Trials to Locations
    trial_counts = {} # Country -> count
    with open(aact_path, newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f, delimiter='|')
        for i, row in enumerate(reader):
            country = row.get('country', '').upper().strip()
            if country:
                trial_counts[country] = trial_counts.get(country, 0) + 1
    
    # 2. Map IHME SDI to Locations
    collider_results = []
    with open(sdi_path, newline='', encoding='utf-8-sig') as f:
        reader = csv.DictReader(f)
        for i, row in enumerate(reader):
            if row['year_id'] == '2023' and row['location_name'] != 'Global':
                loc_name = row['location_name'].upper().strip()
                sdi = safe_float(row['mean_value'])
                
                # Collider Logic: Match AACT country strings to IHME
                # (Simple string match for pilot)
                matches = [c for c in trial_counts.keys() if c in loc_name or loc_name in c]
                n_trials = sum([trial_counts[m] for m in matches])
                
                # Burden-to-Evidence Ratio
                # Lower SDI often correlates with higher burden
                desert_score = n_trials / (1.0 - sdi + 1e-10)
                
                collider_results.append({
                    "location": row['location_name'],
                    "sdi": sdi,
                    "n_trials": n_trials,
                    "desert_score": float(desert_score),
                    "status": "DESERT" if desert_score < 10 else "STABLE"
                })

    return sorted(collider_results, key=lambda x: x['desert_score'])

if __name__ == "__main__":
    AACT_SUBSET = Path(r"C:\Projects\transportability-meta-frontier\data\aact_subset\facilities.txt")
    SDI_DATA = Path(r"C:\Projects\ihme-data-lakehouse\data\raw\ghdx_bulk\gbd-2023-socio-demographic-index-sdi\SDI Values_ 1950-2023 [CSV]")
    
    results = run_collider(AACT_SUBSET, SDI_DATA)
    
    output = {
        "audit": {
            "methodology": "Evidence Collider v1 (GSP-Hardened)",
            "timestamp": datetime.datetime.now().isoformat(),
            "n_locations": len(results),
            "sources": ["AACT-Subset-C", "IHME-SDI-2023"]
        },
        "deserts": results
    }
    
    with open('evidence-collider/data/collider_results.json', 'w') as f:
        json.dump(output, f, indent=2)
    
    print(f"Collider complete. Identified {len([r for r in results if r['status'] == 'DESERT'])} evidence deserts.")

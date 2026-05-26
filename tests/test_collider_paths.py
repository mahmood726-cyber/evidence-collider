import json
from pathlib import Path

from core.collider import build_output, resolve_aact_path, resolve_sdi_path, run_collider, write_output


def test_resolve_paths_prefer_env_overrides(monkeypatch, tmp_path):
    aact = tmp_path / "facilities.txt"
    aact.write_text("country|\nPAKISTAN|\n", encoding="utf-8")
    sdi = tmp_path / "sdi.csv"
    sdi.write_text("year_id,location_name,mean_value\n2023,Pakistan,0.4\n", encoding="utf-8")

    monkeypatch.setenv("EVIDENCE_COLLIDER_AACT_PATH", str(aact))
    monkeypatch.setenv("EVIDENCE_COLLIDER_SDI_PATH", str(sdi))

    assert resolve_aact_path() == aact
    assert resolve_sdi_path() == sdi


def test_run_collider_and_write_output(tmp_path):
    aact = tmp_path / "facilities.txt"
    aact.write_text(
        "country|name\nPakistan|Trial A\nPakistan|Trial B\nCanada|Trial C\nCanada|Trial D\n",
        encoding="utf-8",
    )
    sdi = tmp_path / "sdi.csv"
    sdi.write_text(
        "year_id,location_name,mean_value\n"
        "2023,Pakistan,0.50\n"
        "2023,Canada,0.90\n"
        "2022,Pakistan,0.40\n"
        "2023,Global,0.70\n",
        encoding="utf-8",
    )

    results = run_collider(aact, sdi)
    assert [row["location"] for row in results] == ["Pakistan", "Canada"]
    assert results[0]["status"] == "DESERT"
    assert results[0]["n_trials"] == 2
    assert results[1]["status"] == "STABLE"
    assert results[1]["n_trials"] == 2

    payload = build_output(results, timestamp="2026-05-26T00:00:00")
    output_path = tmp_path / "collider_results.json"
    written = write_output(payload, output_path=output_path)

    assert written == output_path
    loaded = json.loads(output_path.read_text(encoding="utf-8"))
    assert loaded["audit"]["n_locations"] == 2
    assert loaded["deserts"][0]["location"] == "Pakistan"

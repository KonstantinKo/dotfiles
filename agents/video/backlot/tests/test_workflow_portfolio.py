from __future__ import annotations

from pathlib import Path

from tests.conftest import FakeProvider, run_json
from tests.test_workflow import _register_cut, _workflow


def _snapshot_tree(*roots: Path) -> dict[str, bytes]:
    snapshot = {}
    for root in roots:
        snapshot.update({str(path): path.read_bytes() for path in root.rglob("*") if path.is_file()})
    return snapshot


def test_backlot_skill_scope_stays_inside_backlot_projects():
    video_root = Path(__file__).resolve().parents[2]
    assert (video_root / "backlot" / "skills" / "studio" / "SKILL.md").is_file()
    assert (video_root / "backlot" / "skills" / "assemble" / "SKILL.md").is_file()
    assert not (video_root / "skills" / "backlot").exists()


def test_read_only_inspections_preserve_richer_records_when_media_changed(project):
    _workflow(project, ["picture"])
    _, final, output = _register_cut(project)
    root, vault_project = project["root"], project["vault_project"]
    (vault_project / "Delivery.md").write_text(
        "# Delivery record\n\n"
        f"Accepted picture: complete-v3, SHA-256 `{final['sha256']}`.\n\n"
        "Later share copy: scored-v2; share expiry does not replace the picture master.\n\n"
        "Accepted limitations: one static reaction and short laughter.\n",
        encoding="utf-8",
    )
    for name, note in {
        "Status.md": "\n\nRecorded tracker stage remains boards; delivery record is current.\n",
        "Costs.md": "\n\nProvider credits and EUR ledger are separate; missing actual charge remains unknown.\n",
        "Deliverables.md": "\n\nCurrent external delivery: complete-v3; remote copy: scored-v2.\n",
        "demo.md": "\n\nHistorical approval scope is the exact picture version above.\n",
    }.items():
        path = vault_project / name
        current = path.read_text(encoding="utf-8") if path.is_file() else ""
        path.write_text(current + note, encoding="utf-8")

    # Make the registered media disagree with its accepted version. Inspection
    # must report the discrepancy while leaving every source record untouched.
    output.write_bytes(output.read_bytes() + b"changed after the accepted hash")
    before = _snapshot_tree(root, vault_project)
    FakeProvider.calls.clear()

    code, stage = run_json("stage")
    assert code == 1 and any("SHA-256" in issue or "differs from recorded" in issue
                             for issue in stage["missing"])
    status_code, status = run_json("status")
    cost_code, costs = run_json("cost")
    delivery_code, delivery = run_json("delivery")
    assert status_code == 0 and "Readiness: blocked" in status["status"]
    assert cost_code == 0 and "Native provider operations" not in costs["costs"]
    assert delivery_code == 1 and delivery["readiness"] == "blocked"
    assert "media missing or differs from recorded SHA-256" in str(delivery["blockers"])
    assert _snapshot_tree(root, vault_project) == before
    assert FakeProvider.calls == []

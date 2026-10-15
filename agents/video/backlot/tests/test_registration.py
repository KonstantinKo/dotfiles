from __future__ import annotations

import io
import json
import subprocess
from concurrent.futures import ThreadPoolExecutor
from contextlib import redirect_stdout

import pytest
import yaml
from PIL import Image

from backlot import cli, expenses, lineage, register, takes
from backlot import frontmatter
from backlot.authority import file_hash
from backlot.decisions import approve
from backlot.project import load_project_dir
from tests.conftest import FFMPEG, FakeProvider, run_json


def direct(*args):
    buf = io.StringIO()
    with redirect_stdout(buf):
        code = cli.main([*args, "--json"])
    return code, json.loads(buf.getvalue().strip().splitlines()[-1])


def picture(path, color):
    Image.new("RGB", (16, 16), color).save(path)
    return path


def video(path, color):
    subprocess.run([FFMPEG, "-y", "-loglevel", "error", "-f", "lavfi", "-i",
                    f"color=c={color}:s=32x32:r=24", "-frames:v", "24", "-pix_fmt", "yuv420p", str(path)], check=True)
    return path


def write_spec(project, name, data):
    path = project["root"] / f"{name}.json"
    path.write_text(json.dumps(data))
    return str(path)


def test_register_external_and_derivative_idempotent_native_expense_and_current_manifest(project):
    root = project["root"]
    source = video(root / "inputs" / "source.mp4", "red")
    derived = video(root / "inputs" / "derived.mp4", "blue")
    source_spec = {"kind": "vid", "origin": "provider", "media": str(source), "provider": "Higgsfield",
                   "operation_id": "job-12", "status": "rejected", "source_key": "opening",
                   "coverage": [{"story": "Opening", "source_frames": [0, 8], "shot": "S010"},
                                {"story": "Moon", "source_frames": [9, 15], "shot": "S020"}],
                   "original_request": {"prompt": "original"}, "effective_request": {"prompt": "effective"},
                   "expense": {"charge_status": "charged", "estimate": {"amount": 12, "unit": "credits"},
                               "charge": {"amount": 11, "unit": "credits", "evidence": "job receipt"},
                               "source_kind": "legacy", "source_ref": "audit/job-12"}}
    spec_file = write_spec(project, "source", source_spec)
    code, checked = direct("register", spec_file, "--dry-run")
    assert code == 0 and checked["provider_calls"] == 0 and checked["prepared"]["probe"]["streams"]
    assert not (root / "takes" / "vid-001").exists()
    code, first = direct("register", spec_file)
    assert code == 0 and first["take"] == "vid-001" and first["media_copied"] is False
    code, second = direct("register", spec_file)
    assert code == 0 and second["take"] == first["take"]
    meta = yaml.safe_load((root / "takes" / "vid-001" / "meta.yaml").read_text())
    assert meta["coverage"][1]["shot"] == "S020" and meta["original_request"]["prompt"] == "original"
    derivative_spec = {"kind": "vid", "origin": "local_derivative", "media": str(derived),
                       "source_refs": [{"id": "vid-001", "sha256": meta["sha256"], "role": "picture"}],
                       "coverage": [{"story": "Opening", "source_frames": [0, 8]}],
                       "recipe": "crop.py", "expense": {"provider": "local", "evidence_key": "crop-1",
                       "charge_status": "zero", "charge": {"amount": 0, "unit": "EUR"}}}
    code, derivative = direct("register", write_spec(project, "derived", derivative_spec))
    assert code == 0 and derivative["take"] == "vid-002"
    assert not FakeProvider.calls
    assert len(takes.list_takes(load_project_dir(root))) == 2
    assert expenses.summary(load_project_dir(root))["native_charged"] == {"credits": 11.0, "EUR": 0.0}
    allocated = expenses.allocate(load_project_dir(root), first["expense_id"], "current_final",
                                  source_ref="final-source-map.json", reason="selected picture range")
    assert allocated["allocation"] == "current_final"
    assert expenses.summary(load_project_dir(root))["current_final_native_allocation"] == {"credits": 11.0}
    assert direct("register", spec_file)[1]["take"] == "vid-001"
    assert "actual charge unknown for 0 operation(s)" in (project["vault_project"] / "Costs.md").read_text()
    manifest = [json.loads(line) for line in (root / "takes" / "manifest.jsonl").read_text().splitlines()]
    assert len(manifest) == 2 and manifest[0]["status"] == "rejected"
    approve(load_project_dir(root), "vid-002", "accepted crop", source_ref="thread/message-7",
            source_message="Yes, use this crop", scope="opening picture range")
    manifest = [json.loads(line) for line in (root / "takes" / "manifest.jsonl").read_text().splitlines()]
    assert manifest[1]["status"] == "approved"
    assert direct("manifest")[0] == 0


def test_existing_take_enriches_without_new_fee_and_preserves_unknown_fields(project):
    root = project["root"]
    source = picture(root / "inputs" / "old.png", "green")
    proj = load_project_dir(root)
    with takes.locked(proj):
        take = takes.Take(take="img-001", kind="img", model="legacy", provider="fal", status="new",
                          file="inputs/old.png", cost_eur=1.656, request_id="accepted-job")
        takes.take_dir(proj, take.take).mkdir()
        takes.write_meta(proj, take)
    path = takes.meta_path(proj, "img-001")
    raw = yaml.safe_load(path.read_text())
    raw.pop("schema_version")
    raw["legacy_custom"] = {"keep": True}
    path.write_text(yaml.safe_dump(raw))
    assert direct("migrate", "--dry-run")[1]["changed"] == ["img-001"]
    assert direct("migrate")[1]["changed"] == ["img-001"]
    assert direct("migrate")[1]["changed"] == []
    spec = {"id": "img-001", "kind": "img", "origin": "provider", "media": str(source),
            "provider": "fal", "operation_id": "accepted-job", "original_request": {"prompt": "old"},
            "expense": {"charge_status": "unknown", "estimate": {"amount": 1.8, "unit": "USD"},
                        "project_ledger": {"amount": 1.656, "unit": "EUR", "basis": "recorded conversion"},
                        "balance_observations": [{"amount": 38.29, "unit": "USD", "source": "user dashboard",
                                                  "observed_at": "2026-10-01T05:29:00Z"}]}}
    for candidate in (spec, {k: v for k, v in spec.items() if k != "id"}):
        code, result = direct("register", write_spec(project, "enrich", candidate))
        assert code == 0 and result["take"] == "img-001"
    assert takes.spent_eur(proj) == 1.656
    assert len(expenses.list_expenses(proj)) == 1
    assert len(expenses.list_expenses(proj)[0]["balance_observations"]) == 1
    assert expenses.summary(proj)["unknown_actual_charges"] == 1
    meta = yaml.safe_load(path.read_text())
    assert meta["legacy_custom"] == {"keep": True} and meta["schema_version"] == 2
    assert meta["original_request"]["prompt"] == "old"


def test_lineage_flags_only_changed_source_descendants_preserving_approved_bytes(project):
    root = project["root"]
    paths = [picture(root / "inputs" / f"p{i}.png", color) for i, color in enumerate(("red", "blue", "green", "yellow", "purple"))]
    proj = load_project_dir(root)
    src = register.register(proj, {"kind": "img", "origin": "supplied", "media": str(paths[0]), "source_key": "look"})
    derivative = register.register(proj, {"kind": "img", "origin": "local_derivative", "media": str(paths[1]),
                                    "source_refs": [{"id": src["take"], "sha256": src["sha256"]}]})
    assembled = register.register(proj, {"kind": "img", "origin": "assembly", "media": str(paths[2]),
                                   "source_refs": [{"id": derivative["take"], "sha256": derivative["sha256"]}]})
    unrelated = register.register(proj, {"kind": "img", "origin": "supplied", "media": str(paths[3])})
    takes.set_status(proj, assembled["take"], "approved")
    before = paths[2].read_bytes()
    assert lineage.check(proj)["needs_review"] == []
    register.register(proj, {"kind": "img", "origin": "supplied", "media": str(paths[4]), "source_key": "look"})
    result = lineage.check(proj)
    assert result["needs_review"] == [derivative["take"], assembled["take"]]
    assert unrelated["take"] not in result["needs_review"]
    assert paths[2].read_bytes() == before and takes.load_take(proj, assembled["take"]).status == "approved"


def test_lineage_detects_overwritten_and_missing_registered_outputs(project):
    root = project["root"]
    source = picture(root / "inputs" / "source.png", "red")
    derived = picture(root / "inputs" / "derived.png", "blue")
    proj = load_project_dir(root)
    original = register.register(proj, {"kind": "img", "origin": "supplied", "media": str(source)})
    child = register.register(proj, {"kind": "img", "origin": "local_derivative", "media": str(derived),
                                     "source_refs": [{"id": original["take"]}]})
    takes.set_status(proj, original["take"], "approved")
    expected = takes.load_take(proj, original["take"]).sha256
    picture(source, "green")
    changed = lineage.check(proj)
    assert changed["needs_review"] == [original["take"], child["take"]]
    assert any("recorded output bytes changed" in reason for reason in changed["direct"][original["take"]])
    assert changed["recorded_output_bytes_unchanged"] is False
    assert takes.load_take(proj, original["take"]).sha256 == expected
    assert takes.load_take(proj, original["take"]).status == "approved"
    source.unlink()
    missing = lineage.check(proj)
    assert missing["needs_review"] == [original["take"], child["take"]]
    assert missing["recorded_output_versions_available"] is False


def test_register_reconciles_zero_legacy_eur_and_rejects_conflict_without_writes(project):
    root = project["root"]
    source = picture(root / "inputs" / "legacy.png", "red")
    proj = load_project_dir(root)
    with takes.locked(proj):
        legacy = takes.Take(take="img-001", kind="img", model="old", provider="fal",
                            file="inputs/legacy.png", request_id="job-1")
        takes.take_dir(proj, legacy.take).mkdir()
        takes.write_meta(proj, legacy)
    spec = {"id": "img-001", "kind": "img", "origin": "provider", "media": str(source),
            "provider": "fal", "operation_id": "job-1",
            "expense": {"charge_status": "unknown", "estimate": {"amount": 1.8, "unit": "USD"},
                        "project_ledger": {"amount": 1.656, "unit": "EUR"}}}
    registered = register.register(proj, spec)
    assert takes.spent_eur(proj) == 1.656
    assert takes.load_take(proj, "img-001").expense_id == registered["expense_id"]
    assert register.register(proj, spec)["take"] == "img-001"
    assert takes.spent_eur(proj) == 1.656 and len(expenses.list_expenses(proj)) == 1
    before = takes.meta_path(proj, "img-001").read_bytes()
    with pytest.raises(Exception, match="conflicts with existing take costs"):
        register.register(proj, {**spec, "expense": {**spec["expense"],
            "project_ledger": {"amount": 2.0, "unit": "EUR"}}})
    assert takes.meta_path(proj, "img-001").read_bytes() == before
    assert len(expenses.list_expenses(proj)) == 1


def test_one_provider_job_with_two_imported_files_books_eur_once(project):
    root = project["root"]
    proj = load_project_dir(root)
    media = [picture(root / "inputs" / f"part-{i}.png", color)
             for i, color in enumerate(("red", "blue"))]
    spec = {"kind": "img", "origin": "provider", "provider": "fal", "operation_id": "one-job",
            "expense": {"charge_status": "unknown", "project_ledger": {"amount": 1.2, "unit": "EUR"}}}
    rows = [register.register(proj, {**spec, "media": str(path)}) for path in media]
    assert rows[0]["take"] != rows[1]["take"]
    assert rows[0]["expense_id"] == rows[1]["expense_id"]
    assert len(expenses.list_expenses(proj)) == 1
    assert takes.spent_eur(proj) == 1.2


def test_concurrent_register_allocates_unique_ids(project):
    root = project["root"]
    files = [picture(root / "inputs" / f"thread{i}.png", color) for i, color in enumerate(("red", "blue"))]
    proj = load_project_dir(root)
    with ThreadPoolExecutor(max_workers=2) as pool:
        results = list(pool.map(lambda path: register.register(proj, {"kind": "img", "origin": "supplied", "media": str(path)}), files))
    assert {row["take"] for row in results} == {"img-001", "img-002"}
    assert len(takes.list_takes(proj)) == 2


def test_unknown_cloud_price_fails_before_quote_or_provider_call(project):
    note = project["vault"] / "Studio" / "Models" / "fake-image.md"
    note.write_text(note.read_text().replace("cost_eur: 0.5\n", ""))
    code, data = direct("gen", "img", "--model", "fake-image", "--prompt", "p", "--yes")
    assert code == 1 and "no paid-route price estimate" in data["error"] and not FakeProvider.calls
    note.write_text(note.read_text().replace("cost_unit: per_image\n", "cost_unit: per_image\ncost_eur: 0.0\n"))
    code, data = direct("gen", "img", "--model", "fake-image", "--prompt", "p", "--dry-run")
    assert code == 1 and "zero cloud price without" in data["error"] and not FakeProvider.calls
    note.write_text(note.read_text().replace("cost_eur: 0.0\n", "cost_eur: 0.0\nzero_price_evidence: {source: web Unlimited}\n"))
    code, data = direct("gen", "img", "--model", "fake-image", "--prompt", "p", "--yes")
    assert code == 1 and "route-specific" in data["error"] and not FakeProvider.calls
    note.write_text(note.read_text().replace("zero_price_evidence: {source: web Unlimited}",
        "zero_price_evidence: {source: official route quote, model: fake-image, route: fal-ai/fake, observed_at: '2025-01-01T00:00:00Z', expires_at: '2025-01-02T00:00:00Z'}"))
    code, data = direct("gen", "img", "--model", "fake-image", "--prompt", "p", "--yes")
    assert code == 1 and "expired" in data["error"] and not FakeProvider.calls


def test_generated_take_records_effective_request_and_verified_output(project):
    code, rows = run_json("gen", "img", "--model", "fake-image", "--prompt", "red cube", "--yes")
    assert code == 0 and rows[0]["take"] == "img-001"
    proj = load_project_dir(project["root"])
    take = takes.load_take(proj, "img-001")
    assert take.original_request["prompt"] == "red cube"
    assert take.effective_request["route"] == "fal-ai/fake"
    assert take.sha256 == register._hash_media(takes.take_file(proj, "img-001"))
    assert take.probe["streams"]


def test_paid_generated_multifile_job_has_one_unknown_actual_expense(project, monkeypatch):
    from backlot.providers.base import GenResult

    class TwoFiles(FakeProvider):
        def run(self, model, req):
            req.on_submit("paid-two-files")
            files = [picture(req.workdir / f"result-{i}.png", color)
                     for i, color in enumerate(("red", "blue"))]
            return GenResult(files=files, job_id="paid-two-files", raw={"ok": True})

    monkeypatch.setattr("backlot.gen.get_provider", lambda name, cfg=None: TwoFiles(cfg))
    code, rows = run_json("gen", "img", "--model", "fake-image", "--prompt", "two", "--yes")
    assert code == 0 and len(rows) == 2
    proj = load_project_dir(project["root"])
    records = expenses.list_expenses(proj)
    assert len(records) == 1
    assert records[0]["operation_id"] == "paid-two-files"
    assert records[0]["estimate"]["amount"] == 0.5
    assert records[0]["estimate"]["basis"] == "project budget quote"
    assert records[0]["charge_status"] == "unknown" and records[0]["charge"] is None
    assert expenses.summary(proj)["unknown_actual_charges"] == 1
    assert {takes.load_take(proj, row["take"]).expense_id for row in rows} == {records[0]["id"]}
    assert takes.spent_eur(proj) == 0.5
    first = takes.load_take(proj, rows[0]["take"])
    register.register(proj, {"id": first.take, "kind": "img", "origin": "provider",
                             "media": str(proj.root / first.file), "provider": "fal",
                             "operation_id": "paid-two-files",
                             "expense": {"charge_status": "unknown",
                                         "project_ledger": {"amount": 0.5, "unit": "EUR"}}})
    assert takes.spent_eur(proj) == 0.5 and len(expenses.list_expenses(proj)) == 1


def test_generated_operation_expense_enriches_with_native_receipt_without_duplicate(project):
    code, rows = run_json("gen", "img", "--model", "fake-image", "--prompt", "receipt", "--yes")
    assert code == 0
    proj = load_project_dir(project["root"])
    take = takes.load_take(proj, rows[0]["take"])
    original = expenses.list_expenses(proj)[0]
    assert original["charge_status"] == "unknown" and original["id"] == take.expense_id
    evidence = {"provider": "fal", "operation_id": take.request_id, "source_ref": "receipt/job",
                "charge_status": "charged", "estimate": {"amount": 0.6, "unit": "USD"},
                "charge": {"amount": 0.57, "unit": "USD", "evidence": "receipt/job"},
                "project_ledger": {"amount": 0.5, "unit": "EUR", "basis": "project budget quote"}}
    for _ in range(2):
        updated = expenses.register(proj, evidence)
        assert updated["id"] == original["id"] and updated["charge_status"] == "charged"
    assert len(expenses.list_expenses(proj)) == 1
    assert updated["budget_quote"] == original["estimate"]
    assert updated["charge"]["unit"] == "USD"
    assert expenses.summary(proj)["native_charged"] == {"USD": 0.57}
    assert takes.spent_eur(proj) == 0.5


def test_stub_route_fails_before_cost_reservation(project, monkeypatch):
    from backlot.providers.higgsfield import HiggsfieldProvider

    note = project["vault"] / "Studio" / "Models" / "fake-image.md"
    data, body = frontmatter.read(note)
    data.update(provider="higgsfield", endpoint="higgsfield/unknown", cost_eur=0.5)
    frontmatter.write(note, data, body)
    monkeypatch.setattr("backlot.gen.get_provider", lambda name, cfg=None: HiggsfieldProvider(cfg))
    code, result = direct("gen", "img", "--model", "fake-image", "--prompt", "p", "--yes")
    assert code == 1 and "not configured" in result["error"]
    assert not FakeProvider.calls and not list((project["root"] / "takes").glob("img-*"))


def test_comfy_zero_requires_exact_workflow_evidence(project, monkeypatch):
    from backlot.providers.comfyui_local import WORKFLOWS_DIR

    note = project["vault"] / "Studio" / "Models" / "fake-image.md"
    data, body = frontmatter.read(note)
    data.update(provider="comfyui-local", endpoint="workflows/comfyui-ltx23-gguf.json", cost_eur=0.0)
    frontmatter.write(note, data, body)
    monkeypatch.setattr("backlot.gen.get_provider", lambda name, cfg=None: FakeProvider(cfg))
    code, result = direct("gen", "img", "--model", "fake-image", "--prompt", "p", "--yes")
    assert code == 1 and "local_zero_evidence" in result["error"] and not FakeProvider.calls
    data["local_zero_evidence"] = {"source": "verified local workflow inventory", "model": "fake-image",
                                   "route": "workflows/comfyui-ltx23-gguf.json", "verified_at": "2026-10-01T00:00:00Z",
                                   "cost_scope": "local_only", "workflow_sha256": file_hash(WORKFLOWS_DIR / "comfyui-ltx23-gguf.json")}
    frontmatter.write(note, data, body)
    code, result = direct("gen", "img", "--model", "fake-image", "--prompt", "p", "--yes")
    assert code == 0 and result[0]["cost_eur"] == 0 and len(FakeProvider.calls) == 1

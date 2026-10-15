from __future__ import annotations

import io
import json
from contextlib import redirect_stdout
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest
import yaml

from backlot import cli, expenses, takes
from backlot.authority import authorize, quote
from backlot.config import load_studio
from backlot.decisions import list_decisions
from backlot.errors import BacklotError, EXIT_CONFIRM
from backlot.gen import GenOptions, plan
from backlot.project import load_project_dir
from backlot.scaffold import validate_hook_settings
from tests.conftest import FakeProvider
from tests.conftest import run_json


def direct(*args: str):
    buf = io.StringIO()
    with redirect_stdout(buf):
        code = cli.main([*args, "--json"])
    return code, json.loads(buf.getvalue().strip().splitlines()[-1])


def expiry() -> str:
    return (datetime.now(timezone.utc) + timedelta(hours=1)).isoformat()


def approve_quote(project, quoted):
    return authorize(load_project_dir(project["root"]), quoted,
                     source_message="Yes, submit this exact call with these inputs and estimate.",
                     source_ref="thread-1/message-42", balance_amount=10.0,
                     balance_unit="EUR", balance_source="provider account page, just checked",
                     expires_at=expiry())["id"]


def test_yes_alone_cannot_submit_and_exact_approval_is_one_use(project):
    call = ("gen", "img", "--model", "fake-image", "--prompt", "red cube")
    code, data = direct(*call, "--yes")
    assert code == EXIT_CONFIRM and data["needs_confirmation"] and not FakeProvider.calls
    code, data = direct(*call, "--dry-run")
    assert code == 0 and data["quote"]["balance"]["status"] == "unavailable"
    quote_path = project["root"] / "quote.json"
    quote_path.write_text(json.dumps(data))
    code, auth = direct("authorize", str(quote_path), "--source-message", "Yes, submit this exact call.",
                        "--source-ref", "thread-1/message-42", "--balance", "10",
                        "--balance-unit", "EUR", "--balance-source", "account page now",
                        "--expires", expiry())
    assert code == 0 and auth["state"] == "available"
    code, result = direct(*call, "--yes", "--authorization", auth["id"])
    assert code == 0 and result[0]["take"] == "img-001" and len(FakeProvider.calls) == 1
    code, data = direct(*call, "--yes", "--authorization", auth["id"])
    assert code == EXIT_CONFIRM and "cannot be reused" in data["error"] and len(FakeProvider.calls) == 1


def test_authorization_fails_closed_on_changed_input_route_and_expiry(project):
    proj = load_project_dir(project["root"])
    studio = load_studio()
    q = plan(studio, proj, GenOptions(kind="img", model_id="fake-image", prompt="first")).quote
    auth_id = approve_quote(project, q)
    code, data = direct("gen", "img", "--model", "fake-image", "--prompt", "changed", "--yes", "--authorization", auth_id)
    assert code == EXIT_CONFIRM and "does not match" in data["error"]
    code, data = direct("tts", "--model", "fake-tts", "--voice", "v", "--text", "first", "--yes", "--authorization", auth_id)
    assert code == EXIT_CONFIRM and "does not match" in data["error"]
    path = proj.vault_project / "Records" / "spend" / f"{auth_id}.yaml"
    record = yaml.safe_load(path.read_text())
    record["expires_at"] = "2000-01-01T00:00:00+00:00"
    path.write_text(yaml.safe_dump(record))
    code, data = direct("gen", "img", "--model", "fake-image", "--prompt", "first", "--yes", "--authorization", auth_id)
    assert code == EXIT_CONFIRM and "expired" in data["error"] and not FakeProvider.calls


def test_batch_only_submits_the_two_explicitly_approved_calls(project):
    batch = project["root"] / "two.yaml"
    batch.write_text(yaml.safe_dump({"requests": [
        {"kind": "img", "model": "fake-image", "prompt": "character A"},
        {"kind": "img", "model": "fake-image", "prompt": "character B"},
    ]}))
    code, data = direct("batch", str(batch), "--dry-run")
    assert code == 0 and len(data["quotes"]) == 2
    auths = [approve_quote(project, q) for q in data["quotes"]]
    hall = project["root"] / "hall.yaml"
    hall.write_text(yaml.safe_dump({"requests": yaml.safe_load(batch.read_text())["requests"] + [
        {"kind": "img", "model": "fake-image", "prompt": "hall prompt feedback only"}]}))
    code, data = direct("batch", str(hall), "--yes", "--authorization", auths[0], "--authorization", auths[1])
    assert code == EXIT_CONFIRM and not FakeProvider.calls
    code, data = direct("batch", str(batch), "--yes", "--authorization", auths[0], "--authorization", auths[1])
    assert code == 0 and data["takes"] == ["img-001", "img-002"] and len(FakeProvider.calls) == 2


def test_scoped_picture_score_and_share_decisions_drive_handoff(project):
    for kind, name, version in (("picture", "silent-v3", "a" * 64),
                                ("scored", "scored-v2", "b" * 64),
                                ("share", "scored-share", "b" * 64)):
        code, _ = direct("decision", "approve", kind, name, "--version", version,
                         "--scope", f"{kind} only", "--reason", "accepted",
                         "--source-ref", f"thread/message-{kind}",
                         "--source-message", f"Yes to this {kind} version.")
        assert code == 0
    records = list_decisions(load_project_dir(project["root"]))
    assert [r["subject_type"] for r in records] == ["picture", "scored", "share"]
    handoff = (project["vault_project"] / "Handoff.md").read_text()
    assert "picture: `silent-v3`" in handoff
    assert "scored: `scored-v2`" in handoff
    assert "Current approved variant: `scored-share` (share)" in handoff
    code, _ = direct("handoff", "--claim", "House / S012", "--worker", "editor", "--base-revision", "0")
    assert code == 0
    code, data = direct("handoff", "--claim", "House / S012", "--worker", "other", "--base-revision", "0")
    assert code == 1 and "expected revision" in data["error"]


def test_ordered_media_hashes_change_the_quote(project):
    from backlot.models import find_model
    from backlot.providers.base import GenRequest

    model_path = project["vault"] / "Studio" / "Models" / "fake-edit.md"
    model_path.write_text(model_path.read_text().replace("status: disabled", "status: active"))
    model = find_model(project["vault"], "fake-edit")
    a = project["root"] / "inputs" / "a.png"
    b = project["root"] / "inputs" / "b.png"
    a.write_bytes(b"A")
    b.write_bytes(b"B")
    first = quote(model, GenRequest(prompt="p", images=[a, b]), cost_eur=0.1)
    second = quote(model, GenRequest(prompt="p", images=[b, a]), cost_eur=0.1)
    assert first["fingerprint"] != second["fingerprint"]
    assert first["request"]["media"]["image"][0]["name"] == "a.png"


def test_missing_spend_hook_is_visible(project):
    settings = project["root"] / ".claude" / "settings.json"
    settings.unlink()
    with pytest.raises(BacklotError, match="spend hook settings missing"):
        validate_hook_settings(settings)


def test_zero_cost_operation_needs_no_paid_authorization(project, monkeypatch):
    class Free(FakeProvider):
        def estimate(self, model, req):
            return 0.0

    model_path = project["vault"] / "Studio" / "Models" / "fake-image.md"
    model_path.write_text(model_path.read_text().replace("provider: fal", "provider: local").replace("cost_eur: 0.5", "cost_eur: 0.0"))
    monkeypatch.setattr("backlot.gen.get_provider", lambda name, cfg=None: Free(cfg))
    code, result = direct("gen", "img", "--model", "fake-image", "--prompt", "free")
    assert code == 0 and result[0]["cost_eur"] == 0.0


def test_accepted_captions_response_survives_parser_failure_and_recovers_without_create(project, monkeypatch):
    from backlot.providers.base import ProviderError

    run_json("tts", "--model", "fake-tts", "--text", "hello", "--yes")
    calls = []

    class NoTimestamps(FakeProvider):
        def call_json(self, model, req):
            calls.append("create")
            req.on_submit("paid-cap-job")
            return {"text": "hello"}

        def fetch_json(self, endpoint, request_id):
            raise ProviderError("saved raw response should be used first")

    monkeypatch.setattr("backlot.captions.get_provider", lambda name, cfg=None: NoTimestamps(cfg))
    code, data = direct("captions", "vo-001", "--model", "fake-stt", "--dry-run")
    auth_id = approve_quote(project, data["quote"])
    code, data = direct("captions", "vo-001", "--model", "fake-stt", "--yes", "--authorization", auth_id)
    assert code == 1 and "no timestamps" in data["error"]
    meta_path = project["root"] / "takes" / "cap-001" / "meta.yaml"
    meta = yaml.safe_load(meta_path.read_text())
    assert meta["request_id"] == "paid-cap-job" and meta["response"] == {"text": "hello"}
    assert meta["status"] == "failed" and meta["cost_eur"] == 0.01
    expense = expenses.list_expenses(load_project_dir(project["root"]))
    assert len(expense) == 2 and meta["expense_id"]
    assert next(row for row in expense if row["id"] == meta["expense_id"])["charge_status"] == "unknown"
    assert "| cap-001 | cap |" in (project["vault_project"] / "Costs.md").read_text()
    auth = yaml.safe_load((project["vault_project"] / "Records" / "spend" / f"{auth_id}.yaml").read_text())
    assert auth["state"] == "completed" and auth["request_id"] == "paid-cap-job"
    monkeypatch.setattr("backlot.captions.normalize_words", lambda result: ("hello", [{"start": 0.0, "end": 0.5, "text": "hello"}]))
    code, recovered = direct("recover", "cap-001")
    assert code == 0 and recovered["status"] == "new" and calls == ["create"]


def test_paid_captions_poll_failure_recovers_by_job_id_without_resubmit(project, monkeypatch):
    from backlot.providers.base import ProviderError

    run_json("tts", "--model", "fake-tts", "--text", "hello", "--yes")
    calls = []

    class RetryFetch(FakeProvider):
        def call_json(self, model, req):
            calls.append("create")
            req.on_submit("cap-poll-job")
            raise ProviderError("poll interrupted")

        def fetch_json(self, endpoint, request_id):
            calls.append("fetch")
            assert request_id == "cap-poll-job"
            return {"words": [{"text": "hello", "start": 0, "end": 0.5}]}

    monkeypatch.setattr("backlot.captions.get_provider", lambda name, cfg=None: RetryFetch(cfg))
    code, data = direct("captions", "vo-001", "--model", "fake-stt", "--dry-run")
    auth_id = approve_quote(project, data["quote"])
    code, data = direct("captions", "vo-001", "--model", "fake-stt", "--yes", "--authorization", auth_id)
    assert code == 1 and "poll interrupted" in data["error"]
    code, recovered = direct("recover", "cap-001")
    assert code == 0 and recovered["status"] == "new" and calls == ["create", "fetch"]
    proj = load_project_dir(project["root"])
    expense = next(row for row in expenses.list_expenses(proj) if row["id"] == recovered["expense_id"])
    assert expense["operation_id"] == "cap-poll-job" and expense["charge_status"] == "unknown"


def test_pre_submit_failure_has_no_expense_but_accepted_unknown_job_does(project, monkeypatch):
    from backlot.providers.base import ProviderError, ProviderPreSubmitError

    class BeforeSubmit(FakeProvider):
        def run(self, model, req):
            raise ProviderPreSubmitError("cannot submit")

    class AcceptedWithoutId(FakeProvider):
        def run(self, model, req):
            raise ProviderError("accepted but job id unavailable")

    call = ("gen", "img", "--model", "fake-image", "--prompt", "p")
    code, quoted = direct(*call, "--dry-run")
    assert code == 0
    first_auth = approve_quote(project, quoted["quote"])
    monkeypatch.setattr("backlot.gen.get_provider", lambda name, cfg=None: BeforeSubmit(cfg))
    code, _ = direct(*call, "--yes", "--authorization", first_auth)
    proj = load_project_dir(project["root"])
    assert code == 1 and expenses.list_expenses(proj) == [] and takes.list_takes(proj) == []
    second_auth = approve_quote(project, quoted["quote"])
    monkeypatch.setattr("backlot.gen.get_provider", lambda name, cfg=None: AcceptedWithoutId(cfg))
    code, data = direct(*call, "--yes", "--authorization", second_auth)
    assert code == 1 and "uncertain" in data["error"]
    failed = takes.load_take(proj, "img-001")
    assert failed.status == "failed" and failed.request_id == "" and failed.expense_id
    rows = expenses.list_expenses(proj)
    assert len(rows) == 1 and rows[0]["operation_id"] is None
    assert rows[0]["charge_status"] == "unknown" and rows[0]["estimate"]["amount"] == 0.5


def test_fal_without_request_id_never_polls(project, monkeypatch):
    from backlot.models import find_model
    from backlot.providers.base import GenRequest, ProviderError
    from backlot.providers.fal import FalProvider

    class Handler:
        request_id = ""

        def status(self):
            pytest.fail("accepted submission without ID must not poll")

    class Client:
        def submit(self, endpoint, arguments):
            return Handler()

    monkeypatch.setattr(FalProvider, "_client", lambda self: Client())
    model = find_model(project["vault"], "fake-image")
    with pytest.raises(ProviderError, match="without a request id"):
        FalProvider()._subscribe(model, GenRequest(prompt="p"))


def test_input_mutation_after_reservation_cannot_reach_provider(project, monkeypatch):
    from backlot import authority

    model_path = project["vault"] / "Studio" / "Models" / "fake-edit.md"
    model_path.write_text(model_path.read_text().replace("status: disabled", "status: active"))
    source = project["root"] / "inputs" / "reference.png"
    source.write_bytes(b"approved bytes")
    args = ("gen", "img", "--model", "fake-edit", "--prompt", "p", "--image", str(source))
    code, data = direct(*args, "--dry-run")
    auth_id = approve_quote(project, data["quote"])
    original_reserve = authority.reserve

    def change_after_reserve(proj, record_id, quoted):
        result = original_reserve(proj, record_id, quoted)
        source.write_bytes(b"different bytes")
        return result

    monkeypatch.setattr(authority, "reserve", change_after_reserve)
    code, data = direct(*args, "--yes", "--authorization", auth_id)
    assert code == 1 and "changed after approval" in data["error"] and not FakeProvider.calls
    record = yaml.safe_load((project["vault_project"] / "Records" / "spend" / f"{auth_id}.yaml").read_text())
    assert record["state"] == "available"


def test_disappeared_input_during_staging_releases_spend_reservation(project, monkeypatch):
    from backlot import authority, takes

    model_path = project["vault"] / "Studio" / "Models" / "fake-edit.md"
    model_path.write_text(model_path.read_text().replace("status: disabled", "status: active"))
    source = project["root"] / "inputs" / "reference.png"
    source.write_bytes(b"approved bytes")
    args = ("gen", "img", "--model", "fake-edit", "--prompt", "p", "--image", str(source))
    code, data = direct(*args, "--dry-run")
    assert code == 0
    auth_id = approve_quote(project, data["quote"])
    original_reserve = authority.reserve

    def disappear_after_reserve(proj, record_id, quoted):
        result = original_reserve(proj, record_id, quoted)
        source.unlink()
        return result

    monkeypatch.setattr(authority, "reserve", disappear_after_reserve)
    code, data = direct(*args, "--yes", "--authorization", auth_id)
    assert code == 1 and "could not stage approved input" in data["error"]
    assert not FakeProvider.calls
    record = yaml.safe_load((project["vault_project"] / "Records" / "spend" / f"{auth_id}.yaml").read_text())
    assert record["state"] == "available"
    assert takes.spent_eur(load_project_dir(project["root"])) == 0
    assert not (project["root"] / "takes" / "img-001").exists()


def test_handoff_latest_rejection_revokes_same_scoped_version(project):
    common = ("share", "scored-share", "--version", "c" * 64, "--scope", "remote copy",
              "--reason", "reviewed", "--source-ref", "thread/message-1", "--source-message", "Yes, share this.")
    assert direct("decision", "approve", *common)[0] == 0
    assert "Current approved variant: `scored-share`" in (project["vault_project"] / "Handoff.md").read_text()
    assert direct("decision", "reject", *common)[0] == 0
    handoff = (project["vault_project"] / "Handoff.md").read_text()
    assert "share: no typed approval recorded" in handoff
    assert "Current approved variant: unregistered" in handoff


def test_expiry_after_upload_prevents_fal_submit(project, monkeypatch):
    from backlot.providers.fal import FalProvider

    model_path = project["vault"] / "Studio" / "Models" / "fake-edit.md"
    model_path.write_text(model_path.read_text().replace("status: disabled", "status: active"))
    source = project["root"] / "inputs" / "reference.png"
    source.write_bytes(b"approved bytes")
    args = ("gen", "img", "--model", "fake-edit", "--prompt", "p", "--image", str(source))
    code, data = direct(*args, "--dry-run")
    auth_id = approve_quote(project, data["quote"])
    auth_path = project["vault_project"] / "Records" / "spend" / f"{auth_id}.yaml"
    submissions = []

    class Client:
        def upload_file(self, path):
            assert Path(path).read_bytes() == b"approved bytes"
            record = yaml.safe_load(auth_path.read_text())
            record["expires_at"] = "2000-01-01T00:00:00+00:00"
            auth_path.write_text(yaml.safe_dump(record))
            return "https://fake/uploaded"

        def submit(self, endpoint, arguments):
            submissions.append(arguments)
            pytest.fail("expired authorization must stop before submit")

    monkeypatch.setattr(FalProvider, "_client", lambda self: Client())
    monkeypatch.setattr("backlot.gen.get_provider", lambda name, cfg=None: FalProvider(cfg))
    code, data = direct(*args, "--yes", "--authorization", auth_id)
    assert code == 1 and "expired before provider submission" in data["error"]
    assert not submissions and not (project["root"] / "takes" / "img-001").exists()

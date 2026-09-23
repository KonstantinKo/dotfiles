"""ComfyUI Desktop provider: workflow JSON with placeholders -> /prompt, poll /history, fetch /view."""

from __future__ import annotations

import json
import random
import time
import uuid
from pathlib import Path
from typing import Any

import httpx

from backlot.models import ModelSpec
from backlot.providers.base import BaseProvider, GenRequest, GenResult, ProviderError

WORKFLOWS_DIR = Path(__file__).resolve().parent.parent.parent / "workflows"


def workflow_path(model: ModelSpec) -> Path:
    name = str(model.extra.get("workflow") or model.endpoint or model.id)
    if name.startswith("workflows/"):
        name = name[len("workflows/"):]
    path = Path(name)
    if not path.is_absolute():
        path = WORKFLOWS_DIR / (name if name.endswith(".json") else f"{name}.json")
    return path


def substitute(node: Any, values: dict[str, Any]) -> Any:
    """Replace {{name}} placeholders. A string that is exactly one placeholder takes the typed value."""
    if isinstance(node, dict):
        return {k: substitute(v, values) for k, v in node.items()}
    if isinstance(node, list):
        return [substitute(v, values) for v in node]
    if isinstance(node, str):
        stripped = node.strip()
        if stripped.startswith("{{") and stripped.endswith("}}") and stripped.count("{{") == 1:
            key = stripped[2:-2].strip()
            if key in values:
                return values[key]
            raise ProviderError(f"workflow placeholder {{{{{key}}}}} has no value")
        out = node
        for key, value in values.items():
            out = out.replace("{{" + key + "}}", str(value))
        return out
    return node


class ComfyUILocalProvider(BaseProvider):
    name = "comfyui-local"

    @property
    def url(self) -> str:
        return str(self.config.get("url") or "http://127.0.0.1:8188").rstrip("/")

    def reachable(self, timeout: float = 2.0) -> bool:
        try:
            return httpx.get(f"{self.url}/system_stats", timeout=timeout).status_code == 200
        except httpx.HTTPError:
            return False

    def estimate(self, model: ModelSpec, req: GenRequest) -> float:
        return 0.0 if model.cost_eur == 0 else super().estimate(model, req)

    def _upload(self, path: Path) -> str:
        with path.open("rb") as fh:
            resp = httpx.post(f"{self.url}/upload/image", files={"image": (path.name, fh)}, timeout=60)
        resp.raise_for_status()
        data = resp.json()
        name = data.get("name", path.name)
        sub = data.get("subfolder")
        return f"{sub}/{name}" if sub else name

    def _values(self, model: ModelSpec, req: GenRequest, template_text: str = "") -> dict[str, Any]:
        """Placeholder values. `{{frames}}` is derived from the request duration x fps when the
        template uses it; `{{image}}` is the uploaded input image and must exist in the template
        whenever an image is given."""
        values: dict[str, Any] = {"seed": random.randint(0, 2**31 - 1)}
        values.update(model.defaults)
        values["prompt"] = req.prompt or req.text
        values["negative_prompt"] = req.params.get("negative_prompt", model.defaults.get("negative_prompt", ""))
        if req.image:
            if "{{image}}" not in template_text:
                raise ProviderError(f"workflow template has no {{{{image}}}} node ({workflow_path(model).name}); the model cannot take --image")
            values["image"] = self._upload(req.image)
        if req.audio:
            values["audio"] = self._upload(req.audio)
        if req.duration_s:
            values["duration"] = req.duration_s
        values.update(req.params)
        if "{{frames}}" in template_text and "frames" not in req.params and req.duration_s:
            fps = float(values.get("fps") or 24)
            values["frames"] = int(round(float(req.duration_s) * fps))
        if values.get("seed") in (None, -1, "-1"):
            values["seed"] = random.randint(0, 2**31 - 1)
        return values

    def run(self, model: ModelSpec, req: GenRequest) -> GenResult:
        path = workflow_path(model)
        if not path.exists():
            raise ProviderError(f"workflow template not found: {path}")
        text = path.read_text(encoding="utf-8")
        template = json.loads(text)
        template.pop("_comment", None)
        workflow = substitute(template, self._values(model, req, text))
        if not self.reachable():
            raise ProviderError(f"ComfyUI not reachable at {self.url}")
        client_id = uuid.uuid4().hex
        start = time.time()
        resp = httpx.post(f"{self.url}/prompt", json={"prompt": workflow, "client_id": client_id}, timeout=60)
        if resp.status_code != 200:
            raise ProviderError(f"ComfyUI rejected workflow: {resp.text[:400]}")
        prompt_id = resp.json().get("prompt_id")
        if not prompt_id:
            raise ProviderError(f"ComfyUI returned no prompt_id: {resp.text[:200]}")
        if req.on_submit:
            req.on_submit(str(prompt_id))
        history = self._wait(prompt_id, float(self.config.get("timeout_s", 3600)))
        files = self._collect(history, req.workdir)
        if not files:
            raise ProviderError("ComfyUI produced no outputs")
        return GenResult(files=files, job_id=prompt_id, seconds=time.time() - start, raw=history)

    def _wait(self, prompt_id: str, timeout_s: float) -> dict[str, Any]:
        deadline = time.time() + timeout_s
        while time.time() < deadline:
            resp = httpx.get(f"{self.url}/history/{prompt_id}", timeout=30)
            if resp.status_code == 200:
                entry = resp.json().get(prompt_id)
                if entry:
                    status = entry.get("status") or {}
                    if status.get("status_str") == "error":
                        raise ProviderError(f"ComfyUI job failed: {json.dumps(status)[:400]}")
                    if entry.get("outputs"):
                        return entry
            time.sleep(2)
        raise ProviderError(f"ComfyUI job {prompt_id} timed out after {timeout_s:.0f}s")

    def _collect(self, history: dict[str, Any], workdir: Path) -> list[Path]:
        workdir.mkdir(parents=True, exist_ok=True)
        files: list[Path] = []
        for node_out in (history.get("outputs") or {}).values():
            for key in ("videos", "gifs", "images", "audio"):
                for i, item in enumerate(node_out.get(key) or []):
                    if not isinstance(item, dict) or not item.get("filename"):
                        continue
                    if item.get("type") not in (None, "output"):
                        continue
                    params = {"filename": item["filename"], "subfolder": item.get("subfolder", ""), "type": item.get("type", "output")}
                    resp = httpx.get(f"{self.url}/view", params=params, timeout=300)
                    resp.raise_for_status()
                    ext = Path(item["filename"]).suffix or ".bin"
                    target = workdir / f"out{len(files) if files else ''}{ext}"
                    target.write_bytes(resp.content)
                    files.append(target)
        return files

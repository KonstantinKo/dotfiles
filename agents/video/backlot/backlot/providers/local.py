"""Local, no-network provider: TTS through the kokoro and edge-tts CLIs (~/.local/bin)."""

from __future__ import annotations

import os
import shutil
import subprocess
import time
from pathlib import Path

from backlot.models import ModelSpec
from backlot.providers.base import BaseProvider, GenRequest, GenResult, ProviderError

ENGINES = ("kokoro", "edge-tts")
DEFAULT_TIMEOUT_S = 120
KOKORO_CACHE = Path.home() / ".cache" / "huggingface" / "hub" / "models--hexgrad--Kokoro-82M"


def find_cli(name: str) -> str | None:
    found = shutil.which(name)
    if found:
        return found
    candidate = Path.home() / ".local" / "bin" / name
    return str(candidate) if candidate.exists() else None


class LocalProvider(BaseProvider):
    name = "local"

    def estimate(self, model: ModelSpec, req: GenRequest) -> float:
        return 0.0

    def run(self, model: ModelSpec, req: GenRequest) -> GenResult:
        engine = (model.endpoint or model.extra.get("engine") or "").strip()
        if engine not in ENGINES:
            raise ProviderError(f"model {model.id}: endpoint must be one of {ENGINES}, got {engine!r}")
        cli = find_cli(engine)
        if not cli:
            raise ProviderError(f"{engine} CLI not found on PATH or in ~/.local/bin")
        text = req.text or req.prompt
        if not text:
            raise ProviderError("tts needs text")
        voice = req.voice or str(model.defaults.get("voice") or "")
        params = {**model.defaults, **req.params}
        req.workdir.mkdir(parents=True, exist_ok=True)
        start = time.time()
        if engine == "kokoro":
            out = req.workdir / "out.wav"
            cmd = [cli, "-o", str(out), "-t", text]
            if voice:
                cmd += ["-m", voice]
            if "speed" in params:
                cmd += ["-s", str(params["speed"])]
            lang = params.get("lang") or params.get("language")
            if lang:
                cmd += ["-l", str(lang)]
        else:
            out = req.workdir / "out.mp3"
            cmd = [cli, "-t", text, "--write-media", str(out)]
            if voice:
                cmd += ["-v", voice]
            for flag in ("rate", "volume", "pitch"):
                if flag in params:
                    cmd += [f"--{flag}", str(params[flag])]
        env = dict(os.environ)
        if engine == "kokoro" and KOKORO_CACHE.is_dir():
            env.setdefault("HF_HUB_OFFLINE", "1")
        timeout = float(self.config.get("timeout_s") or DEFAULT_TIMEOUT_S)
        try:
            proc = subprocess.run(cmd, capture_output=True, text=True, check=False, timeout=timeout, env=env)
        except subprocess.TimeoutExpired as exc:
            hint = "; use the edge-tts model instead" if engine == "kokoro" else ""
            raise ProviderError(f"{engine} timed out after {timeout:.0f} s (providers.local.timeout_s in studio.yaml){hint}") from exc
        except OSError as exc:
            raise ProviderError(f"{engine} could not start: {exc}") from exc
        if proc.returncode != 0 or not out.exists():
            raise ProviderError(f"{engine} failed: {(proc.stderr or proc.stdout).strip()[:400]}")
        return GenResult(files=[out], job_id="", seconds=time.time() - start, raw={"cmd": cmd})

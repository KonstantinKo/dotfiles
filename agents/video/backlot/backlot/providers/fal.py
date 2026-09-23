"""fal.ai provider via fal_client. Key from env FAL_KEY or the macOS Keychain; never written to disk."""

from __future__ import annotations

import mimetypes
import os
import subprocess
import time
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

from backlot.models import ModelSpec
from backlot.providers.base import BaseProvider, GenRequest, GenResult, ProviderError, build_arguments

DEFAULT_TIMEOUT_S = 900.0
POLL_INTERVAL_S = 1.0
_MEDIA_EXT = {".png", ".jpg", ".jpeg", ".webp", ".gif", ".mp4", ".mov", ".webm", ".mp3", ".wav", ".ogg", ".flac", ".m4a"}
_URL_KEYS = ("images", "image", "video", "audio", "output", "outputs", "file", "audio_file", "video_file", "image_file")


def keychain_key(service: str = "fal-api", account: str = "FAL_KEY") -> str | None:
    try:
        out = subprocess.run(
            ["security", "find-generic-password", "-s", service, "-a", account, "-w"],
            capture_output=True, text=True, timeout=10, check=False,
        )
    except (OSError, subprocess.SubprocessError):
        return None
    key = out.stdout.strip()
    return key or None


def has_key(config: dict[str, Any] | None = None) -> bool:
    return bool(resolve_key(config or {}))


def resolve_key(config: dict[str, Any]) -> str | None:
    return os.environ.get("FAL_KEY") or keychain_key(
        str(config.get("keychain_service", "fal-api")), str(config.get("keychain_account", "FAL_KEY"))
    )


def extract_media(result: Any) -> list[str]:
    """Collect media URLs from a fal result, in order, across the common response shapes."""
    urls: list[str] = []

    def looks_like_media(url: str) -> bool:
        return url.startswith("http") and (Path(urlparse(url).path).suffix.lower() in _MEDIA_EXT or "fal.media" in url)

    def walk(node: Any) -> None:
        if isinstance(node, dict):
            if isinstance(node.get("url"), str) and (node.get("content_type") or node.get("file_name") or looks_like_media(node["url"])):
                urls.append(node["url"])
                return
            for key, value in node.items():
                if isinstance(value, str) and key.endswith("_url") and looks_like_media(value):
                    urls.append(value)
                elif key in _URL_KEYS or isinstance(value, (dict, list)):
                    walk(value)
        elif isinstance(node, list):
            for item in node:
                walk(item)

    walk(result)
    seen: set[str] = set()
    return [u for u in urls if not (u in seen or seen.add(u))]


class FalProvider(BaseProvider):
    name = "fal"

    def _client(self):
        key = resolve_key(self.config)
        if not key:
            raise ProviderError("no FAL_KEY in env or Keychain (service fal-api, account FAL_KEY)")
        os.environ["FAL_KEY"] = key
        import fal_client

        return fal_client

    def _upload(self, path: Path) -> str:
        client = self._client()
        try:
            return client.upload_file(str(path))
        except Exception as exc:  # noqa: BLE001 - fal_client raises many exception types
            raise ProviderError(f"upload of {path.name} failed: {_short(exc)}") from exc

    @property
    def timeout_s(self) -> float:
        return float(self.config.get("timeout_s") or DEFAULT_TIMEOUT_S)

    def _subscribe(self, model: ModelSpec, req: GenRequest) -> tuple[Any, str, float]:
        """submit, hand the request id to the caller (recorded before any waiting), then poll
        the status until completed or `timeout_s`; the result is only read when it is complete."""
        client = self._client()
        if not model.endpoint:
            raise ProviderError(f"model {model.id} has no endpoint")
        args = build_arguments(model, req, self._upload)
        start = time.time()
        request_id = ""
        try:
            handler = client.submit(model.endpoint, arguments=args)
            request_id = str(getattr(handler, "request_id", "") or "")
            if req.on_submit and request_id:
                req.on_submit(request_id)
            deadline = start + self.timeout_s
            while not isinstance(handler.status(), client.Completed):
                if time.time() >= deadline:
                    raise ProviderError(
                        f"{model.endpoint} request {request_id} still running after {self.timeout_s:.0f} s "
                        "(providers.fal.timeout_s in studio.yaml); `backlot recover <take>` fetches it once it finishes"
                    )
                time.sleep(POLL_INTERVAL_S)
            result = handler.get()
        except ProviderError:
            raise
        except Exception as exc:  # noqa: BLE001
            raise ProviderError(f"{model.endpoint} failed: {_short(exc)}") from exc
        return result, request_id, time.time() - start

    def call_json(self, model: ModelSpec, req: GenRequest) -> dict[str, Any]:
        result, _, _ = self._subscribe(model, req)
        return result if isinstance(result, dict) else {"result": result}

    def run(self, model: ModelSpec, req: GenRequest) -> GenResult:
        result, request_id, seconds = self._subscribe(model, req)
        files = _download_all(result, req.workdir)
        return GenResult(files=files, job_id=request_id, seconds=seconds, raw=result)

    def fetch(self, endpoint: str, request_id: str, workdir: Path) -> GenResult:
        client = self._client()
        try:
            status = client.status(endpoint, request_id)
            if not isinstance(status, client.Completed):
                raise ProviderError(f"request {request_id} on {endpoint} is {type(status).__name__.lower()}; try again later")
            result = client.result(endpoint, request_id)
        except ProviderError:
            raise
        except Exception as exc:  # noqa: BLE001
            raise ProviderError(f"{endpoint} result {request_id} failed: {_short(exc)}") from exc
        return GenResult(files=_download_all(result, workdir), job_id=request_id, raw=result)


def _download_all(result: Any, workdir: Path) -> list[Path]:
    urls = extract_media(result)
    if not urls:
        raise ProviderError(f"no media in fal response: {str(result)[:300]}")
    return [download(url, workdir, f"out{i if i else ''}") for i, url in enumerate(urls)]


def _short(exc: BaseException) -> str:
    text = str(exc).strip() or exc.__class__.__name__
    return text.splitlines()[0][:300]


def download(url: str, workdir: Path, stem: str) -> Path:
    import httpx

    workdir.mkdir(parents=True, exist_ok=True)
    try:
        with httpx.stream("GET", url, follow_redirects=True, timeout=120) as resp:
            resp.raise_for_status()
            ext = Path(urlparse(url).path).suffix.lower()
            if ext not in _MEDIA_EXT:
                ext = mimetypes.guess_extension(resp.headers.get("content-type", "").split(";")[0]) or ".bin"
            target = workdir / f"{stem}{ext}"
            with target.open("wb") as fh:
                for chunk in resp.iter_bytes():
                    fh.write(chunk)
    except (httpx.HTTPError, OSError) as exc:
        raise ProviderError(f"download of {url} failed: {_short(exc)}") from exc
    return target

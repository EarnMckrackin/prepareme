"""
Prep Suite Generator — Vercel serverless front end.

Upload a document (or paste text) + an instruction + pick kid/adult + pick a model
provider  ->  generate  ->  the finished interactive course HTML is returned inline and
the browser opens / downloads it as a standalone file.

Serverless notes:
  - No disk persistence (the function filesystem is ephemeral/read-only). The generated
    course is sent back in the JSON response and the browser turns it into a Blob URL.
  - Model calls go to hosted providers over HTTP. Default is Gemini (free tier). Users can
    paste their own key (BYOK) to use any provider without server-side keys.

Local dev:
    pip install -r requirements.txt
    export GEMINI_API_KEY=...        # or GROQ_API_KEY / XAI_API_KEY / OPENAI_API_KEY / ANTHROPIC_API_KEY
    uvicorn api.index:app --reload --port 8000
"""

import asyncio
import base64
import functools
import ipaddress
import os
import socket
import time
from collections import defaultdict
from pathlib import Path
from urllib.parse import urlparse

import httpx

from fastapi import FastAPI, Request, UploadFile, File, Form, HTTPException
from fastapi.responses import HTMLResponse

import sys
sys.path.insert(0, str(Path(__file__).parent))
from _generator import (  # noqa: E402
    build_course, extract_main_text, normalize_url,
    GenerationError, resolve_provider, ENV_KEYS,
)

# ---------- rate limiting (sliding window, per IP, in-process) ---------------
# Resets on cold start — fine for serverless; protects within a warm instance.
_RATE_LIMIT = 10          # max requests
_RATE_WINDOW = 60         # per this many seconds
_rate_window: dict[str, list[float]] = defaultdict(list)


def _check_rate_limit(ip: str) -> bool:
    now = time.monotonic()
    bucket = _rate_window[ip]
    bucket[:] = [t for t in bucket if now - t < _RATE_WINDOW]
    if len(bucket) >= _RATE_LIMIT:
        return False
    bucket.append(now)
    return True


# ---------- SSRF guard -------------------------------------------------------
_MAX_UPLOAD_BYTES = 10 * 1024 * 1024  # 10 MB


def _assert_public_url(url: str) -> None:
    """Block URLs that resolve to private/reserved addresses (SSRF mitigation)."""
    parsed = urlparse(url)
    if parsed.scheme not in ("http", "https"):
        raise GenerationError("Only http/https URLs are supported.")
    host = parsed.hostname
    if not host:
        raise GenerationError(f"Invalid URL: {url}")
    try:
        addr = ipaddress.ip_address(socket.gethostbyname(host))
    except (socket.gaierror, ValueError):
        raise GenerationError(f"Could not resolve host: {host}")
    if (addr.is_private or addr.is_loopback or addr.is_link_local
            or addr.is_reserved or addr.is_multicast or addr.is_unspecified):
        raise GenerationError(f"Fetching that URL is not permitted.")


# ---------- concurrent URL fetching -----------------------------------------
_URL_TIMEOUT = httpx.Timeout(30.0, connect=10.0)
_MAX_CONCURRENT_URLS = 5


async def fetch_urls(urls: list[str]) -> list[tuple[str, str]]:
    """Fetch many URLs concurrently and return [(url, extracted_text)] in input order.

    Raises GenerationError on the first URL that can't be fetched.
    """
    sem = asyncio.Semaphore(_MAX_CONCURRENT_URLS)
    headers = {"User-Agent": "Mozilla/5.0 (PrepSuiteBot)"}

    async with httpx.AsyncClient(timeout=_URL_TIMEOUT, follow_redirects=True,
                                 headers=headers) as client:
        async def one(raw: str) -> tuple[str, str]:
            url = normalize_url(raw)
            # SSRF guard — runs DNS resolution in a thread to keep the event loop free
            await asyncio.to_thread(_assert_public_url, url)
            async with sem:
                try:
                    r = await client.get(url)
                except httpx.HTTPError as e:
                    raise GenerationError(f"Could not fetch {url} ({type(e).__name__}).")
            if r.status_code != 200:
                raise GenerationError(f"Could not fetch {url} (HTTP {r.status_code}).")
            # extraction is CPU-bound; run it off the event loop
            text = await asyncio.to_thread(extract_main_text, r.text, url)
            if not text:
                raise GenerationError(f"Fetched {url} but found no readable text.")
            return url, text

        return await asyncio.gather(*(one(u) for u in urls))

# ----------------------------------------------------------------------------
APP_DIR = Path(__file__).parent
TEMPLATE_PATH = APP_DIR / "_course_template.html"
UPLOAD_PAGE = (APP_DIR / "_ui.html").read_text(encoding="utf-8")

# Default provider when the form doesn't specify one. Free tier first.
DEFAULT_BACKEND = os.environ.get("PREP_BACKEND", "gemini")

app = FastAPI(title="Prep Suite Generator")


# ---------- document extraction ---------------------------------------------
def extract_text(filename: str, raw: bytes) -> str:
    """Pull plain text out of an uploaded file. Supports txt/md/pdf/docx."""
    ext = Path(filename).suffix.lower()
    if ext in (".txt", ".md", ".markdown", ".csv"):
        return raw.decode("utf-8", errors="replace")
    if ext == ".pdf":
        try:
            from pypdf import PdfReader
            import io
        except ImportError:
            raise GenerationError("PDF support needs pypdf (it's in requirements.txt).")
        try:
            reader = PdfReader(io.BytesIO(raw))
            return "\n\n".join((p.extract_text() or "") for p in reader.pages)
        except Exception as e:
            raise GenerationError(f"Could not read that PDF ({type(e).__name__}). "
                                  "Try pasting the text instead.")
    if ext == ".docx":
        try:
            import io, docx
        except ImportError:
            raise GenerationError("DOCX support needs python-docx (it's in requirements.txt).")
        try:
            d = docx.Document(io.BytesIO(raw))
            return "\n\n".join(p.text for p in d.paragraphs if p.text.strip())
        except Exception as e:
            raise GenerationError(f"Could not read that DOCX ({type(e).__name__}). "
                                  "Try pasting the text instead.")
    return raw.decode("utf-8", errors="replace")


# ---------- routes ----------------------------------------------------------
@app.get("/", response_class=HTMLResponse)
def home():
    return UPLOAD_PAGE


@app.get("/api/config")
def config():
    """Tell the UI which providers already have a server-side key configured."""
    return {
        "default": resolve_provider(DEFAULT_BACKEND),
        "configured": {p: bool(os.environ.get(env, "").strip())
                       for p, env in ENV_KEYS.items()},
    }


@app.post("/api/generate")
async def generate(
    request: Request,
    instruction: str = Form(""),
    learner: str = Form("adult"),
    grade: str = Form(""),
    context: str = Form(""),
    pasted: str = Form(""),
    urls: str = Form(""),
    provider: str = Form(""),
    api_key: str = Form(""),
    file: UploadFile | None = File(None),
):
    # Rate limit: 10 requests/minute per IP (x-forwarded-for on Vercel)
    forwarded = request.headers.get("x-forwarded-for", "")
    client_ip = forwarded.split(",")[0].strip() or (request.client.host if request.client else "unknown")
    if not _check_rate_limit(client_ip):
        raise HTTPException(429, "Too many requests — please wait a moment and try again.")

    material_parts = []

    # 1) uploaded document
    if file is not None and file.filename:
        raw = await file.read()
        if len(raw) > _MAX_UPLOAD_BYTES:
            raise HTTPException(400, f"File is too large (max {_MAX_UPLOAD_BYTES // 1_048_576} MB).")
        try:
            material_parts.append(extract_text(file.filename, raw))
        except GenerationError as e:
            raise HTTPException(400, str(e))

    # 2) URLs (one per line) — fetched concurrently
    url_list = [ln.strip() for ln in urls.splitlines() if ln.strip()]
    if url_list:
        try:
            for src, text in await fetch_urls(url_list):
                material_parts.append(f"[Source: {src}]\n{text}")
        except GenerationError as e:
            raise HTTPException(400, str(e))

    # 3) pasted text
    if pasted.strip():
        material_parts.append(pasted.strip())

    material = "\n\n".join(p for p in material_parts if p.strip()).strip()

    if not material:
        raise HTTPException(400, "Provide a document, a URL, or paste some study material.")
    if not instruction.strip():
        raise HTTPException(400, "Add a one-line instruction (topic / focus / tone).")

    # Fold grade level into the audience signal for kid courses.
    learner = "kid" if learner == "kid" else "adult"
    instruction_full = instruction.strip()
    if learner == "kid" and grade.strip():
        instruction_full += f" (school grade level: {grade.strip()})"

    try:
        course, html = await asyncio.to_thread(
            functools.partial(
                build_course,
                instruction=instruction_full,
                material=material,
                learner=learner,
                context=context.strip(),
                template_path=TEMPLATE_PATH,
                provider=provider or DEFAULT_BACKEND,
                api_key=api_key,
            )
        )
    except GenerationError as e:
        raise HTTPException(422, f"Generation failed: {e}")

    title = course.get("meta", {}).get("title", "Untitled course")
    html_b64 = base64.b64encode(html.encode("utf-8")).decode("ascii")
    return {
        "title": title,
        "modules": len(course.get("modules", [])),
        "html_b64": html_b64,
    }


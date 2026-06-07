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
import hashlib
import hmac
import json
import ipaddress
import logging
import os
import re
import socket
import time
from collections import defaultdict
from pathlib import Path
from urllib.parse import urljoin, urlparse

import httpx

from fastapi import FastAPI, Request, UploadFile, File, Form, HTTPException
from fastapi.responses import FileResponse, HTMLResponse

import sys
sys.path.insert(0, str(Path(__file__).parent))
from _generator import (  # noqa: E402
    build_course, extract_main_text, inject, normalize_url, validate,
    GenerationError, resolve_provider, ENV_KEYS,
)
from _generated_courses import GENERATED_COURSES  # noqa: E402


log = logging.getLogger(__name__)

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


def _redis_rate_limit_config() -> tuple[str, str] | None:
    url = (os.environ.get("UPSTASH_REDIS_REST_URL")
           or os.environ.get("KV_REST_API_URL") or "").strip().rstrip("/")
    token = (os.environ.get("UPSTASH_REDIS_REST_TOKEN")
             or os.environ.get("KV_REST_API_TOKEN") or "").strip()
    if url and token:
        return url, token
    return None


async def _check_rate_limit_shared(ip: str) -> bool:
    cfg = _redis_rate_limit_config()
    if not cfg:
        return _check_rate_limit(ip)

    base_url, token = cfg
    window = int(time.time() // _RATE_WINDOW)
    key = f"prep-suite:rate:{ip}:{window}"
    payload = [["INCR", key], ["EXPIRE", key, _RATE_WINDOW + 5]]
    try:
        async with httpx.AsyncClient(timeout=httpx.Timeout(3.0, connect=1.0)) as client:
            r = await client.post(
                f"{base_url}/pipeline",
                headers={"Authorization": f"Bearer {token}"},
                json=payload,
            )
        if r.status_code != 200:
            log.warning("Shared rate limit failed HTTP %s: %s", r.status_code, r.text[:200])
            return _check_rate_limit(ip)
        data = r.json()
        count = int(data[0]["result"])
        return count <= _RATE_LIMIT
    except Exception as e:  # noqa: BLE001
        log.warning("Shared rate limit unavailable: %s", type(e).__name__)
        return _check_rate_limit(ip)


# ---------- SSRF guard -------------------------------------------------------
_MAX_UPLOAD_BYTES = 10 * 1024 * 1024  # 10 MB
_MAX_URL_FETCH_BYTES = 8 * 1024 * 1024  # 8 MB
_MAX_REQUEST_BYTES = 12 * 1024 * 1024  # includes multipart overhead
_MAX_TEXT_FIELDS = {
    "instruction": 2_000,
    "grade": 120,
    "learning_style": 80,
    "context": 12_000,
    "pasted": 120_000,
    "urls": 4_000,
    "web_search": 2_000,
    "model": 200,
    "api_key": 8_000,
    "username": 120,
    "passcode": 400,
}
_MAX_URLS = 10
_MAX_TAVILY_QUERIES = 5
_MAX_TAVILY_RESULT_CHARS = 40_000
_MAX_REDIRECTS = 3


def _assert_public_url(url: str) -> None:
    """Block URLs that resolve to private/reserved addresses (SSRF mitigation)."""
    parsed = urlparse(url)
    if parsed.scheme not in ("http", "https"):
        raise GenerationError("Only http/https URLs are supported.")
    host = parsed.hostname
    if not host:
        raise GenerationError(f"Invalid URL: {url}")
    port = parsed.port or (443 if parsed.scheme == "https" else 80)
    try:
        infos = socket.getaddrinfo(host, port, type=socket.SOCK_STREAM)
    except socket.gaierror:
        raise GenerationError(f"Could not resolve host: {host}")
    if not infos:
        raise GenerationError(f"Could not resolve host: {host}")
    for *_, sockaddr in infos:
        try:
            addr = ipaddress.ip_address(sockaddr[0])
        except ValueError:
            raise GenerationError(f"Could not resolve host safely: {host}")
        if (addr.is_private or addr.is_loopback or addr.is_link_local
                or addr.is_reserved or addr.is_multicast or addr.is_unspecified):
            raise GenerationError("Fetching that URL is not permitted.")


def _check_text_field(name: str, value: str) -> str:
    limit = _MAX_TEXT_FIELDS[name]
    if len(value.encode("utf-8")) > limit:
        raise HTTPException(400, f"{name} is too large (max {limit} bytes).")
    return value


async def _read_limited_response(r: httpx.Response, url: str) -> str:
    chunks: list[bytes] = []
    total = 0
    async for chunk in r.aiter_bytes():
        total += len(chunk)
        if total > _MAX_URL_FETCH_BYTES:
            mb = _MAX_URL_FETCH_BYTES // 1_048_576
            raise GenerationError(f"Could not fetch {url}: response is larger than {mb} MB.")
        chunks.append(chunk)
    encoding = getattr(r, "encoding", None) or "utf-8"
    return b"".join(chunks).decode(encoding, errors="replace")


def _blob_storage_enabled() -> bool:
    return (
        os.environ.get("PREP_STORE_COURSES", "").strip().lower() in {"1", "true", "yes"}
        and bool(os.environ.get("BLOB_READ_WRITE_TOKEN", "").strip())
    )


def _slugify_title(title: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", title.lower()).strip("-")
    return slug[:80] or "course"


def _store_course_blob(title: str, html: str) -> dict[str, str] | None:
    if not _blob_storage_enabled():
        return None
    try:
        from vercel.blob import BlobClient

        access = os.environ.get("PREP_BLOB_ACCESS", "public").strip().lower()
        if access not in {"public", "private"}:
            access = "public"
        client = BlobClient()
        blob = client.put(
            f"courses/{_slugify_title(title)}.html",
            html.encode("utf-8"),
            access=access,
            content_type="text/html; charset=utf-8",
            add_random_suffix=True,
        )
        return {
            "url": blob.url,
            "download_url": getattr(blob, "download_url", blob.url),
        }
    except Exception as e:  # noqa: BLE001
        log.warning("Blob storage unavailable: %s", type(e).__name__)
        return None


# ---------- concurrent URL fetching -----------------------------------------
_URL_TIMEOUT = httpx.Timeout(30.0, connect=10.0)
_MAX_CONCURRENT_URLS = 5


async def fetch_urls(urls: list[str]) -> list[tuple[str, str]]:
    """Fetch many URLs concurrently and return [(url, extracted_text)] in input order.

    Raises GenerationError on the first URL that can't be fetched.
    """
    sem = asyncio.Semaphore(_MAX_CONCURRENT_URLS)
    headers = {"User-Agent": "Mozilla/5.0 (PrepSuiteBot)"}

    async with httpx.AsyncClient(timeout=_URL_TIMEOUT, follow_redirects=False,
                                 headers=headers) as client:
        async def one(raw: str) -> tuple[str, str]:
            url = normalize_url(raw)
            async with sem:
                current_url = url
                body = ""
                for _ in range(_MAX_REDIRECTS + 1):
                    # SSRF guard — runs DNS resolution in a thread to keep the event loop free.
                    await asyncio.to_thread(_assert_public_url, current_url)
                    try:
                        async with client.stream("GET", current_url) as r:
                            if 300 <= r.status_code < 400:
                                location = r.headers.get("Location") or r.headers.get("location")
                                if not location:
                                    raise GenerationError(
                                        f"Could not fetch {url} (redirect without location).")
                                current_url = urljoin(current_url, location)
                                continue
                            if r.status_code != 200:
                                raise GenerationError(
                                    f"Could not fetch {url} (HTTP {r.status_code}).")
                            body = await _read_limited_response(r, url)
                            break
                    except httpx.HTTPError as e:
                        raise GenerationError(f"Could not fetch {url} ({type(e).__name__}).")
                else:
                    raise GenerationError(f"Could not fetch {url} (too many redirects).")
            # extraction is CPU-bound; run it off the event loop
            text = await asyncio.to_thread(extract_main_text, body, current_url)
            if not text:
                raise GenerationError(f"Fetched {url} but found no readable text.")
            return url, text

        return await asyncio.gather(*(one(u) for u in urls))


async def search_tavily(queries: list[str]) -> list[tuple[str, str]]:
    """Run Tavily searches and return [(query, readable_result_text)]."""
    api_key = os.environ.get("TAVILY_API_KEY", "").strip()
    if not api_key:
        raise GenerationError("Tavily web search needs TAVILY_API_KEY configured.")

    async with httpx.AsyncClient(timeout=httpx.Timeout(30.0, connect=10.0)) as client:
        async def one(query: str) -> tuple[str, str]:
            try:
                r = await client.post(
                    "https://api.tavily.com/search",
                    headers={"Authorization": f"Bearer {api_key}"},
                    json={
                        "query": query,
                        "topic": "general",
                        "search_depth": "basic",
                        "max_results": 5,
                        "include_answer": True,
                        "include_raw_content": "text",
                    },
                )
            except httpx.HTTPError as e:
                raise GenerationError(f"Tavily search failed for '{query}' ({type(e).__name__}).")
            if r.status_code in (401, 403):
                raise GenerationError("Tavily rejected TAVILY_API_KEY.")
            if r.status_code == 429:
                raise GenerationError("Tavily rate limit / quota hit. Try again later.")
            if r.status_code != 200:
                raise GenerationError(f"Tavily search failed for '{query}' (HTTP {r.status_code}).")

            data = r.json()
            parts = [f"Query: {query}"]
            answer = (data.get("answer") or "").strip()
            if answer:
                parts.append(f"Answer summary:\n{answer}")
            for item in data.get("results", []) or []:
                if not isinstance(item, dict):
                    continue
                title = (item.get("title") or "Untitled result").strip()
                url = (item.get("url") or "").strip()
                content = (item.get("raw_content") or item.get("content") or "").strip()
                if content:
                    parts.append(f"Source: {title}\nURL: {url}\n{content}")
            text = "\n\n".join(parts).strip()[:_MAX_TAVILY_RESULT_CHARS]
            if not text:
                raise GenerationError(f"Tavily returned no readable results for '{query}'.")
            return query, text

        return await asyncio.gather(*(one(q) for q in queries))

# ----------------------------------------------------------------------------
APP_DIR = Path(__file__).parent
TEMPLATE_PATH = APP_DIR / "_course_template.html"
COURSES_DIR = APP_DIR / "courses"
UPLOAD_PAGE = (APP_DIR / "_ui.html").read_text(encoding="utf-8")

LIBRARY_COURSES = [
    {
        "id": "gen-ai-learning-lab",
        "title": "Gen AI Learning Lab",
        "subtitle": "Advanced RAG & Agentic Systems",
        "description": (
            "A gated, mastery-tracked lab for fine-tuning decisions, LoRA, "
            "quantization, evaluation, and deployment tradeoffs."
        ),
        "tags": ["Gen AI", "RAG", "LoRA", "Evaluation"],
        "level": "Level 2",
        "modules": "5 stages",
        "href": "/courses/gen-ai-learning-lab.html",
    },
    {
        "id": "grayscale-interview-prep",
        "title": "Grayscale Interview Prep",
        "subtitle": "Principal PM interview room",
        "description": (
            "Generated course for Grayscale PPM interview practice, with "
            "company thesis, risk language, drills, flashcards, and answer patterns."
        ),
        "tags": ["Interview", "Grayscale", "PPM", "Fintech"],
        "level": "Generated",
        "modules": "8 modules",
        "href": "/courses/grayscale-interview-prep-generated.html",
        "gated": True,
    },
    {
        "id": "grayscale-ppm-mastery",
        "title": "Grayscale PPM Mastery",
        "subtitle": "Product, fintech, Web3, architecture",
        "description": (
            "Generated mastery course covering asset management, digital assets, "
            "operating architecture, strategy, mentoring, quizzes, and scenario drills."
        ),
        "tags": ["PPM", "Web3", "Architecture", "Quiz"],
        "level": "Generated",
        "modules": "9 modules",
        "href": "/courses/grayscale-ppm-mastery-generated.html",
        "gated": True,
    },
]

COURSE_ID_BY_FILENAME = {
    "gen-ai-learning-lab.html": "gen-ai-learning-lab",
    "grayscale-interview-prep.html": "grayscale-interview-prep",
    "grayscale-interview-prep-generated.html": "grayscale-interview-prep",
    "grayscale-ppm-mastery.html": "grayscale-ppm-mastery",
    "grayscale-ppm-mastery-generated.html": "grayscale-ppm-mastery",
}

ACCESS_COOKIE = "prep_access_code"
SESSION_COOKIE = "prep_session"
OPENROUTER_PUBLIC_MODEL = "openrouter/free"


def _split_csv(value: str | None) -> list[str]:
    return [v.strip() for v in (value or "").split(",") if v.strip()]


def _truthy(value) -> bool:
    if isinstance(value, bool):
        return value
    return str(value or "").strip().lower() in {"1", "true", "yes", "y", "on"}


def _all_course_ids() -> set[str]:
    return {c["id"] for c in LIBRARY_COURSES}


def _public_library_ids() -> set[str]:
    raw = os.environ.get("PREP_LIBRARY_PUBLIC_IDS")
    if raw is None:
        return {"gen-ai-learning-lab"}
    ids = set(_split_csv(raw))
    return _all_course_ids() if "*" in ids else ids


def _access_code_from_request(request: Request) -> str:
    query = getattr(request, "query_params", {}) or {}
    headers = getattr(request, "headers", {}) or {}
    cookies = getattr(request, "cookies", {}) or {}
    return (
        str(query.get("access_code") or "").strip()
        or str(headers.get("x-prep-access-code") or "").strip()
        or str(cookies.get(ACCESS_COOKIE) or "").strip()
    )


def _auth_users() -> dict[str, dict]:
    raw = os.environ.get("PREP_AUTH_USERS", "").strip()
    if not raw:
        return {}
    try:
        parsed = json.loads(raw)
    except json.JSONDecodeError:
        log.warning("PREP_AUTH_USERS is not valid JSON.")
        return {}
    if not isinstance(parsed, dict):
        return {}
    users: dict[str, dict] = {}
    for username, spec in parsed.items():
        if isinstance(spec, dict):
            users[str(username)] = spec
        elif isinstance(spec, str):
            users[str(username)] = {"passcode": spec, "library": ["*"], "openrouter_paid": True}
    return users


def _session_secret() -> str:
    return (
        os.environ.get("PREP_AUTH_SECRET", "").strip()
        or os.environ.get("PREP_ADMIN_ACCESS_CODE", "").strip()
        or os.environ.get("OPENROUTER_API_KEY", "").strip()
        or "prep-dev-session-secret"
    )


def _b64url_encode(raw: bytes) -> str:
    return base64.urlsafe_b64encode(raw).decode("ascii").rstrip("=")


def _b64url_decode(value: str) -> bytes:
    padding = "=" * (-len(value) % 4)
    return base64.urlsafe_b64decode((value + padding).encode("ascii"))


def _sign_session(payload: str) -> str:
    sig = hmac.new(_session_secret().encode("utf-8"), payload.encode("ascii"),
                   hashlib.sha256).digest()
    return _b64url_encode(sig)


def _session_cookie(username: str) -> str:
    payload = _b64url_encode(json.dumps({"u": username}, separators=(",", ":")).encode("utf-8"))
    return f"{payload}.{_sign_session(payload)}"


def _session_user(request: Request) -> str:
    cookies = getattr(request, "cookies", {}) or {}
    token = str(cookies.get(SESSION_COOKIE) or "").strip()
    if "." not in token:
        return ""
    payload, sig = token.rsplit(".", 1)
    if not hmac.compare_digest(sig, _sign_session(payload)):
        return ""
    try:
        data = json.loads(_b64url_decode(payload).decode("utf-8"))
    except (ValueError, json.JSONDecodeError):
        return ""
    username = str(data.get("u") or "").strip()
    return username if username in _auth_users() else ""


def _access_from_spec(username: str, spec: dict, public_ids: set[str]) -> dict:
    granted_ids = set(_split_csv(os.environ.get("PREP_LIBRARY_GRANTED_IDS")))
    raw_library = spec.get("library", spec.get("courses", [])) if isinstance(spec, dict) else []
    if isinstance(raw_library, str):
        granted_ids.update(_split_csv(raw_library))
    elif isinstance(raw_library, list):
        granted_ids.update(str(v).strip() for v in raw_library if str(v).strip())
    if "*" in granted_ids:
        allowed_ids = _all_course_ids()
    else:
        allowed_ids = public_ids | granted_ids
    return {
        "user": username or spec.get("user") or spec.get("email") or "public",
        "library": allowed_ids,
        "openrouter_paid": _truthy(spec.get("openrouter_paid") if isinstance(spec, dict) else False),
        "authenticated": bool(username),
    }


def _access_records() -> dict[str, dict]:
    records: dict[str, dict] = {}
    raw = os.environ.get("PREP_ACCESS_CODES", "").strip()
    if raw:
        try:
            parsed = json.loads(raw)
        except json.JSONDecodeError:
            log.warning("PREP_ACCESS_CODES is not valid JSON.")
            parsed = {}
        if isinstance(parsed, dict):
            for code, spec in parsed.items():
                if isinstance(spec, dict):
                    records[str(code)] = spec
                elif isinstance(spec, list):
                    records[str(code)] = {"library": spec}
                elif isinstance(spec, str):
                    records[str(code)] = {"user": spec, "library": []}

    admin_code = os.environ.get("PREP_ADMIN_ACCESS_CODE", "").strip()
    if admin_code:
        records.setdefault(admin_code, {
            "user": "admin",
            "library": ["*"],
            "openrouter_paid": True,
        })
    return records


def _access_for_request(request: Request) -> dict:
    public_ids = _public_library_ids()
    users = _auth_users()
    username = _session_user(request)
    if username and username in users:
        auth_access = _access_from_spec(username, users[username], public_ids)
        return {
            "code": "",
            "user": auth_access["user"],
            "library": auth_access["library"],
            "openrouter_paid": auth_access["openrouter_paid"],
            "has_access_code": False,
            "authenticated": True,
        }

    code = _access_code_from_request(request)
    spec = _access_records().get(code, {}) if code else {}
    access = _access_from_spec("", spec, public_ids) if spec else {
        "user": "public",
        "library": public_ids,
        "openrouter_paid": False,
    }
    return {
        "code": code,
        "user": access["user"],
        "library": access["library"],
        "openrouter_paid": access["openrouter_paid"],
        "has_access_code": bool(code and spec),
        "authenticated": False,
    }


def _filter_library_for_request(request: Request) -> list[dict]:
    access = _access_for_request(request)
    courses = []
    for course in LIBRARY_COURSES:
        if course["id"] not in access["library"]:
            continue
        item = dict(course)
        item.pop("gated", None)
        courses.append(item)
    return courses


def _ensure_course_access(request: Request, course_id: str) -> None:
    if course_id not in _access_for_request(request)["library"]:
        raise HTTPException(403, "You do not have access to this course.")


def _openrouter_free_models() -> list[str]:
    models = _split_csv(os.environ.get("PREP_OPENROUTER_FREE_MODELS"))
    if not models:
        models = [os.environ.get("PREP_OPENROUTER_FREE_MODEL", OPENROUTER_PUBLIC_MODEL).strip()
                  or OPENROUTER_PUBLIC_MODEL]
    return models


def _openrouter_paid_models() -> list[str]:
    return _split_csv(os.environ.get("PREP_OPENROUTER_PAID_MODELS"))


def _is_openrouter_free_model(model: str) -> bool:
    model = (model or "").strip()
    return model == OPENROUTER_PUBLIC_MODEL or model.endswith(":free") or model in _openrouter_free_models()


def _authorize_model(request: Request, provider: str, requested_model: str,
                     requested_key: str) -> str:
    if provider != "openrouter":
        return requested_model.strip()
    model = requested_model.strip()
    if requested_key.strip():
        return model

    access = _access_for_request(request)
    free_default = _openrouter_free_models()[0]
    paid_default = (
        os.environ.get("PREP_OPENROUTER_PAID_MODEL", "").strip()
        or os.environ.get("PREP_MODEL", "").strip()
        or "openai/gpt-4o-mini"
    )
    if access["openrouter_paid"]:
        return model or paid_default
    if model and not _is_openrouter_free_model(model):
        raise HTTPException(403, "That OpenRouter model requires paid API access.")
    return model or free_default

# Default provider when the form doesn't specify one. Prefer AI Gateway when configured,
# otherwise keep the existing free-tier Gemini path.
DEFAULT_BACKEND = os.environ.get(
    "PREP_BACKEND",
    "gateway" if os.environ.get("AI_GATEWAY_API_KEY", "").strip() else "gemini",
)

app = FastAPI(title="Prep Suite Generator")


@app.middleware("http")
async def add_security_headers(request: Request, call_next):
    response = await call_next(request)
    response.headers.setdefault("X-Content-Type-Options", "nosniff")
    response.headers.setdefault("Referrer-Policy", "no-referrer")
    response.headers.setdefault("X-Frame-Options", "DENY")
    response.headers.setdefault(
        "Content-Security-Policy",
        "default-src 'self'; "
        "script-src 'self' 'unsafe-inline' 'unsafe-eval' https://cdn.jsdelivr.net https://unpkg.com; "
        "style-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net https://fonts.googleapis.com; "
        "font-src https://fonts.gstatic.com data:; "
        "connect-src 'self'; "
        "img-src 'self' data: blob:; "
        "object-src 'none'; base-uri 'self'; frame-ancestors 'none'",
    )
    return response


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
    raise GenerationError("Unsupported file type. Upload txt, md, markdown, csv, pdf, or docx.")


# ---------- routes ----------------------------------------------------------
@app.get("/", response_class=HTMLResponse)
def home(request: Request):
    headers = {}
    code = _access_code_from_request(request)
    if code:
        headers["Set-Cookie"] = f"{ACCESS_COOKIE}={code}; Path=/; Max-Age=2592000; SameSite=Lax"
    return HTMLResponse(UPLOAD_PAGE, headers=headers)


@app.get("/library", response_class=HTMLResponse)
def library(request: Request):
    headers = {}
    code = _access_code_from_request(request)
    if code:
        headers["Set-Cookie"] = f"{ACCESS_COOKIE}={code}; Path=/; Max-Age=2592000; SameSite=Lax"
    return HTMLResponse(UPLOAD_PAGE, headers=headers)


@app.get("/api/library")
def library_api(request: Request):
    access = _access_for_request(request)
    return {
        "courses": _filter_library_for_request(request),
        "access": {
            "user": access["user"],
            "has_access_code": access["has_access_code"],
            "authenticated": access["authenticated"],
            "openrouter_paid": access["openrouter_paid"],
        },
    }


@app.post("/api/login")
async def login(username: str = Form(""), passcode: str = Form("")):
    username = _check_text_field("username", username).strip()
    passcode = _check_text_field("passcode", passcode).strip()
    users = _auth_users()
    spec = users.get(username)
    expected = str(spec.get("passcode") or "") if isinstance(spec, dict) else ""
    if not username or not expected or not hmac.compare_digest(passcode, expected):
        raise HTTPException(401, "Invalid username or passcode.")
    cookie = (
        f"{SESSION_COOKIE}={_session_cookie(username)}; Path=/; "
        "Max-Age=2592000; SameSite=Lax; HttpOnly"
    )
    return HTMLResponse('{"ok":true}', media_type="application/json", headers={"Set-Cookie": cookie})


@app.post("/api/logout")
async def logout():
    cookie = f"{SESSION_COOKIE}=; Path=/; Max-Age=0; SameSite=Lax; HttpOnly"
    return HTMLResponse('{"ok":true}', media_type="application/json", headers={"Set-Cookie": cookie})


@app.get("/courses/{filename:path}")
def course_asset(request: Request, filename: str):
    if filename in GENERATED_COURSES:
        course_id = GENERATED_COURSES[filename]["id"]
        _ensure_course_access(request, course_id)
        course = GENERATED_COURSES[filename]["course"]
        errs = validate(course)
        if errs:
            raise HTTPException(500, "Generated course is invalid: " + "; ".join(errs[:3]))
        html = inject(course, TEMPLATE_PATH.read_text(encoding="utf-8"))
        return HTMLResponse(html)

    course_id = COURSE_ID_BY_FILENAME.get(filename)
    if course_id:
        _ensure_course_access(request, course_id)

    target = (COURSES_DIR / filename).resolve()
    try:
        target.relative_to(COURSES_DIR.resolve())
    except ValueError:
        raise HTTPException(404, "Course not found.")
    if not target.is_file():
        raise HTTPException(404, "Course not found.")
    media_type = "text/html; charset=utf-8" if target.suffix == ".html" else None
    if target.suffix == ".jsx":
        media_type = "text/javascript; charset=utf-8"
    return FileResponse(target, media_type=media_type)


@app.get("/api/config")
def config(request: Request):
    """Tell the UI which providers already have a server-side key configured."""
    access = _access_for_request(request)
    return {
        "default": resolve_provider(DEFAULT_BACKEND),
        "configured": {p: bool(os.environ.get(env, "").strip())
                       for p, env in ENV_KEYS.items()},
        "sources": {
            "tavily": bool(os.environ.get("TAVILY_API_KEY", "").strip()),
        },
        "access": {
            "user": access["user"],
            "has_access_code": access["has_access_code"],
            "authenticated": access["authenticated"],
            "openrouter_paid": access["openrouter_paid"],
        },
        "openrouter": {
            "free_models": _openrouter_free_models(),
            "paid_models": _openrouter_paid_models(),
            "free_default": _openrouter_free_models()[0],
        },
    }


@app.post("/api/generate")
async def generate(
    request: Request,
    instruction: str = Form(""),
    learner: str = Form("adult"),
    grade: str = Form(""),
    learning_style: str = Form("mixed"),
    context: str = Form(""),
    pasted: str = Form(""),
    urls: str = Form(""),
    web_search: str = Form(""),
    provider: str = Form(""),
    model: str = Form(""),
    api_key: str = Form(""),
    file: UploadFile | None = File(None),
):
    content_length = request.headers.get("content-length")
    if content_length:
        try:
            too_large = int(content_length) > _MAX_REQUEST_BYTES
        except ValueError:
            too_large = True
        if too_large:
            mb = _MAX_REQUEST_BYTES // 1_048_576
            raise HTTPException(413, f"Request is too large (max {mb} MB).")

    instruction = _check_text_field("instruction", instruction)
    grade = _check_text_field("grade", grade)
    learning_style = _check_text_field("learning_style", learning_style)
    context = _check_text_field("context", context)
    pasted = _check_text_field("pasted", pasted)
    urls = _check_text_field("urls", urls)
    web_search = _check_text_field("web_search", web_search)
    model = _check_text_field("model", model)
    api_key = _check_text_field("api_key", api_key)

    # Rate limit: 10 requests/minute per IP (x-forwarded-for on Vercel)
    forwarded = request.headers.get("x-forwarded-for", "")
    client_ip = forwarded.split(",")[0].strip() or (request.client.host if request.client else "unknown")
    if not await _check_rate_limit_shared(client_ip):
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
    if len(url_list) > _MAX_URLS:
        raise HTTPException(400, f"Too many URLs (max {_MAX_URLS}).")
    if url_list:
        try:
            for src, text in await fetch_urls(url_list):
                material_parts.append(f"[Source: {src}]\n{text}")
        except GenerationError as e:
            raise HTTPException(400, str(e))

    # 3) Tavily web searches (one query per line)
    search_queries = [ln.strip() for ln in web_search.splitlines() if ln.strip()]
    if len(search_queries) > _MAX_TAVILY_QUERIES:
        raise HTTPException(400, f"Too many web searches (max {_MAX_TAVILY_QUERIES}).")
    if search_queries:
        try:
            for query, text in await search_tavily(search_queries):
                material_parts.append(f"[Tavily search: {query}]\n{text}")
        except GenerationError as e:
            raise HTTPException(400, str(e))

    # 4) pasted text
    if pasted.strip():
        material_parts.append(pasted.strip())

    material = "\n\n".join(p for p in material_parts if p.strip()).strip()

    if not material:
        raise HTTPException(400, "Provide a document, a URL, or paste some study material.")
    if not instruction.strip():
        raise HTTPException(400, "Add a one-line instruction (topic / focus / tone).")

    # Fold grade level into the audience signal for kid courses.
    learner = "kid" if learner == "kid" else "adult"
    learning_style = learning_style if learning_style in {"mixed", "visual", "practice", "read", "audio"} else "mixed"
    instruction_full = instruction.strip()
    if learner == "kid" and grade.strip():
        instruction_full += f" (school grade level: {grade.strip()})"

    try:
        selected_provider = resolve_provider(provider or DEFAULT_BACKEND)
        selected_model = _authorize_model(request, selected_provider, model, api_key)
        course, html = await asyncio.to_thread(
            functools.partial(
                build_course,
                instruction=instruction_full,
                material=material,
                learner=learner,
                learning_style=learning_style,
                context=context.strip(),
                template_path=TEMPLATE_PATH,
                provider=selected_provider,
                api_key=api_key,
                model=selected_model,
            )
        )
    except GenerationError as e:
        raise HTTPException(422, f"Generation failed: {e}")

    title = course.get("meta", {}).get("title", "Untitled course")
    result = {
        "title": title,
        "modules": len(course.get("modules", [])),
    }
    blob = await asyncio.to_thread(_store_course_blob, title, html)
    if blob:
        result.update(blob)
    else:
        result["html_b64"] = base64.b64encode(html.encode("utf-8")).decode("ascii")
    return result

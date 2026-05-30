"""
_generator.py — the engine of the prep suite (serverless / multi-provider build).

documents + instruction  ->  strict COURSE json  ->  validated  ->  injected into template

This is the reusable core. api/index.py (the web front end) is a thin wrapper around it.

All model calls go over plain HTTP (httpx) so the serverless bundle stays small and
cold-starts stay fast — no heavy vendor SDKs. Add a provider by adding one function and
one entry to PROVIDERS.

Providers:
  - gemini     (Google AI Studio — generous free tier)   default
  - groq       (Groq — fast free tier, OpenAI-compatible)
  - grok       (xAI Grok — OpenAI-compatible)
  - openai     (paid fallback)
  - anthropic  (paid fallback)
"""

import json
import os
import re
from pathlib import Path

import httpx


class GenerationError(Exception):
    """Raised when generation or validation fails in a way worth showing the user."""


def normalize_url(url: str) -> str:
    url = url.strip()
    if not re.match(r"^https?://", url, re.I):
        url = "https://" + url
    return url


def _regex_html_to_text(html: str) -> str:
    """Dependency-free fallback: strip tags into rough plain text."""
    html = re.sub(r"(?is)<(script|style|noscript|head)[^>]*>.*?</\1>", " ", html)
    html = re.sub(r"(?is)<br\s*/?>", "\n", html)
    html = re.sub(r"(?is)</(p|div|li|h[1-6]|tr)>", "\n", html)
    text = re.sub(r"(?s)<[^>]+>", " ", html)
    for a, b in (("&nbsp;", " "), ("&amp;", "&"), ("&lt;", "<"), ("&gt;", ">"),
                 ("&quot;", '"'), ("&#39;", "'")):
        text = text.replace(a, b)
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n\s*\n\s*\n+", "\n\n", text).strip()
    return text


def extract_main_text(html: str, url: str = "", max_chars: int = 40000) -> str:
    """Pull the readable main content out of an HTML page.

    Prefers trafilatura (readability-style main-content detection, drops nav/ads/boilerplate);
    falls back to a built-in regex cleaner if trafilatura is unavailable or returns nothing.
    """
    text = ""
    try:
        import trafilatura
        extracted = trafilatura.extract(
            html, url=url or None,
            include_comments=False, include_tables=True,
            favor_recall=True, no_fallback=False,
        )
        if extracted:
            text = extracted.strip()
    except Exception:
        text = ""
    if not text:
        text = _regex_html_to_text(html)
    return text[:max_chars]


def fetch_url_text(url: str, max_chars: int = 40000) -> str:
    """Synchronous fetch + extract for a single URL (used in CLI/local contexts)."""
    url = normalize_url(url)
    try:
        with httpx.Client(timeout=httpx.Timeout(30.0, connect=10.0),
                          follow_redirects=True,
                          headers={"User-Agent": "Mozilla/5.0 (PrepSuiteBot)"}) as c:
            r = c.get(url)
    except httpx.HTTPError as e:
        raise GenerationError(f"Could not fetch {url} ({type(e).__name__}).")
    if r.status_code != 200:
        raise GenerationError(f"Could not fetch {url} (HTTP {r.status_code}).")
    text = extract_main_text(r.text, url=url, max_chars=max_chars)
    if not text:
        raise GenerationError(f"Fetched {url} but found no readable text.")
    return text


# ----------------------------------------------------------------------------
# 1. The generation prompt (kept in sync with the COURSE schema)
# ----------------------------------------------------------------------------
SYSTEM_PROMPT = """You are a course generator. You convert study material into a single JSON object that drives an interactive study app. Output ONLY valid JSON — no markdown, no prose, no code fences.

The JSON must match this schema exactly:
{ "meta": {"title","subtitle","learner"}, "modules": [ {"type","id","label","data"} ] }

Allowed module types and their data shapes:
- overview: {kicker, headline, body, cards:[{tag,title,text}], stepsTitle, steps:[...]}
- concept_cards: {intro, cards:[{badge, name, fields:[{label,text,tone}], highlight:{label,q,a}}]}
  tone is one of: neutral, good, info, bad, warn
- flashcards: {cards:[{q,a}]}
- glossary: {intro, terms:[{t,d}]}
- cheatsheet: {title, intro, blocks:[{title, wide(optional bool), text(optional), items(optional array)}]}
- sequence: {title, intro, modes:[{key, label, items:[{id,label,why}], correct:[ids in correct order]}]}
- challenge: {kind, title, intro, startLabel, timer(optional int), rounds:[{title(optional), scenario(optional), constraints(optional array), question, opts:[string OR {label,detail}], correct (0-based index into opts), exp(optional) OR (rightFeedback AND wrongFeedback array parallel to opts with null in the correct slot)}]}
  kind is one of: quiz, rounds, timed, classify

Requirements:
- Build a coherent course from the material. Always include, in this order:
  one overview, one concept_cards, one flashcards, one challenge with kind "quiz",
  one glossary, one cheatsheet. Add a challenge with kind "rounds" (a build/apply game),
  a challenge with kind "timed" (a speed round, timer 20), and a sequence when the material supports them.
- Every module id must be unique and lowercase. Tab labels should be short and numbered (e.g. "1. Big Idea").
- Ground every fact in the provided material. Do NOT invent facts. If something is ambiguous, leave it out.
- On each concept card, write a "highlight" box (label starts with an emoji like ⚠) calling out the single most common mistake or test trap for that concept.
- Match the requested audience. If the instruction names a grade level or says "kid", set meta.learner="kid", keep language simple, friendly and encouraging, use concrete examples. Otherwise set meta.learner="adult".
- 8 to 12 flashcards. 6 to 10 quiz questions. Questions test understanding, not trivia.
- "correct" is a 0-based index into "opts". For rounds/classify, "wrongFeedback" is parallel to "opts" (use null for the correct slot). Use "exp" OR rightFeedback+wrongFeedback, not both.

Return the JSON object and nothing else."""


def _user_message(instruction: str, learner: str, material: str,
                  context: str = "", max_chars: int = 24000) -> str:
    learner_hint = ("Audience: a child / the specified grade level. Use meta.learner=\"kid\"."
                    if learner == "kid" else
                    "Audience: an adult learner. Use meta.learner=\"adult\".")
    trimmed = material[:max_chars]
    if len(material) > max_chars:
        trimmed += "\n\n[material truncated for length]"
    context_block = f"\nADDITIONAL CONTEXT (goals, constraints, focus areas):\n{context.strip()}\n" \
        if context and context.strip() else ""
    return f"INSTRUCTION: {instruction}\n{learner_hint}\n{context_block}\nMATERIAL:\n{trimmed}"


# ----------------------------------------------------------------------------
# 2. Model backends — all over HTTP. Each returns the raw text the model emitted.
# ----------------------------------------------------------------------------
# Default model per provider. Override with PREP_MODEL or a per-request `model`.
DEFAULT_MODELS = {
    "gemini": "gemini-2.0-flash",
    "groq": "llama-3.3-70b-versatile",
    "grok": "grok-3-mini",
    "openai": "gpt-4o-mini",
    "anthropic": "claude-sonnet-4-20250514",
}

# Which env var holds each provider's key.
ENV_KEYS = {
    "gemini": "GEMINI_API_KEY",
    "groq": "GROQ_API_KEY",
    "grok": "XAI_API_KEY",
    "openai": "OPENAI_API_KEY",
    "anthropic": "ANTHROPIC_API_KEY",
}

_HTTP_TIMEOUT = httpx.Timeout(120.0, connect=15.0)


def _call_gemini(system: str, user: str, api_key: str, model: str) -> str:
    url = (f"https://generativelanguage.googleapis.com/v1beta/models/"
           f"{model}:generateContent?key={api_key}")
    payload = {
        "system_instruction": {"parts": [{"text": system}]},
        "contents": [{"role": "user", "parts": [{"text": user}]}],
        "generationConfig": {"temperature": 0.3, "response_mime_type": "application/json"},
    }
    with httpx.Client(timeout=_HTTP_TIMEOUT) as c:
        r = c.post(url, json=payload)
    _raise_for_provider(r, "Gemini")
    data = r.json()
    try:
        return data["candidates"][0]["content"]["parts"][0]["text"]
    except (KeyError, IndexError):
        raise GenerationError(f"Gemini returned no content: {json.dumps(data)[:300]}")


def _call_openai_compatible(system: str, user: str, api_key: str, model: str,
                            base_url: str, label: str) -> str:
    payload = {
        "model": model,
        "temperature": 0.3,
        "response_format": {"type": "json_object"},
        "messages": [{"role": "system", "content": system},
                     {"role": "user", "content": user}],
    }
    with httpx.Client(timeout=_HTTP_TIMEOUT) as c:
        r = c.post(f"{base_url}/chat/completions",
                   headers={"Authorization": f"Bearer {api_key}"}, json=payload)
    _raise_for_provider(r, label)
    data = r.json()
    try:
        return data["choices"][0]["message"]["content"]
    except (KeyError, IndexError):
        raise GenerationError(f"{label} returned no content: {json.dumps(data)[:300]}")


def _call_groq(system: str, user: str, api_key: str, model: str) -> str:
    return _call_openai_compatible(system, user, api_key, model,
                                   "https://api.groq.com/openai/v1", "Groq")


def _call_grok(system: str, user: str, api_key: str, model: str) -> str:
    return _call_openai_compatible(system, user, api_key, model,
                                   "https://api.x.ai/v1", "Grok")


def _call_openai(system: str, user: str, api_key: str, model: str) -> str:
    return _call_openai_compatible(system, user, api_key, model,
                                   "https://api.openai.com/v1", "OpenAI")


def _call_anthropic(system: str, user: str, api_key: str, model: str) -> str:
    payload = {
        "model": model,
        "max_tokens": 8000,
        "temperature": 0.3,
        "system": system,
        "messages": [{"role": "user", "content": user}],
    }
    headers = {"x-api-key": api_key, "anthropic-version": "2023-06-01"}
    with httpx.Client(timeout=_HTTP_TIMEOUT) as c:
        r = c.post("https://api.anthropic.com/v1/messages", headers=headers, json=payload)
    _raise_for_provider(r, "Anthropic")
    data = r.json()
    try:
        return "".join(b.get("text", "") for b in data["content"] if b.get("type") == "text")
    except (KeyError, TypeError):
        raise GenerationError(f"Anthropic returned no content: {json.dumps(data)[:300]}")


PROVIDERS = {
    "gemini": _call_gemini,
    "groq": _call_groq,
    "grok": _call_grok,
    "openai": _call_openai,
    "anthropic": _call_anthropic,
}


def _raise_for_provider(r: httpx.Response, label: str) -> None:
    if r.status_code == 200:
        return
    detail = r.text[:300]
    if r.status_code in (401, 403):
        raise GenerationError(f"{label} rejected the API key (HTTP {r.status_code}). "
                              "Check the key and that the API is enabled.")
    if r.status_code == 429:
        raise GenerationError(f"{label} rate limit / quota hit (HTTP 429). "
                              "Wait a moment or switch providers / add a paid key.")
    raise GenerationError(f"{label} error HTTP {r.status_code}: {detail}")


def resolve_provider(requested: str | None) -> str:
    provider = (requested or os.environ.get("PREP_BACKEND") or "gemini").lower()
    if provider not in PROVIDERS:
        raise GenerationError(f"Unknown provider '{provider}'. "
                              f"Choose one of: {', '.join(PROVIDERS)}.")
    return provider


def resolve_key(provider: str, requested_key: str | None) -> str:
    key = (requested_key or "").strip() or os.environ.get(ENV_KEYS[provider], "").strip()
    if not key:
        raise GenerationError(
            f"No API key for '{provider}'. Set {ENV_KEYS[provider]} in the environment "
            f"or paste a key in the form (BYOK).")
    return key


def _generate_json(system: str, user: str, provider: str, api_key: str, model: str) -> str:
    return PROVIDERS[provider](system, user, api_key, model)


# ----------------------------------------------------------------------------
# 3. Parsing + validation
# ----------------------------------------------------------------------------
def _extract_json(raw: str) -> dict:
    """Be forgiving: strip code fences and grab the outermost {...} if needed."""
    s = raw.strip()
    s = re.sub(r"^```(?:json)?\s*", "", s)
    s = re.sub(r"\s*```$", "", s)
    try:
        return json.loads(s)
    except json.JSONDecodeError:
        a, b = s.find("{"), s.rfind("}")
        if a == -1 or b == -1 or b <= a:
            raise GenerationError("Model did not return JSON.")
        try:
            return json.loads(s[a:b + 1])
        except json.JSONDecodeError as e:
            raise GenerationError(f"Model returned invalid JSON: {e}")


VALID_TYPES = {"overview", "concept_cards", "flashcards", "glossary",
               "cheatsheet", "sequence", "challenge"}
VALID_KINDS = {"quiz", "rounds", "timed", "classify"}


def validate(course: dict) -> list[str]:
    """Return a list of problems. Empty list == valid. Mirrors what the engine needs."""
    errs: list[str] = []
    if not isinstance(course, dict):
        return ["Top level is not an object."]

    meta = course.get("meta")
    if not isinstance(meta, dict) or not meta.get("title"):
        errs.append("meta.title is required.")
    if meta and meta.get("learner") not in (None, "kid", "adult"):
        errs.append("meta.learner must be 'kid' or 'adult'.")

    modules = course.get("modules")
    if not isinstance(modules, list) or not modules:
        return errs + ["modules must be a non-empty array."]

    seen_ids = set()
    for i, m in enumerate(modules):
        where = f"module[{i}]"
        if not isinstance(m, dict):
            errs.append(f"{where} is not an object."); continue
        mid, mtype = m.get("id"), m.get("type")
        if not mid:
            errs.append(f"{where} missing id.")
        elif mid in seen_ids:
            errs.append(f"{where} duplicate id '{mid}'.")
        else:
            seen_ids.add(mid)
        if mtype not in VALID_TYPES:
            errs.append(f"{where} invalid type '{mtype}'."); continue
        if not m.get("label"):
            errs.append(f"{where} ({mtype}) missing label.")
        data = m.get("data")
        if not isinstance(data, dict):
            errs.append(f"{where} ({mtype}) missing data object."); continue

        if mtype == "flashcards":
            cards = data.get("cards")
            if not isinstance(cards, list) or not cards:
                errs.append(f"{where} flashcards need a non-empty cards array.")
            else:
                for j, c in enumerate(cards):
                    if not (c.get("q") and c.get("a")):
                        errs.append(f"{where} card[{j}] needs q and a.")
        elif mtype == "glossary":
            if not isinstance(data.get("terms"), list) or not data["terms"]:
                errs.append(f"{where} glossary needs a terms array.")
        elif mtype == "concept_cards":
            if not isinstance(data.get("cards"), list) or not data["cards"]:
                errs.append(f"{where} concept_cards needs a cards array.")
        elif mtype == "sequence":
            modes = data.get("modes")
            if not isinstance(modes, list) or not modes:
                errs.append(f"{where} sequence needs a modes array.")
            else:
                for j, mode in enumerate(modes):
                    items = mode.get("items", [])
                    ids = {it.get("id") for it in items}
                    correct = mode.get("correct", [])
                    if not items or not correct:
                        errs.append(f"{where} mode[{j}] needs items and correct.")
                    elif set(correct) != ids:
                        errs.append(f"{where} mode[{j}] correct ids must match item ids.")
        elif mtype == "challenge":
            kind = data.get("kind")
            if kind not in VALID_KINDS:
                errs.append(f"{where} challenge invalid kind '{kind}'.")
            rounds = data.get("rounds")
            if not isinstance(rounds, list) or not rounds:
                errs.append(f"{where} challenge needs a rounds array.")
            else:
                for j, r in enumerate(rounds):
                    opts = r.get("opts")
                    if not isinstance(opts, list) or len(opts) < 2:
                        errs.append(f"{where} round[{j}] needs >=2 opts."); continue
                    c = r.get("correct")
                    if not isinstance(c, int) or not (0 <= c < len(opts)):
                        errs.append(f"{where} round[{j}] correct index out of range.")
                    if not r.get("question"):
                        errs.append(f"{where} round[{j}] missing question.")
                    wf = r.get("wrongFeedback")
                    if wf is not None and len(wf) != len(opts):
                        errs.append(f"{where} round[{j}] wrongFeedback must be parallel to opts.")
    return errs


# ----------------------------------------------------------------------------
# 4. Injection into the template
# ----------------------------------------------------------------------------
COURSE_RE = re.compile(r"const COURSE =\s*[\s\S]*?\n\s*;")


def inject(course: dict, template: str) -> str:
    payload = "const COURSE =\n" + json.dumps(course, indent=2, ensure_ascii=False) + "\n;"
    new, n = COURSE_RE.subn(lambda _: payload, template, count=1)
    if n != 1:
        raise GenerationError("Could not find the COURSE injection point in the template.")
    return new


# ----------------------------------------------------------------------------
# 5. Public entry point
# ----------------------------------------------------------------------------
def build_course(instruction: str, material: str, learner: str,
                 template_path: Path, provider: str | None = None,
                 api_key: str | None = None, model: str | None = None,
                 context: str = "", retries: int = 1) -> tuple[dict, str]:
    """Returns (course_dict, finished_html). Raises GenerationError on failure."""
    template = Path(template_path).read_text(encoding="utf-8")
    user = _user_message(instruction, learner, material, context=context)

    prov = resolve_provider(provider)
    key = resolve_key(prov, api_key)
    mdl = (model or os.environ.get("PREP_MODEL") or DEFAULT_MODELS[prov])

    last_errs: list[str] = []
    for attempt in range(retries + 1):
        sys_prompt = SYSTEM_PROMPT
        if attempt > 0 and last_errs:
            sys_prompt += ("\n\nYour previous output had these problems — fix them and "
                           "return corrected JSON only:\n- " + "\n- ".join(last_errs))
        raw = _generate_json(sys_prompt, user, prov, key, mdl)
        course = _extract_json(raw)
        course.setdefault("meta", {}).setdefault("learner", learner)
        last_errs = validate(course)
        if not last_errs:
            return course, inject(course, template)

    raise GenerationError("Validation failed after retry:\n- " + "\n- ".join(last_errs))

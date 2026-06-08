"""
_generator.py — the engine of the prep suite (serverless / multi-provider build).

documents + instruction  ->  strict COURSE json  ->  validated  ->  injected into template

This is the reusable core. api/index.py (the web front end) is a thin wrapper around it.

All model calls go over plain HTTP (httpx) so the serverless bundle stays small and
cold-starts stay fast — no heavy vendor SDKs. Add a provider by adding one function and
one entry to PROVIDERS.

Providers:
  - gateway    (Vercel AI Gateway — unified model routing)
  - gemini     (Google AI Studio — generous free tier)   default
  - groq       (Groq — fast free tier, OpenAI-compatible)
  - grok       (xAI Grok — OpenAI-compatible)
  - openai     (paid fallback)
  - anthropic  (paid fallback)
"""

import json
import logging
import os
import re
from pathlib import Path

import httpx


log = logging.getLogger(__name__)


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
SYSTEM_PROMPT = """You are a course architect and generator. You convert study material into a single JSON object that drives an interactive study app. Output ONLY valid JSON — no markdown, no prose, no code fences.

The JSON must match this schema exactly:
{ "meta": {"title","subtitle","learner","learningStyle"}, "modules": [ {"type","id","label","data"} ] }

Allowed module types and their data shapes:
- overview: {kicker, headline, body, cards:[{tag,title,text}], stepsTitle, steps:[...]}
- concept_cards: {intro, cards:[{badge, name, fields:[{label,text,tone}], highlight:{label,q,a}}]}
  tone is one of: neutral, good, info, bad, warn
- flashcards: {cards:[{q,a}]}
- visual_map: {title, intro, nodes:[{id,label,tag,summary}], links:[{from,to,label}]}
- drag_sort: {title, intro, buckets:[{id,label,hint}], items:[{id,label,detail,bucket}]}
- teach_back: {title, intro, prompts:[{q,keyPoints:[...],sample}]}
- notes: {title, intro, sections:[{heading,summary,bullets:[...],check}]}
- audio_script: {title, intro, segments:[{label,text}]}
- glossary: {intro, terms:[{t,d}]}
- cheatsheet: {title, intro, blocks:[{title, wide(optional bool), text(optional), items(optional array)}]}
- sequence: {title, intro, modes:[{key, label, items:[{id,label,why}], correct:[ids in correct order]}]}
- challenge: {kind, title, intro, startLabel, timer(optional int), rounds:[{title(optional), scenario(optional), constraints(optional array), question, opts:[string OR {label,detail}], correct (0-based index into opts), exp(optional) OR (rightFeedback AND wrongFeedback array parallel to opts with null in the correct slot)}]}
  kind is one of: quiz, rounds, timed, classify

Course design requirements:
- First infer the learning domain from the instruction and material. Do NOT reuse a job-prep,
  interview, business, or software framing unless the user explicitly asks for that. A music,
  arts, language, fitness, craft, or hobby topic should become a guided skill-practice journey,
  not a career-prep course.
- Build a complete, domain-specific course from the material. Always include these modules:
  one overview, one visual_map, one concept_cards, one drag_sort, one flashcards,
  one challenge with kind "quiz", one teach_back, one challenge with kind "rounds",
  one challenge with kind "timed" and timer 20, one glossary, one notes, one cheatsheet,
  and one sequence. Add audio_script when the learner preference is audio.
- Domain adaptation examples:
  * Jazz/music: use listening, ear training, harmonic movement, instrument/repertoire practice,
    improvisation choices, chord-scale relationships, voice-leading, transcription, and practice
    routine language. Rounds should feel like musical decisions, not workplace cases.
  * Programming/AI/web: use build steps, debugging, architecture decisions, and implementation drills.
  * Academic/test prep: use misconceptions, worked examples, retrieval practice, and exam traps.
  * Professional/interview prep: use role pressure, executive framing, decision judgment, and answer drills.
- Make the course as rich as the curated examples: each module should teach or practice a distinct
  skill, not repeat the same summary in different formats.
- Quantity targets:
  overview cards 3-5; concept cards 5-8 with 2-4 fields each; flashcards 10-12;
  quiz questions 8-10; glossary terms 10-16; notes sections 4-8; cheatsheet blocks 5-8;
  visual map nodes 5-9; drag_sort items 8-12; teach_back prompts 4-6;
  sequence modes 1-3 with 5-8 items each; rounds challenge 4-7 rounds;
  timed challenge 6-10 rounds.
- If learningStyle is visual, put visual_map before concept_cards. If practice, put drag_sort,
  sequence, and challenge modules earlier. If read, put notes and cheatsheet earlier. If audio,
  put audio_script near the top. If mixed, balance the order naturally.
- Every module id must be unique and lowercase. Tab labels should be short and numbered (e.g. "1. Big Idea").
- Ground every fact in the provided material. Do NOT invent facts. If something is ambiguous, leave it out.
- On each concept card, write a "highlight" box (label starts with an emoji like ⚠) calling out the single most common mistake or test trap for that concept.
- Match the requested audience. If the instruction names a grade level or says "kid", set meta.learner="kid", keep language simple, friendly and encouraging, use concrete examples. Otherwise set meta.learner="adult".
- Set meta.learningStyle to one of: mixed, visual, practice, read, audio.
- 8 to 12 flashcards. 6 to 10 quiz questions. Questions test understanding, not trivia.
- "correct" is a 0-based index into "opts". For rounds/classify, "wrongFeedback" is parallel to "opts" (use null for the correct slot). Use "exp" OR rightFeedback+wrongFeedback, not both.

Return the JSON object and nothing else."""


def _course_design_hint(instruction: str, material: str) -> str:
    haystack = f"{instruction}\n{material[:4000]}".lower()
    if re.search(r"\b(jazz|music|musical|chord|scale|harmony|harmonic|melody|improv|improvis|piano|guitar|sax|trumpet|bass|drum|ear training|voice[- ]?leading)\b", haystack):
        return (
            "Course archetype: creative musical practice path. Structure the experience as a "
            "guided progression from hearing/recognizing ideas to applying them on an instrument "
            "or in improvisation. Use drills such as ear-training choices, chord/scale fit, "
            "voice-leading order, listening analysis, repertoire study, and practice routines. "
            "Avoid interview, employer, resume, product, or job-prep framing unless the instruction "
            "explicitly requests it."
        )
    if re.search(r"\b(interview|job|career|resume|onsite|hiring|role|stakeholder|executive)\b", haystack):
        return (
            "Course archetype: professional readiness path. Emphasize role-specific judgment, "
            "answer practice, decision pressure, narrative clarity, and scenario drills."
        )
    if re.search(r"\b(code|programming|javascript|html|css|python|react|api|gen ai|llm|rag|model|software|web app)\b", haystack):
        return (
            "Course archetype: technical build lab. Emphasize concepts, implementation sequence, "
            "debugging choices, architecture tradeoffs, and hands-on build/apply challenges."
        )
    if re.search(r"\b(test|exam|grade|school|quiz|homework|class|biology|history|math|science)\b", haystack):
        return (
            "Course archetype: academic mastery path. Emphasize misconception repair, worked "
            "examples, retrieval practice, and exam-style understanding checks."
        )
    return (
        "Course archetype: guided learning path. Adapt the module names, examples, drills, "
        "sequence, and challenge scenarios to the actual subject instead of using a generic "
        "job-prep or software-project frame."
    )


def _user_message(instruction: str, learner: str, material: str,
                  context: str = "", learning_style: str = "mixed",
                  max_chars: int = 24000) -> str:
    learner_hint = ("Audience: a child / the specified grade level. Use meta.learner=\"kid\"."
                    if learner == "kid" else
                    "Audience: an adult learner. Use meta.learner=\"adult\".")
    style_hint = (
        "Study preference: "
        f"{learning_style if learning_style in {'mixed', 'visual', 'practice', 'read', 'audio'} else 'mixed'}. "
        "Use this as a starting preference, but keep the course multimodal."
    )
    trimmed = material[:max_chars]
    if len(material) > max_chars:
        trimmed += "\n\n[material truncated for length]"
    context_block = f"\nADDITIONAL CONTEXT (goals, constraints, focus areas):\n{context.strip()}\n" \
        if context and context.strip() else ""
    design_hint = _course_design_hint(instruction, material)
    return (f"INSTRUCTION: {instruction}\n{learner_hint}\n{style_hint}\n"
            f"COURSE DESIGN ADAPTATION:\n{design_hint}\n"
            f"{context_block}\nMATERIAL:\n{trimmed}")


# ----------------------------------------------------------------------------
# 2. Model backends — all over HTTP. Each returns the raw text the model emitted.
# ----------------------------------------------------------------------------
# Default model per provider. Override with PREP_MODEL or a per-request `model`.
DEFAULT_MODELS = {
    "gateway": "openai/gpt-5.4",
    "gemini": "gemini-2.0-flash",
    "groq": "llama-3.3-70b-versatile",
    "grok": "grok-3-mini",
    "openai": "gpt-4o-mini",
    "openrouter": "openrouter/free",
    "anthropic": "claude-sonnet-4-20250514",
}

# Which env var holds each provider's key.
ENV_KEYS = {
    "gateway": "AI_GATEWAY_API_KEY",
    "gemini": "GEMINI_API_KEY",
    "groq": "GROQ_API_KEY",
    "grok": "XAI_API_KEY",
    "openai": "OPENAI_API_KEY",
    "openrouter": "OPENROUTER_API_KEY",
    "anthropic": "ANTHROPIC_API_KEY",
}

_HTTP_TIMEOUT = httpx.Timeout(120.0, connect=15.0)


def _max_output_tokens() -> int:
    raw = os.environ.get("PREP_MAX_OUTPUT_TOKENS", "").strip()
    try:
        value = int(raw) if raw else 12000
    except ValueError:
        value = 12000
    return max(4000, min(value, 24000))


def _strict_generation_required() -> bool:
    return os.environ.get("PREP_STRICT_GENERATION", "").strip().lower() in {"1", "true", "yes"}


def _call_gemini(system: str, user: str, api_key: str, model: str) -> str:
    url = (f"https://generativelanguage.googleapis.com/v1beta/models/"
           f"{model}:generateContent")
    payload = {
        "system_instruction": {"parts": [{"text": system}]},
        "contents": [{"role": "user", "parts": [{"text": user}]}],
        "generationConfig": {"temperature": 0.3, "response_mime_type": "application/json"},
    }
    with httpx.Client(timeout=_HTTP_TIMEOUT) as c:
        r = c.post(url, headers={"x-goog-api-key": api_key}, json=payload)
    _raise_for_provider(r, "Gemini")
    data = r.json()
    try:
        return data["candidates"][0]["content"]["parts"][0]["text"]
    except (KeyError, IndexError):
        raise GenerationError(f"Gemini returned no content: {json.dumps(data)[:300]}")


def _call_openai_compatible(system: str, user: str, api_key: str, model: str,
                            base_url: str, label: str,
                            extra_headers: dict[str, str] | None = None) -> str:
    payload = {
        "model": model,
        "temperature": 0.3,
        "max_tokens": _max_output_tokens(),
        "response_format": {"type": "json_object"},
        "messages": [{"role": "system", "content": system},
                     {"role": "user", "content": user}],
    }
    headers = {"Authorization": f"Bearer {api_key}"}
    if extra_headers:
        headers.update(extra_headers)
    with httpx.Client(timeout=_HTTP_TIMEOUT) as c:
        r = c.post(f"{base_url}/chat/completions", headers=headers, json=payload)
    _raise_for_provider(r, label)
    data = r.json()
    try:
        return data["choices"][0]["message"]["content"]
    except (KeyError, IndexError):
        raise GenerationError(f"{label} returned no content: {json.dumps(data)[:300]}")


def _call_gateway(system: str, user: str, api_key: str, model: str) -> str:
    return _call_openai_compatible(system, user, api_key, model,
                                   "https://ai-gateway.vercel.sh/v1", "AI Gateway")


def _call_groq(system: str, user: str, api_key: str, model: str) -> str:
    return _call_openai_compatible(system, user, api_key, model,
                                   "https://api.groq.com/openai/v1", "Groq")


def _call_grok(system: str, user: str, api_key: str, model: str) -> str:
    return _call_openai_compatible(system, user, api_key, model,
                                   "https://api.x.ai/v1", "Grok")


def _call_openai(system: str, user: str, api_key: str, model: str) -> str:
    return _call_openai_compatible(system, user, api_key, model,
                                   "https://api.openai.com/v1", "OpenAI")


def _call_openrouter(system: str, user: str, api_key: str, model: str) -> str:
    headers = {}
    site_url = os.environ.get("OPENROUTER_SITE_URL", "").strip()
    app_name = os.environ.get("OPENROUTER_APP_NAME", "").strip()
    if site_url:
        headers["HTTP-Referer"] = site_url
    if app_name:
        headers["X-Title"] = app_name
    return _call_openai_compatible(system, user, api_key, model,
                                   "https://openrouter.ai/api/v1", "OpenRouter",
                                   extra_headers=headers)


def _call_anthropic(system: str, user: str, api_key: str, model: str) -> str:
    payload = {
        "model": model,
        "max_tokens": _max_output_tokens(),
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
    "gateway": _call_gateway,
    "gemini": _call_gemini,
    "groq": _call_groq,
    "grok": _call_grok,
    "openai": _call_openai,
    "openrouter": _call_openrouter,
    "anthropic": _call_anthropic,
}


def _raise_for_provider(r: httpx.Response, label: str) -> None:
    if r.status_code == 200:
        return
    detail = r.text[:300]
    log.warning("%s provider error HTTP %s: %s", label, r.status_code, detail)
    if r.status_code in (401, 403):
        raise GenerationError(f"{label} rejected the API key (HTTP {r.status_code}). "
                              "Check the key and that the API is enabled.")
    if r.status_code == 429:
        raise GenerationError(f"{label} rate limit / quota hit (HTTP 429). "
                              "Wait a moment or switch providers / add a paid key.")
    raise GenerationError(f"{label} could not complete the request (HTTP {r.status_code}). "
                          "Try again or switch providers.")


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


VALID_TYPES = {"overview", "concept_cards", "flashcards", "visual_map",
               "drag_sort", "teach_back", "notes", "audio_script",
               "glossary", "cheatsheet", "sequence", "challenge"}
VALID_KINDS = {"quiz", "rounds", "timed", "classify"}
VALID_STYLES = {"mixed", "visual", "practice", "read", "audio"}
REQUIRED_GENERATED_TYPES = {"overview", "concept_cards", "flashcards", "visual_map",
                            "drag_sort", "teach_back", "notes", "glossary",
                            "cheatsheet", "sequence"}
REQUIRED_GENERATED_CHALLENGES = {"quiz", "rounds", "timed"}
MIN_GENERATED_MODULES = 12


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
    if meta and meta.get("learningStyle") not in (None, *VALID_STYLES):
        errs.append("meta.learningStyle must be one of mixed, visual, practice, read, audio.")

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
        elif mtype == "visual_map":
            nodes = data.get("nodes")
            links = data.get("links")
            if not isinstance(nodes, list) or not nodes:
                errs.append(f"{where} visual_map needs a nodes array.")
            elif not isinstance(links, list):
                errs.append(f"{where} visual_map needs a links array.")
            else:
                ids = {n.get("id") for n in nodes if isinstance(n, dict)}
                for j, link in enumerate(links):
                    if link.get("from") not in ids or link.get("to") not in ids:
                        errs.append(f"{where} link[{j}] must reference node ids.")
        elif mtype == "drag_sort":
            buckets = data.get("buckets")
            items = data.get("items")
            if not isinstance(buckets, list) or len(buckets) < 2:
                errs.append(f"{where} drag_sort needs at least two buckets.")
            elif not isinstance(items, list) or not items:
                errs.append(f"{where} drag_sort needs an items array.")
            else:
                bucket_ids = {b.get("id") for b in buckets if isinstance(b, dict)}
                for j, item in enumerate(items):
                    if item.get("bucket") not in bucket_ids:
                        errs.append(f"{where} item[{j}] bucket must reference a bucket id.")
        elif mtype == "teach_back":
            prompts = data.get("prompts")
            if not isinstance(prompts, list) or not prompts:
                errs.append(f"{where} teach_back needs a prompts array.")
            else:
                for j, prompt in enumerate(prompts):
                    if not prompt.get("q") or not isinstance(prompt.get("keyPoints"), list):
                        errs.append(f"{where} prompt[{j}] needs q and keyPoints.")
        elif mtype == "notes":
            sections = data.get("sections")
            if not isinstance(sections, list) or not sections:
                errs.append(f"{where} notes needs a sections array.")
        elif mtype == "audio_script":
            segments = data.get("segments")
            if not isinstance(segments, list) or not segments:
                errs.append(f"{where} audio_script needs a segments array.")
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


def _module_by_type(course: dict, mtype: str) -> list[dict]:
    return [m for m in course.get("modules", []) if isinstance(m, dict) and m.get("type") == mtype]


def _challenge_by_kind(course: dict, kind: str) -> list[dict]:
    return [
        m for m in _module_by_type(course, "challenge")
        if isinstance(m.get("data"), dict) and m["data"].get("kind") == kind
    ]


def _count_first(course: dict, mtype: str, field: str) -> int:
    modules = _module_by_type(course, mtype)
    if not modules or not isinstance(modules[0].get("data"), dict):
        return 0
    value = modules[0]["data"].get(field)
    return len(value) if isinstance(value, list) else 0


def validate_generation_design(course: dict) -> list[str]:
    """Quality gate for newly generated courses. Stricter than renderer validation."""
    errs = validate(course)
    if errs:
        return errs
    modules = course.get("modules", [])
    if len(modules) < MIN_GENERATED_MODULES:
        errs.append(f"generated course must include at least {MIN_GENERATED_MODULES} modules.")

    present_types = {m.get("type") for m in modules if isinstance(m, dict)}
    for mtype in sorted(REQUIRED_GENERATED_TYPES - present_types):
        errs.append(f"generated course missing required {mtype} module.")

    present_challenges = {
        m.get("data", {}).get("kind") for m in _module_by_type(course, "challenge")
        if isinstance(m.get("data"), dict)
    }
    for kind in sorted(REQUIRED_GENERATED_CHALLENGES - present_challenges):
        errs.append(f"generated course missing required challenge kind '{kind}'.")

    minimums = [
        ("overview", "cards", 3),
        ("concept_cards", "cards", 5),
        ("flashcards", "cards", 10),
        ("glossary", "terms", 10),
        ("notes", "sections", 4),
        ("cheatsheet", "blocks", 5),
        ("visual_map", "nodes", 5),
        ("drag_sort", "items", 8),
        ("teach_back", "prompts", 4),
    ]
    for mtype, field, minimum in minimums:
        count = _count_first(course, mtype, field)
        if count and count < minimum:
            errs.append(f"{mtype}.{field} should include at least {minimum} items.")

    sequences = _module_by_type(course, "sequence")
    if sequences:
        modes = sequences[0].get("data", {}).get("modes", [])
        if isinstance(modes, list) and modes:
            first_items = modes[0].get("items", [])
            if isinstance(first_items, list) and len(first_items) < 5:
                errs.append("sequence modes should include at least 5 items.")

    challenge_minimums = {"quiz": 8, "rounds": 4, "timed": 6}
    for kind, minimum in challenge_minimums.items():
        challenges = _challenge_by_kind(course, kind)
        if challenges:
            rounds = challenges[0].get("data", {}).get("rounds", [])
            if isinstance(rounds, list) and len(rounds) < minimum:
                errs.append(f"challenge kind '{kind}' should include at least {minimum} rounds.")

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
                 context: str = "", learning_style: str = "mixed",
                 retries: int = 2) -> tuple[dict, str]:
    """Returns (course_dict, finished_html). Raises GenerationError on failure."""
    template = Path(template_path).read_text(encoding="utf-8")
    learning_style = learning_style if learning_style in VALID_STYLES else "mixed"
    user = _user_message(instruction, learner, material,
                         context=context, learning_style=learning_style)

    prov = resolve_provider(provider)
    key = resolve_key(prov, api_key)
    mdl = (model or os.environ.get("PREP_MODEL") or DEFAULT_MODELS[prov])

    last_errs: list[str] = []
    best_schema_valid: dict | None = None
    for attempt in range(retries + 1):
        sys_prompt = SYSTEM_PROMPT
        if attempt > 0 and last_errs:
            sys_prompt += ("\n\nYour previous output had these problems — fix them and "
                           "return corrected JSON only:\n- " + "\n- ".join(last_errs))
        raw = _generate_json(sys_prompt, user, prov, key, mdl)
        course = _extract_json(raw)
        meta = course.setdefault("meta", {})
        meta.setdefault("learner", learner)
        meta.setdefault("learningStyle", learning_style)
        schema_errs = validate(course)
        if schema_errs:
            last_errs = schema_errs
            continue
        best_schema_valid = course
        design_errs = validate_generation_design(course)
        if not design_errs:
            return course, inject(course, template)
        last_errs = design_errs

    if best_schema_valid is not None and not _strict_generation_required():
        best_schema_valid.setdefault("meta", {})["qualityWarning"] = (
            "The model returned a schema-valid course but missed some richness targets."
        )
        log.warning("Returning schema-valid course despite design gaps: %s", "; ".join(last_errs[:6]))
        return best_schema_valid, inject(best_schema_valid, template)

    raise GenerationError("Validation failed after retry:\n- " + "\n- ".join(last_errs))

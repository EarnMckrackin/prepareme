"""
Offline QA suite for the Prep Suite Generator.

The runtime deps (httpx, fastapi, trafilatura) aren't installed in this sandbox, so we
inject lightweight stubs into sys.modules *before* importing the app modules. This lets us
exercise the real application logic (validation, JSON extraction, template injection,
provider tables, rate limiting, SSRF guard, build_course retry loop) without a network.

Run:  python tests/run_qa.py
Exit code is non-zero if any check fails.
"""

import asyncio
import importlib
import json
import os
import pathlib
import sys
import types

ROOT = pathlib.Path(__file__).resolve().parent.parent
API = ROOT / "api"
sys.path.insert(0, str(API))

# ---------------------------------------------------------------------------
# results
# ---------------------------------------------------------------------------
PASS, FAIL = [], []


def check(name, cond, detail=""):
    (PASS if cond else FAIL).append(name)
    mark = "✅" if cond else "❌"
    print(f"{mark} {name}" + (f"  — {detail}" if detail and not cond else ""))


def expect_raises(name, fn, exc):
    try:
        fn()
        check(name, False, "no exception raised")
    except exc:
        check(name, True)
    except Exception as e:  # noqa: BLE001
        check(name, False, f"wrong exception {type(e).__name__}: {e}")


def make_rich_course():
    def rounds(prefix, n):
        return [
            {
                "title": f"{prefix} {i}",
                "scenario": f"Scenario {i}",
                "question": f"What should happen in {prefix} {i}?",
                "opts": ["first", "second", "third"],
                "correct": i % 3,
                "exp": "Because this option matches the source concept.",
            }
            for i in range(1, n + 1)
        ]

    seq_items = [{"id": f"s{i}", "label": f"Step {i}", "why": f"Reason {i}"}
                 for i in range(1, 6)]
    long_text = ("This is a full, multi-sentence explanation that defines the idea precisely, "
                 "explains how and why it works in practice, and then walks through a concrete "
                 "worked example with specific values so the learner actually understands it.")
    summary_text = ("This section teaches the underlying idea in depth: it states the rule, shows "
                    "the mechanism step by step, and grounds it in a concrete, specific example "
                    "that the learner can reproduce on their own.")
    glossary_def = ("A precise, full-sentence definition of the term that explains what it means "
                    "and gives a concrete example of where it applies.")
    flash_answer = ("A complete answer that explains the reasoning and includes a specific, "
                    "concrete example rather than merely restating the term itself.")
    return {
        "meta": {"title": "Rich Course", "subtitle": "QA", "learner": "adult",
                 "learningStyle": "mixed"},
        "modules": [
            {"type": "overview", "id": "overview", "label": "1. Overview",
             "data": {"kicker": "Start", "headline": "A complete course",
                      "body": ("This course gives a complete, in-depth tour of the subject, moving "
                               "from core concepts to concrete worked examples and hands-on "
                               "practice so the learner finishes with real, applicable understanding."),
                      "cards": [
                          {"tag": f"T{i}", "title": f"Card {i}", "text": "Text"}
                          for i in range(1, 4)
                      ], "stepsTitle": "Path", "steps": ["A", "B", "C"]}},
            {"type": "visual_map", "id": "map", "label": "2. Map",
             "data": {"title": "Map", "intro": "Intro",
                      "nodes": [{"id": f"n{i}", "label": f"Node {i}", "tag": "tag",
                                 "summary": "Summary"} for i in range(1, 6)],
                      "links": [{"from": "n1", "to": "n2", "label": "to"}]}},
            {"type": "concept_cards", "id": "concepts", "label": "3. Concepts",
             "data": {"intro": "Intro", "cards": [
                 {"badge": "B", "name": f"Concept {i}",
                  "fields": [{"label": "Idea", "text": long_text, "tone": "info"},
                             {"label": "Example", "text": long_text, "tone": "good"}],
                  "highlight": {"label": "Trap", "q": "Mistake?", "a": "Avoid it."}}
                 for i in range(1, 6)
             ]}},
            {"type": "drag_sort", "id": "sort", "label": "4. Sort",
             "data": {"title": "Sort", "intro": "Intro",
                      "buckets": [{"id": "a", "label": "A", "hint": "A"},
                                  {"id": "b", "label": "B", "hint": "B"}],
                      "items": [{"id": f"it{i}", "label": f"Item {i}",
                                 "detail": "Detail", "bucket": "a" if i % 2 else "b"}
                                for i in range(1, 9)]}},
            {"type": "flashcards", "id": "cards", "label": "5. Cards",
             "data": {"cards": [{"q": f"Q{i}", "a": flash_answer} for i in range(1, 11)]}},
            {"type": "challenge", "id": "quiz", "label": "6. Quiz",
             "data": {"kind": "quiz", "title": "Quiz", "intro": "Intro",
                      "startLabel": "Start", "rounds": rounds("Quiz", 8)}},
            {"type": "teach_back", "id": "teach", "label": "7. Teach",
             "data": {"title": "Teach", "intro": "Intro", "prompts": [
                 {"q": f"Explain {i}", "keyPoints": ["A", "B"], "sample": "Sample"}
                 for i in range(1, 5)
             ]}},
            {"type": "challenge", "id": "rounds", "label": "8. Apply",
             "data": {"kind": "rounds", "title": "Apply", "intro": "Intro",
                      "startLabel": "Start", "rounds": rounds("Apply", 4)}},
            {"type": "challenge", "id": "timed", "label": "9. Speed",
             "data": {"kind": "timed", "title": "Speed", "intro": "Intro",
                      "startLabel": "Start", "timer": 20, "rounds": rounds("Speed", 6)}},
            {"type": "glossary", "id": "glossary", "label": "10. Terms",
             "data": {"intro": "Intro",
                      "terms": [{"t": f"Term {i}", "d": glossary_def}
                                for i in range(1, 11)]}},
            {"type": "notes", "id": "notes", "label": "11. Notes",
             "data": {"title": "Notes", "intro": "Intro", "sections": [
                 {"heading": f"Section {i}", "summary": summary_text,
                  "bullets": ["One", "Two"], "check": "Check"}
                 for i in range(1, 5)
             ]}},
            {"type": "cheatsheet", "id": "sheet", "label": "12. Sheet",
             "data": {"title": "Sheet", "intro": "Intro",
                      "blocks": [{"title": f"Block {i}", "text": "Text"}
                                 for i in range(1, 6)]}},
            {"type": "sequence", "id": "sequence", "label": "13. Order",
             "data": {"title": "Order", "intro": "Intro",
                      "modes": [{"key": "main", "label": "Main",
                                 "items": seq_items,
                                 "correct": [item["id"] for item in seq_items]}]}},
        ],
    }


# ---------------------------------------------------------------------------
# dependency stubs
# ---------------------------------------------------------------------------
def install_stubs():
    # ---- httpx -----------------------------------------------------------
    httpx = types.ModuleType("httpx")

    class Timeout:
        def __init__(self, *a, **k):
            pass

    class HTTPError(Exception):
        pass

    class Response:
        def __init__(self, status_code=200, text="", data=None, headers=None):
            self.status_code = status_code
            self.text = text
            self._data = data or {}
            self.headers = headers or {}
            self.encoding = "utf-8"

        def json(self):
            return self._data

        async def aiter_bytes(self):
            yield self.text.encode("utf-8")

    class _Client:
        def __init__(self, *a, **k):
            pass

        def __enter__(self):
            return self

        def __exit__(self, *a):
            return False

        def get(self, *a, **k):
            return Response(200, "<html><body><p>stub</p></body></html>")

        def post(self, *a, **k):
            return Response(200, data={})

    class _AsyncClient:
        def __init__(self, *a, **k):
            pass

        async def __aenter__(self):
            return self

        async def __aexit__(self, *a):
            return False

        def stream(self, *a, **k):
            class _Stream:
                async def __aenter__(self):
                    return Response(200, "<html><body><p>stub</p></body></html>")

                async def __aexit__(self, *a):
                    return False

            return _Stream()

        async def post(self, *a, **k):
            return Response(200, data=[{"result": 1}, {"result": 1}])

        async def get(self, *a, **k):
            return Response(200, "<html><body><p>stub</p></body></html>")

    httpx.Timeout = Timeout
    httpx.HTTPError = HTTPError
    httpx.Response = Response
    httpx.Client = _Client
    httpx.AsyncClient = _AsyncClient
    sys.modules["httpx"] = httpx

    # ---- fastapi (minimal) ----------------------------------------------
    fastapi = types.ModuleType("fastapi")

    class FastAPI:
        def __init__(self, *a, **k):
            pass

        def _deco(self, *a, **k):
            def wrap(fn):
                return fn
            return wrap

        get = _deco
        post = _deco
        middleware = _deco

    class Request:  # noqa: D401
        pass

    class UploadFile:
        pass

    def Form(default="", **k):
        return default

    def File(default=None, **k):
        return default

    class HTTPException(Exception):
        def __init__(self, status_code, detail=""):
            self.status_code = status_code
            self.detail = detail
            super().__init__(detail)

    fastapi.FastAPI = FastAPI
    fastapi.Request = Request
    fastapi.UploadFile = UploadFile
    fastapi.Form = Form
    fastapi.File = File
    fastapi.HTTPException = HTTPException

    responses = types.ModuleType("fastapi.responses")

    class HTMLResponse:
        def __init__(self, *a, **k):
            pass

    class FileResponse:
        def __init__(self, *a, **k):
            pass

    responses.HTMLResponse = HTMLResponse
    responses.FileResponse = FileResponse
    fastapi.responses = responses
    sys.modules["fastapi"] = fastapi
    sys.modules["fastapi.responses"] = responses

    # NOTE: trafilatura intentionally NOT stubbed -> exercises the regex fallback path.


# ---------------------------------------------------------------------------
# the suite
# ---------------------------------------------------------------------------
def main():
    install_stubs()
    gen = importlib.import_module("_generator")

    # --- 1. provider table consistency -----------------------------------
    pkeys = set(gen.PROVIDERS)
    check("providers: PROVIDERS == ENV_KEYS keys", pkeys == set(gen.ENV_KEYS))
    check("providers: PROVIDERS == DEFAULT_MODELS keys", pkeys == set(gen.DEFAULT_MODELS))

    ui = (API / "_ui.html").read_text()
    import re
    provider_select = re.search(r'<select name="provider"[\s\S]*?</select>', ui)
    ui_opts = set(re.findall(r'<option value="([^"]+)">',
                             provider_select.group(0) if provider_select else ""))
    check("providers: UI dropdown matches PROVIDERS", ui_opts == pkeys,
          f"ui={sorted(ui_opts)} providers={sorted(pkeys)}")
    style_select = re.search(r'<select name="learning_style"[\s\S]*?</select>', ui)
    style_opts = set(re.findall(r'<option value="([^"]+)">',
                                style_select.group(0) if style_select else ""))
    check("learning styles: UI includes all preferences",
          style_opts == {"mixed", "visual", "practice", "read", "audio"}, str(sorted(style_opts)))
    check("ui: generated courses saved locally",
          "prepareme_generated_courses_v1" in ui and "storeGeneratedCourse" in ui)
    check("ui: server courses removable locally",
          "prepareme_hidden_library_courses_v1" in ui and "hideLibraryCourse" in ui
          and "restoreHiddenLibraryCourses" in ui)
    check("ui: BYOK exposes OpenRouter paid models",
          "const byok=!!document.getElementById('api_key').value.trim();" in ui)

    env_example = (ROOT / ".env.example").read_text()
    missing_env = [v for v in gen.ENV_KEYS.values() if v not in env_example]
    check("providers: every ENV key documented in .env.example", not missing_env, str(missing_env))

    # --- 2. normalize_url / html-to-text ---------------------------------
    check("normalize_url adds https", gen.normalize_url("example.com") == "https://example.com")
    check("normalize_url keeps http", gen.normalize_url("http://x.io") == "http://x.io")

    txt = gen._regex_html_to_text(
        "<html><head><style>a{}</style></head><body><nav>Menu</nav>"
        "<p>Hello&nbsp;world.</p><script>bad()</script><p>Bye.</p></body></html>")
    check("regex_html_to_text strips script/style", "bad()" not in txt and "a{}" not in txt)
    check("regex_html_to_text keeps content", "Hello world." in txt and "Bye." in txt)

    em = gen.extract_main_text("<html><body><p>Main content here.</p></body></html>", "https://x.com")
    check("extract_main_text fallback returns text", "Main content here." in em)

    # --- 3. JSON extraction ----------------------------------------------
    check("extract_json: plain", gen._extract_json('{"a":1}') == {"a": 1})
    check("extract_json: fenced", gen._extract_json('```json\n{"a":1}\n```') == {"a": 1})
    check("extract_json: embedded prose",
          gen._extract_json('here you go: {"a":1} thanks') == {"a": 1})
    expect_raises("extract_json: garbage raises", lambda: gen._extract_json("no json here"),
                  gen.GenerationError)

    # --- 4. validate ------------------------------------------------------
    good = {
        "meta": {"title": "T", "learner": "adult", "learningStyle": "mixed"},
        "modules": [
            {"type": "flashcards", "id": "f1", "label": "1. Cards",
             "data": {"cards": [{"q": "a", "a": "b"}]}},
            {"type": "challenge", "id": "q1", "label": "2. Quiz",
             "data": {"kind": "quiz", "rounds": [
                 {"question": "Q?", "opts": ["x", "y"], "correct": 1}]}},
        ],
    }
    check("validate: good course passes", gen.validate(good) == [])

    check("validate: missing title", any("title" in e for e in gen.validate(
        {"meta": {}, "modules": good["modules"]})))
    check("validate: empty modules", any("modules" in e for e in gen.validate(
        {"meta": {"title": "T"}, "modules": []})))
    dup = {"meta": {"title": "T"}, "modules": [good["modules"][0], good["modules"][0]]}
    check("validate: duplicate id", any("duplicate" in e for e in gen.validate(dup)))
    badkind = {"meta": {"title": "T"}, "modules": [
        {"type": "challenge", "id": "c1", "label": "L",
         "data": {"kind": "nope", "rounds": [{"question": "q", "opts": ["a", "b"], "correct": 0}]}}]}
    check("validate: bad challenge kind", any("kind" in e for e in gen.validate(badkind)))
    oob = {"meta": {"title": "T"}, "modules": [
        {"type": "challenge", "id": "c1", "label": "L",
         "data": {"kind": "quiz", "rounds": [{"question": "q", "opts": ["a", "b"], "correct": 9}]}}]}
    check("validate: correct index out of range", any("range" in e for e in gen.validate(oob)))
    badseq = {"meta": {"title": "T"}, "modules": [
        {"type": "sequence", "id": "s1", "label": "L", "data": {"modes": [
            {"key": "m", "label": "m", "items": [{"id": "i1", "label": "a", "why": "w"}],
             "correct": ["i1", "i2"]}]}}]}
    check("validate: sequence id mismatch", any("ids must match" in e for e in gen.validate(badseq)))
    rich = make_rich_course()
    check("validate_generation_design: rich course passes",
          gen.validate_generation_design(rich) == [])
    check("validate_generation_design: thin course rejected",
          any("at least" in e or "missing required" in e
              for e in gen.validate_generation_design(good)))

    # --- 5. inject into the real template --------------------------------
    template = (API / "_course_template.html").read_text()
    injected = gen.inject(good, template)
    check("inject: course title present in html", '"title": "T"' in injected)
    m = re.search(r"const COURSE =\s*([\s\S]*?)\n\s*;", injected)
    check("inject: COURSE block parses back to same course",
          bool(m) and json.loads(m.group(1)) == good)
    expect_raises("inject: missing marker raises",
                  lambda: gen.inject(good, "<html>no marker</html>"), gen.GenerationError)

    # --- 6. _user_message context ----------------------------------------
    um = gen._user_message("do it", "adult", "MAT", context="focus on X")
    check("user_message: includes context block", "ADDITIONAL CONTEXT" in um and "focus on X" in um)
    um2 = gen._user_message("do it", "adult", "MAT", context="")
    check("user_message: omits empty context", "ADDITIONAL CONTEXT" not in um2)
    um3 = gen._user_message("do it", "kid", "MAT")
    check("user_message: kid hint", 'meta.learner="kid"' in um3)
    um4 = gen._user_message("Jazz theory course", "adult", "ii V I chord substitutions")
    check("user_message: jazz adaptation hint",
          "creative musical practice path" in um4 and "Avoid interview" in um4)

    # --- 7. resolve_provider / resolve_key -------------------------------
    check("resolve_provider: default gemini", gen.resolve_provider(None) == "gemini")
    check("resolve_provider: grok valid", gen.resolve_provider("grok") == "grok")
    expect_raises("resolve_provider: unknown raises",
                  lambda: gen.resolve_provider("bogus"), gen.GenerationError)
    check("resolve_key: from arg", gen.resolve_key("gemini", "abc") == "abc")
    expect_raises("resolve_key: missing raises",
                  lambda: gen.resolve_key("openai", ""), gen.GenerationError)

    # --- 8. build_course retry loop (mock provider) ----------------------
    tpl_path = API / "_course_template.html"
    valid_json = json.dumps(rich)
    invalid_json = json.dumps({"meta": {}, "modules": []})

    # 8a: succeeds first try
    gen.PROVIDERS["gemini"] = lambda s, u, k, m: valid_json
    course, html = gen.build_course("i", "mat", "adult", tpl_path, provider="gemini", api_key="x")
    check("build_course: success returns injected html",
          course == rich and '"title": "Rich Course"' in html)

    # 8b: invalid then valid -> retry recovers
    seq = iter([invalid_json, valid_json])
    gen.PROVIDERS["gemini"] = lambda s, u, k, m: next(seq)
    course2, _ = gen.build_course("i", "mat", "adult", tpl_path, provider="gemini", api_key="x")
    check("build_course: recovers on retry", course2 == rich)

    # 8c: schema-valid but thin output. Strict generation is ON by default, so it must raise;
    # opting out (PREP_STRICT_GENERATION=0) restores the warning-tagged fallback.
    gen.PROVIDERS["gemini"] = lambda s, u, k, m: valid_json.replace('"Rich Course"', '"Unused"')
    gen.PROVIDERS["openai"] = lambda s, u, k, m: json.dumps(good)
    old_log_disabled = gen.log.disabled
    gen.log.disabled = True
    try:
        os.environ["PREP_STRICT_GENERATION"] = "0"
        try:
            fallback_course, _ = gen.build_course("i", "mat", "adult", tpl_path,
                                                  provider="openai", api_key="x")
            check("build_course: design-short schema-valid fallback returns (opt-out)",
                  fallback_course["meta"].get("qualityWarning") and fallback_course["meta"]["title"] == "T")
        finally:
            os.environ.pop("PREP_STRICT_GENERATION", None)
    finally:
        gen.log.disabled = old_log_disabled
    expect_raises("build_course: strict mode (default) rejects design-short output",
                  lambda: gen.build_course("i", "mat", "adult", tpl_path,
                                           provider="openai", api_key="x"),
                  gen.GenerationError)

    # 8d: always invalid -> raises after retry
    gen.PROVIDERS["gemini"] = lambda s, u, k, m: invalid_json
    expect_raises("build_course: fails after retries",
                  lambda: gen.build_course("i", "mat", "adult", tpl_path,
                                           provider="gemini", api_key="x"),
                  gen.GenerationError)

    # --- 9. index.py: rate limit, SSRF guard, upload, extract_text -------
    idx = importlib.import_module("index")
    HttpxResponse = sys.modules["httpx"].Response

    class DummyRequest:
        def __init__(self, query=None, headers=None, cookies=None):
            self.query_params = query or {}
            self.headers = headers or {}
            self.cookies = cookies or {}
            self.client = types.SimpleNamespace(host="127.0.0.1")

    # rate limit
    idx._rate_window.clear()
    allowed = sum(1 for _ in range(idx._RATE_LIMIT) if idx._check_rate_limit("1.2.3.4"))
    blocked = not idx._check_rate_limit("1.2.3.4")
    check("rate_limit: allows up to limit", allowed == idx._RATE_LIMIT)
    check("rate_limit: blocks over limit", blocked)
    check("rate_limit: per-IP isolation", idx._check_rate_limit("9.9.9.9"))

    # SSRF guard (monkeypatch DNS to avoid network)
    import socket as _sock
    def fake_getaddrinfo(host, port, *a, **k):
        addrs = {
            "evil.local": ["127.0.0.1"],
            "intra": ["10.0.0.5"],
            "mixed.local": ["93.184.216.34", "10.0.0.5"],
            "ok.com": ["93.184.216.34"],
        }.get(host, ["93.184.216.34"])
        return [(None, None, None, "", (addr, port)) for addr in addrs]

    idx.socket.getaddrinfo = fake_getaddrinfo
    expect_raises("ssrf: loopback blocked",
                  lambda: idx._assert_public_url("http://evil.local/"), gen.GenerationError)
    expect_raises("ssrf: private blocked",
                  lambda: idx._assert_public_url("http://intra/"), gen.GenerationError)
    expect_raises("ssrf: mixed public/private DNS blocked",
                  lambda: idx._assert_public_url("http://mixed.local/"), gen.GenerationError)
    expect_raises("ssrf: non-http scheme blocked",
                  lambda: idx._assert_public_url("ftp://ok.com/"), gen.GenerationError)
    try:
        idx._assert_public_url("https://ok.com/page")
        check("ssrf: public url allowed", True)
    except Exception as e:  # noqa: BLE001
        check("ssrf: public url allowed", False, str(e))

    class RedirectClient:
        def __init__(self, *a, **k):
            pass

        async def __aenter__(self):
            return self

        async def __aexit__(self, *a):
            return False

        def stream(self, method, url):
            class _Stream:
                async def __aenter__(self):
                    return HttpxResponse(302, headers={"Location": "http://intra/latest"})

                async def __aexit__(self, *a):
                    return False

            return _Stream()

    old_async_client = idx.httpx.AsyncClient
    idx.httpx.AsyncClient = RedirectClient
    try:
        expect_raises("fetch_urls: redirect to private host blocked",
                      lambda: asyncio.run(idx.fetch_urls(["https://ok.com/start"])),
                      gen.GenerationError)
    finally:
        idx.httpx.AsyncClient = old_async_client

    class BigResponse:
        encoding = "utf-8"

        async def aiter_bytes(self):
            yield b"x" * (idx._MAX_URL_FETCH_BYTES + 1)

    expect_raises("fetch_urls: response size cap enforced",
                  lambda: asyncio.run(idx._read_limited_response(BigResponse(), "https://ok.com")),
                  gen.GenerationError)
    _ = _sock  # keep ref

    class TavilyClient:
        def __init__(self, *a, **k):
            pass

        async def __aenter__(self):
            return self

        async def __aexit__(self, *a):
            return False

        async def post(self, url, headers=None, json=None):
            return HttpxResponse(200, data={
                "answer": "Short synthesized answer.",
                "results": [{
                    "title": "Primary result",
                    "url": "https://example.com/result",
                    "content": "Relevant search snippet.",
                }],
            })

    old_tavily_key = os.environ.get("TAVILY_API_KEY")
    old_async_client = idx.httpx.AsyncClient
    idx.httpx.AsyncClient = TavilyClient
    os.environ["TAVILY_API_KEY"] = "tvly-test"
    try:
        tavily = asyncio.run(idx.search_tavily(["current AI evaluation methods"]))
        check("tavily: search returns source text",
              len(tavily) == 1 and "Relevant search snippet." in tavily[0][1])
    finally:
        idx.httpx.AsyncClient = old_async_client
        if old_tavily_key is None:
            os.environ.pop("TAVILY_API_KEY", None)
        else:
            os.environ["TAVILY_API_KEY"] = old_tavily_key

    os.environ.pop("TAVILY_API_KEY", None)
    expect_raises("tavily: missing key raises",
                  lambda: asyncio.run(idx.search_tavily(["x"])), gen.GenerationError)
    if old_tavily_key is not None:
        os.environ["TAVILY_API_KEY"] = old_tavily_key

    # extract_text
    check("extract_text: txt decode",
          idx.extract_text("a.txt", b"hello bytes") == "hello bytes")
    expect_raises("extract_text: unknown extension rejected",
                  lambda: idx.extract_text("slides.pptx", b"PK\x03\x04binary"),
                  gen.GenerationError)

    # --- 10. access gates + OpenRouter policy ----------------------------
    saved_env = {k: os.environ.get(k) for k in [
        "PREP_LIBRARY_PUBLIC_IDS",
        "PREP_AUTH_USERS",
        "PREP_AUTH_SECRET",
        "PREP_ACCESS_CODES",
        "PREP_ADMIN_ACCESS_CODE",
        "PREP_OPENROUTER_FREE_MODELS",
        "PREP_OPENROUTER_PAID_MODELS",
        "PREP_OPENROUTER_PAID_MODEL",
        "PREP_MODEL",
    ]}
    try:
        os.environ["PREP_LIBRARY_PUBLIC_IDS"] = "gen-ai-learning-lab"
        os.environ["PREP_ACCESS_CODES"] = json.dumps({
            "alice-code": {
                "user": "alice",
                "library": ["grayscale-interview-prep"],
                "openrouter_paid": True,
            }
        })
        os.environ["PREP_AUTH_USERS"] = json.dumps({
            "devin": {
                "passcode": "prepareme",
                "library": ["*"],
                "openrouter_paid": True,
            }
        })
        os.environ["PREP_AUTH_SECRET"] = "test-session-secret"
        os.environ.pop("PREP_ADMIN_ACCESS_CODE", None)
        os.environ["PREP_OPENROUTER_FREE_MODELS"] = "openrouter/free,meta/test:free"
        os.environ["PREP_OPENROUTER_PAID_MODELS"] = "openai/gpt-4o-mini"
        public_req = DummyRequest()
        alice_req = DummyRequest(query={"access_code": "alice-code"})
        devin_req = DummyRequest(cookies={
            idx.SESSION_COOKIE: idx._session_cookie("devin"),
        })

        public_ids = {c["id"] for c in idx._filter_library_for_request(public_req)}
        alice_ids = {c["id"] for c in idx._filter_library_for_request(alice_req)}
        check("access: public library filtered", public_ids == {"gen-ai-learning-lab"}, str(public_ids))
        check("access: code unlocks course",
              alice_ids == {"gen-ai-learning-lab", "grayscale-interview-prep"}, str(alice_ids))
        devin_ids = {c["id"] for c in idx._filter_library_for_request(devin_req)}
        check("auth: signed session unlocks all courses",
              devin_ids == {"gen-ai-learning-lab", "grayscale-interview-prep",
                            "grayscale-ppm-mastery", "web3-security-foundation"},
              str(devin_ids))
        check("auth: tampered session ignored",
              idx._access_for_request(DummyRequest(cookies={idx.SESSION_COOKIE: "bad.token"}))["user"]
              == "public")
        expect_raises("access: public course route denied",
                      lambda: idx._ensure_course_access(public_req, "grayscale-interview-prep"),
                      idx.HTTPException)
        try:
            idx._ensure_course_access(alice_req, "grayscale-interview-prep")
            check("access: unlocked course route allowed", True)
        except Exception as e:  # noqa: BLE001
            check("access: unlocked course route allowed", False, str(e))

        check("openrouter: public default is free router",
              idx._authorize_model(public_req, "openrouter", "", "") == "openrouter/free")
        check("openrouter: public explicit free model allowed",
              idx._authorize_model(public_req, "openrouter", "meta/test:free", "") == "meta/test:free")
        expect_raises("openrouter: public paid model denied",
                      lambda: idx._authorize_model(public_req, "openrouter", "openai/gpt-4o-mini", ""),
                      idx.HTTPException)
        check("openrouter: BYOK can request paid model",
              idx._authorize_model(public_req, "openrouter", "openai/gpt-4o-mini", "user-key")
              == "openai/gpt-4o-mini")
        check("openrouter: paid code can request paid model",
              idx._authorize_model(alice_req, "openrouter", "openai/gpt-4o-mini", "")
              == "openai/gpt-4o-mini")
        check("openrouter: signed-in user can request paid model",
              idx._authorize_model(devin_req, "openrouter", "openai/gpt-4o-mini", "")
              == "openai/gpt-4o-mini")

        generated_ok = all(not gen.validate(item["course"])
                           for item in idx.GENERATED_COURSES.values())
        check("generated courses: schemas validate", generated_ok)
    finally:
        for key, val in saved_env.items():
            if val is None:
                os.environ.pop(key, None)
            else:
                os.environ[key] = val

    # --- 11. config endpoint sanity --------------------------------------
    cfg = idx.config(DummyRequest())
    check("config: default provider valid", cfg["default"] in gen.PROVIDERS)
    check("config: configured keys cover providers",
          set(cfg["configured"]) == set(gen.PROVIDERS))
    check("config: source flags include tavily",
          "sources" in cfg and "tavily" in cfg["sources"])
    check("config: access and openrouter included",
          "access" in cfg and "openrouter" in cfg)

    # ---------------------------------------------------------------------
    print("\n" + "=" * 60)
    print(f"PASSED {len(PASS)} / {len(PASS) + len(FAIL)}")
    if FAIL:
        print("FAILURES:")
        for f in FAIL:
            print("  -", f)
    print("=" * 60)
    return 1 if FAIL else 0


if __name__ == "__main__":
    sys.exit(main())

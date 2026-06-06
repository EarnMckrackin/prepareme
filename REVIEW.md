# Prepareme — Architecture & Hardening Review

> Review of the current `main` (latest commit: `feat: add Grok to provider dropdown`).
> A checklist of changes to make the product more streamlined and hardened.

## Architecture (as-is)

A single FastAPI serverless function on Vercel that turns documents / URLs / pasted text
into a self-contained interactive study course (`.html`).

```
api/index.py              → web front end: routes, rate limit, SSRF guard, file extraction
api/_generator.py         → engine: prompt, 5 HTTP providers, schema validation, retry, injection
api/_ui.html              → single-page upload form
api/_course_template.html → fixed renderer; COURSE JSON is regex-injected into it
tests/run_qa.py           → offline suite (stubs httpx/fastapi) + GitHub Actions CI
```

**Strengths to preserve:** clean engine/frontend split, no heavy vendor SDKs (small bundle,
fast cold start), BYOK + server keys, schema validation with self-correcting retry, real
offline test suite. The problems are at the edges — abuse resistance, the SSRF guard, and a
few "looks done but isn't quite" spots.

---

## Top 5 (do these first)

1. Fix the SSRF guard — redirects + all-addresses + response size cap (**#1, #2**)
2. Real rate limiting via Vercel WAF/BotID or Upstash (**#3**)
3. Move the Gemini key out of the URL + stop reflecting upstream errors (**#4, #5**)
4. Bump `maxDuration` to match the httpx timeout (**#9**)
5. Adopt Vercel AI Gateway to collapse the provider layer and stop model-ID drift (**#8**)

---

## Hardening — high priority

### 1. SSRF guard is bypassable (most serious)
`_assert_public_url` (`api/index.py:64`) resolves DNS once, but `fetch_urls` uses
`follow_redirects=True`. Three holes:
- **Redirect bypass:** a public URL can `302 → http://169.254.169.254/...` (cloud metadata)
  or to an internal host. Only the first URL is validated; redirect hops are not.
- **DNS rebinding / TOCTOU:** the IP validated isn't guaranteed to be the IP httpx connects to.
- **Multi-record bypass:** `socket.gethostbyname` returns one address; a host with both a
  public and a private A record can slip through.

**Fix:** disable redirects (or validate every hop), use `getaddrinfo` and reject if *any*
resolved address is private, ideally pin the validated IP for the actual connection. Model on
established libraries (e.g. `ssrf-req-filter`) rather than expanding the custom check.

### 2. No response-size cap on URL fetch
`r = await client.get(url)` buffers the entire body before `extract_main_text` trims to 40k
chars. A malicious URL returning gigabytes is an OOM/DoS. **Fix:** stream the response and
abort past a byte ceiling (~5–10 MB).

### 3. Rate limiting is effectively cosmetic
`_rate_window` (`api/index.py:47`) is an in-process dict that resets on cold start; Fluid
Compute runs multiple instances with no shared state, and IP rotation defeats it. The app
exposes *your* server API keys to the open internet → real cost/abuse exposure.
**Options (low → high effort):**
- Vercel WAF rate limiting + BotID (platform-level, near-zero code) — best fit.
- Shared counter in Upstash Redis (Vercel Marketplace) keyed by IP.
- Access token / Sign in with Vercel if it shouldn't be fully public.

### 4. Gemini key travels in the URL query string
`_call_gemini` (`api/_generator.py:166`) uses `?key={api_key}`. Query strings get logged by
proxies/platforms. **Fix:** send it as the `x-goog-api-key` header (like the other providers
use `Authorization`).

### 5. Provider error text is reflected to the user
`_raise_for_provider` (`api/_generator.py:246`) puts `r.text[:300]` from upstream into the
user-facing message. **Fix:** log detail server-side, show the user a generic message.

### 6. No security headers / CSP
Neither the UI nor the generated course sets CSP, `X-Content-Type-Options`,
`Referrer-Policy`, etc. **Fix:** add via FastAPI middleware. Also the UI uses the Tailwind
*browser* CDN (compiles in-browser, not for production) — ship a prebuilt CSS file instead.

### 7. Unbounded text inputs
Only the file upload is capped (10 MB). `pasted`, `context`, `urls`, `instruction` have no
request-body size limit. **Fix:** cap them before the 24k-char model truncation.

---

## Streamlining — biggest levers

### 8. Route through Vercel AI Gateway instead of 5 hand-rolled providers
Highest-leverage change. Today `_generator.py` maintains five bespoke HTTP functions, five
env keys, five hardcoded model IDs (`gemini-2.0-flash`, `grok-3-mini`,
`claude-sonnet-4-20250514` — these *will* drift), and per-provider error handling. AI Gateway
gives `"provider/model"` strings through one endpoint with automatic failover, observability,
and cost tracking — collapsing most of that code and the key-management surface. BYOK still
works as an override.

### 9. `maxDuration: 60` will kill slow generations early
`vercel.json` caps the function at 60s, but the httpx timeout is 120s
(`_HTTP_TIMEOUT`, `api/_generator.py:162`). A slow model gets the function terminated before
its own timeout fires. **Fix:** raise `maxDuration` to 120–300 (platform now allows 300s).

### 10. "Fully standalone" course is not actually offline
The downloaded `.html` pulls Alpine and the Tailwind browser build from jsDelivr at runtime
(`api/_course_template.html`), with no SRI hash (the UI's Tailwind has one; the template's
doesn't). Offline downloads silently break, and a CDN change breaks every previously
downloaded course. **Fix:** inline a prebuilt CSS + Alpine into the template at injection time.

### 11. No persistence → no shareable links
The course only exists as a Blob URL in the generating browser. Storing generated HTML in
Vercel Blob (now supports private storage) and returning a URL would enable sharing *and*
shrink the response (today the whole course is base64'd into memory per request).

### 12. Long blocking request with a spinner
Generation is one synchronous round-trip with no feedback. Streaming partial progress (or
status stages) via the AI SDK / Gateway would make it feel far more responsive.

---

## Smaller items

- **README drift:** provider table omits Grok (added in latest commits). The QA suite checks
  `_ui.html` options against `PROVIDERS` but not the README — extend that check.
- **`extract_text` silent fallback:** unknown extensions fall through to
  `raw.decode("utf-8", errors="replace")` (`api/index.py:155`), turning a binary `.pptx` into
  garbage instead of rejecting it. Reject unknown types explicitly.
- **Test coverage gap:** offline suite doesn't exercise the async `fetch_urls` redirect/SSRF
  path — exactly where the worst bug is. Add a case.
- **`legacy/` in deploy root:** reference-only but still bundled context. Move out of the
  deploy path or document the exclusion.

---

## Suggested sequencing

| Phase | Items | Size |
|---|---|---|
| Quick wins (1 branch) | #4, #5, #9, README/Grok, #7 | small, self-contained |
| Security hardening | #1, #2, #6, test for SSRF redirect path | small–medium |
| Abuse resistance | #3 (WAF/BotID or Upstash) | medium |
| Product streamlining | #8 (AI Gateway), #11 (Blob sharing), #12 (streaming), #10 (inline assets) | larger, separate branches |

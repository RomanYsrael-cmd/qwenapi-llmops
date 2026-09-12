# Security and release checklist

## Secret handling

- Inject `QWEN_API_KEY`, `ROMAN_SEARCH_API_KEY`, and
  `CLOUDFLARE_TUNNEL_TOKEN` through a secret manager or CI secret store.
- Never print a secret, even temporarily. Mask diagnostics by default.
- Rotate any credential that appeared in a notebook output, process list, log,
  screenshot, or browser history. Kaggle version history is immutable evidence;
  deleting a current cell does not guarantee old output is gone.
- Keep `.env` files out of git. `.env.example` contains placeholders only.

## Gateway controls

- Apply authentication middleware to every non-health route, including stream
  lookup/replay/delete and image routes.
- Use constant-time API-key comparison and return generic unauthorized errors.
- Add rate limiting and request-size limits before exposing a public tunnel.
- Keep `/health` minimal; do not expose tokens, filesystem paths, or user data.
- Scope stream ownership to the authenticated caller and expire request state.

## Supply chain and process isolation

- Pin Python dependencies and pin the exact Cloudflare binary version.
- Verify downloaded binaries with a published SHA-256 or signature.
- Extract archives with path-traversal checks; reject absolute paths and `..`.
- Track child-process PIDs and terminate only processes started by this service.
- Avoid passing secrets as command-line arguments because process listings can
  reveal them; prefer inherited environment or file-descriptor mechanisms.

## Data and model safety

- Treat retrieved pages and tool output as untrusted text, not instructions.
- Redact personal data from logs and benchmark fixtures.
- Require live sources for high-stakes categories and show source IDs in the
  final answer. If evidence is insufficient, say so instead of guessing.
- Keep Kaggle as an experiment environment; use a managed service for a real
  production workload with monitoring, quotas, and incident response.

## Before making the project public

- [ ] Rotate/revoke all historical credentials.
- [ ] Remove revealing cells and outputs from Kaggle or publish a clean copy.
- [ ] Run the unit and integration test suite.
- [ ] Add a dependency/binary scan and secret scan in CI.
- [ ] Record cold-start, p50/p95 latency, throughput, concurrency, and VRAM.
- [ ] Confirm the demo notebook makes no network calls by default.

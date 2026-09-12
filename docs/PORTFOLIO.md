# Portfolio presentation

## One-sentence pitch

Designed and operated a source-aware Qwen serving gateway that turns model
tool calls into bounded, cacheable search workflows across dual GPU workers.

## Résumé bullets

- Architected a Qwen3.5 4B GGUF serving stack on dual Tesla T4 GPUs with
  llama.cpp, four concurrent generation slots, health probes, and bounded
  request timeouts.
- Built an OpenAI-compatible FastAPI gateway with a round-robin backend pool,
  source-grounding policy enforcement, Roman Search integration, URL/result
  deduplication, and category-aware TTL caching.
- Validated packaging and recovery behavior, documented security controls, and
  created an offline demo notebook plus dependency-free unit tests for policy,
  search hygiene, and agentic orchestration.

## Skills demonstrated

Python, FastAPI, async HTTP, llama.cpp, GGUF inference, GPU scheduling,
agentic tool-calling, retrieval grounding, caching, API authentication,
observability, packaging, test design, and security review.

## Talking points for an interview

1. Why high-stakes categories override a caller's request to disable grounding.
2. Why a bounded search/runtime budget is safer than an unbounded agent loop.
3. How backend queues and timeouts protect a small GPU pool from overload.
4. Why secrets must be rotated when they appear in immutable notebook history.
5. What would change for production: managed secrets, rate limiting, pinned
   images, metrics, a persistent cache, and a managed GPU runtime.

## Attribution

The implementation was AI-assisted. I owned the requirements, system design,
agent direction, code review, security review, validation, and operation of the
resulting service. This framing is clear about the work without overstating
manual authorship of every generated line.

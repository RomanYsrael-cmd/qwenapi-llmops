# Observed benchmark table

These values are copied from the private Kaggle operational trace and are not
claims about general throughput.

| Scenario | Hardware | Context / slots | Search calls | Sources | Elapsed |
| --- | --- | ---: | ---: | ---: | ---: |
| Agentic legal trace | 2 × Tesla T4 | 32K / 4 | 12 | 46 | ~556 s |
| Runtime packaging recovery | Kaggle T4 session | n/a | n/a | n/a | Passed |

Roman Search latency varied substantially. Before describing performance in a
résumé or interview, measure cold start, single-turn p50/p95, agentic p50/p95,
sustained requests/minute, and VRAM at one, two, and four concurrent turns.

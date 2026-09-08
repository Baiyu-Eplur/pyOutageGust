# Decision log

- 2026-09-06: Created new independent X01 run inside `test`; no R00–R05 repair artifact is edited.
- 2026-09-06: Froze the R02 event snapshot after hash verification; all model reads use the copy.
- 2026-09-06: Chose the fixed 14-day UTC block protocol with named-window union and 48-hour purge because no validated full weather-process ID is present in the frozen input contract.
- 2026-09-06: Pre-registered direct raw-scale conditional mean losses and removed free gust×pressure interaction from every candidate as instructed.
- 2026-09-06: First execution stopped during E/M08 after an overflow in the
  Gompertz derivative below observed support. The analytic zero-limit
  derivative replaced the unstable `inf * 0` calculation before the full run
  was restarted; no ranking was retained from that stopped attempt.
- 2026-09-06: The full restart completed all 27 OOF candidates, the 1,000
  paired OOF draws per task, and six sets of 200 curve refits. Narrative
  rendering then stopped only because optional `tabulate` was unavailable.
  The report renderer was replaced internally and final figures/reports are
  generated from persisted computational artifacts without recomputation.

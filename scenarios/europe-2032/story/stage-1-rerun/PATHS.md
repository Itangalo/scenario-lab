# Stage-1 rerun paths (approved 2026-09-11)

First run per branch (earliest `branch_created_at`), no fault promotions. Election exactly-one holds 60/60. Summaries in `A1.md` … `P2.md` (spare: `P2-rep2.md`).

| branch | path run | rep | seed | turn-5 winner |
|---|---|---|---|---|
| A1 | run-20260910-223510 | 1 | 16131371758201131071 | alliance |
| A2 | run-20260910-224240 | 1 | 3275500770907618172 | retrenchment |
| V1 | run-20260910-224841-01 | 1 | 16469017358909379730 | retrenchment |
| V2 | run-20260910-225257 | 1 | 12706129862752494420 | consolidation |
| P1 | run-20260910-230000 | 1 | 11600467019858866220 | retrenchment |
| P2 | run-20260910-230729 | 1 | 18172784517538253575 | consolidation |

P2 decision: rep 1 (M1 deletion, capital 2.0) kept as the honest first draw over rep 2 (capital 15, same winner, no deletion). Revisit only if all branches crash. Full manifest (all 60 reps with parents and seeds) in `../stage-1-blocks-rerun.json`.

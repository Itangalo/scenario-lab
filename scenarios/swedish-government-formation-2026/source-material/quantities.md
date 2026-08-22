# Quantities: Polling, Seats, and How Far Polls Miss

## Current Polling (August 2026)

Three institutes with field periods ending mid-August 2026 `[source: Swedish
Wikipedia, "Opinionsundersökningar inför riksdagsvalet i Sverige 2026",
retrieved 2026-08-22]`:

| Party | Novus (3–16 Aug) | Verian (3–16 Aug) | Demoskop (29 Jun–10 Aug) | 2022 result |
|-------|-----------------|-------------------|--------------------------|-------------|
| S     | 30.1 | 30.5 | 30.2 | 30.33 |
| SD    | 19.1 | 18.5 | 20.2 | 20.54 |
| M     | 18.3 | 17.3 | 16.8 | 19.10 |
| MP    | 7.9  | 7.7  | 6.6  | 5.08  |
| V     | 7.4  | 7.7  | 6.5  | 6.75  |
| C     | 7.1  | 8.0  | 7.3  | 6.71  |
| KD    | 6.3  | 6.2  | 7.5  | 5.34  |
| L     | 1.9  | 1.9  | 2.4  | 4.61  |

Bloc totals `[source: same]`: left 50.6–53.9, right 43.9–46.9. The bloc gap
ranges from 3.7 to 10.0 points depending on institute — a spread wide enough
that the institutes disagree about how decisive the left's lead is.

Note the disagreement rather than averaging it away: Demoskop shows the
narrowest gap and the strongest SD, Verian the widest gap. Demoskop's field
period is also much longer and starts earlier, which plausibly explains part of
it `[assumption]`.

## The 4% Threshold

A party needs **4%** nationally to enter the riksdag `[model]`. Votes for
parties below it are effectively discarded, so a bloc whose small party falls
short loses that vote share entirely, mechanically transferring seat share to
the other side `[model]`. With L at ~2%, roughly two points of right-bloc
support are currently being wasted.

This is the dominant source of variance in the answer, which is why seats are
drawn per run rather than fixed.

## Seat Allocation

Seats are allocated by the **jämkade uddatalsmetoden** (adjusted odd-numbers /
Sainte-Laguë method) across constituencies, with levelling seats
(utjämningsmandat) correcting for proportionality `[model]`. This is exact
arithmetic and must be computed in the sampler, never by a language model.

**Gap:** the constituency-level detail has not been gathered. A national-level
Sainte-Laguë approximation is accurate to a seat or two and is proposed as
sufficient `[assumption]` — see INDEX.md.

## How Far Polls Miss

From the Gothenburg University Election Research Programme's accuracy study
`[source: "Opinionsundersökningarnas träffsäkerhet inför valen 2002–2022",
Rapport 2022:8, retrieved 2026-08-22]`:

- Average deviation in 2022: **1.1 percentage points per party**
- Range across parties: **0.9 to 1.6 points**
- In the final stretch before election day this fell to **under 0.4 points**
- Systematic pattern: S was underestimated in 266 of 328 measurements

Implications for the sampler `[assumption]`:

- Polls are ~3 weeks out, so the final-stretch figure does not apply. Roughly
  1.0–1.3 points of mean absolute deviation is the right order.
- Mean absolute deviation is about 0.8 sigma for a normal, so sigma is roughly
  1.3–1.6 points for larger parties, scaling down for small ones.
- Errors are **not independent**: shares sum to 100, so draws must be
  correlated, not eight separate normals.
- The documented S underestimation argues for a small positive offset on S
  rather than a symmetric draw.

For L at 1.9–2.4%, reaching 4% is roughly a **three-sigma move** on polling
error alone. See `uncertainties.md` for why the true probability is higher than
that, and still low.

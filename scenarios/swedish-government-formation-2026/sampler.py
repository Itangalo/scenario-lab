#!/usr/bin/env python3
"""Generate starting-state draws for the 2026 Swedish government formation scenario.

Each draw is one plausible election night: vote shares sampled from current
polling plus realistic polling error, the four-percent threshold applied, and
349 seats allocated by the adjusted odd-numbers method (jämkade
uddatalsmetoden). The result is written as a Scenario Lab starting-state JSON
file.

Scenario Lab never runs this script. You run it, deliberately, and then point
`--initial-states` at the directory it produced. Keeping generation outside the
framework is what lets scenario directories stay data rather than code.

Usage:

    # 20 draws from the honest distribution
    python3 sampler.py --count 20 --seed 20260913 --out draws/honest

    # 20 draws conditioned on the Liberals clearing the threshold
    python3 sampler.py --count 20 --seed 20260913 --out draws/l-crosses \\
        --condition l-crosses

The two batches answer different questions and must never be pooled. The honest
batch says what is likely; the conditioned batch says what the Liberals' entry
would mean, and carries no information about how likely that is.
"""

import argparse
import json
import random
import re
from pathlib import Path

# --- Calibration -----------------------------------------------------------
#
# Base shares are the mean of three institutes with field periods ending
# mid-August 2026 (Novus 3-16 Aug, Verian 3-16 Aug, Demoskop 29 Jun-10 Aug).
# Source: sv.wikipedia.org poll aggregation, retrieved 2026-08-22.

BASE_SHARES = {
    "S": 30.27,
    "SD": 19.27,
    "M": 17.47,
    "MP": 7.40,
    "V": 7.20,
    "C": 7.47,
    "KD": 6.67,
    "L": 2.07,
}

PARTY_NAMES = {
    "S": "Socialdemokraterna",
    "M": "Moderaterna",
    "SD": "Sverigedemokraterna",
    "C": "Centerpartiet",
    "V": "Vänsterpartiet",
    "KD": "Kristdemokraterna",
    "MP": "Miljöpartiet",
    "L": "Liberalerna",
}

# 2022 seats, so each draw can say who gained and who lost. That asymmetry is
# what makes the snap-election threat a bargaining instrument rather than a
# uniform pressure: a party that collapsed dreads a fresh election, one that
# surged is tempted by it.
SEATS_2022 = {"S": 107, "SD": 73, "M": 68, "V": 24, "C": 24, "KD": 19, "MP": 18, "L": 16}

LEFT_BLOC = ["S", "V", "MP"]
RIGHT_BLOC = ["M", "SD", "KD", "L"]
# C sits with neither: its double veto is the point of the scenario.

# Polling error. The Gothenburg University accuracy study (Rapport 2022:8)
# found an average deviation of 1.1 percentage points per party in 2022, range
# 0.9-1.6, falling under 0.4 in the final stretch. Polls here are three weeks
# out, so the larger figure applies.
#
# SIGMA_FACTOR is chosen so mean absolute deviation across the eight parties
# lands near 1.0-1.1 points: sigma_i = SIGMA_FACTOR * sqrt(share_i), and mean
# absolute deviation is about 0.8 * sigma for a normal. This scaling (error
# growing with party size) is an assumption, not a published result.
SIGMA_FACTOR = 0.45

# The same study found S underestimated in 266 of 328 measurements. A small
# positive offset rather than a symmetric draw.
S_OFFSET = 0.3

# Tactical vote-lending (stödröstning) between allied parties is a real Swedish
# phenomenon that late polls systematically miss, and is why L took 4.61% in
# 2022 from a weaker polling position. Modelled explicitly because polling error
# alone puts L's threshold crossing at roughly three sigma, which understates it.
STODROSTNING_PROBABILITY = 0.35
STODROSTNING_MEAN = 1.0
STODROSTNING_SD = 0.5

THRESHOLD = 4.0
TOTAL_SEATS = 349
MAJORITY = 175
FIRST_DIVISOR = 1.2  # The "adjusted" in adjusted odd-numbers method.

MAX_CONDITION_ATTEMPTS = 20000

# How far above its polling a party must land to count as "clearly overperforming"
# for the sd-overperforms batch. Three points is roughly what the Sweden Democrats
# did in 2014 (polled around 9-10%, took 12.86%).
#
# Note honestly: the historical record for SD is mixed, not one-directional. They
# overperformed sharply in 2014, underperformed in 2018 (polled ~19-20%, took
# 17.53%) and landed near their polling in 2022. This batch is therefore a
# deliberate "what if", in the same spirit as the l-crosses batch, and not a
# claim that polls systematically understate them.
OVERPERFORMANCE_MARGIN = 3.0

CONDITIONS = {
    "none": lambda shares: True,
    "l-crosses": lambda shares: shares["L"] >= THRESHOLD,
    "sd-overperforms": lambda shares: shares["SD"] >= BASE_SHARES["SD"] + OVERPERFORMANCE_MARGIN,
}


def sample_shares(rng: random.Random) -> dict[str, float]:
    """Draw one set of vote shares from polling plus realistic error."""
    shares = {}
    for party, base in BASE_SHARES.items():
        sigma = SIGMA_FACTOR * (base ** 0.5)
        value = rng.gauss(base, sigma)
        if party == "S":
            value += S_OFFSET
        shares[party] = max(0.1, value)

    # Tactical vote-lending to the Liberals, taken from their closest allies.
    if rng.random() < STODROSTNING_PROBABILITY:
        boost = max(0.0, rng.gauss(STODROSTNING_MEAN, STODROSTNING_SD))
        donors = ["M", "KD"]
        donor_total = sum(shares[d] for d in donors)
        for donor in donors:
            shares[donor] = max(0.1, shares[donor] - boost * shares[donor] / donor_total)
        shares["L"] += boost

    # Shares must sum to 100. Renormalising is also what induces the negative
    # correlation between parties: one party doing well means others do worse.
    total = sum(shares.values())
    return {party: value * 100.0 / total for party, value in shares.items()}


def allocate_seats(shares: dict[str, float]) -> dict[str, int]:
    """Allocate 349 seats by the adjusted odd-numbers method.

    Parties below the four-percent threshold receive no seats and their votes
    are discarded, which is what makes a small party's threshold outcome shift
    seats between the blocs.
    """
    eligible = {p: v for p, v in shares.items() if v >= THRESHOLD}
    if not eligible:
        raise ValueError("No party cleared the threshold; the draw is broken.")

    seats = {party: 0 for party in shares}
    divisors = {party: FIRST_DIVISOR for party in eligible}

    for _ in range(TOTAL_SEATS):
        winner = max(eligible, key=lambda p: shares[p] / divisors[p])
        seats[winner] += 1
        # 1.2, then 3, 5, 7, ...
        divisors[winner] = 2 * seats[winner] + 1

    return seats


def commitments_for(shares: dict[str, float], seats: dict[str, int]) -> list[str]:
    """Derive pre-election commitments consistent with how the night went.

    Drawn together with the result rather than independently: a campaign that
    produced an unusually strong result for a party is also a campaign in which
    different things were said out loud. The conditioning rules are plausible
    rather than empirical.
    """
    lines = [
        "The Centre Party repeated throughout the campaign that it will not seek "
        "organised cooperation with the Sweden Democrats, and will not support any "
        "government containing the Left Party.",
        "The Social Democrats ruled out cooperation with the Sweden Democrats, and "
        "declined to name any constellation they would pursue.",
    ]

    if seats["SD"] > seats["M"]:
        lines.append(
            "The Sweden Democrats finished ahead of the Moderates and spent the "
            "closing week saying plainly that the largest party on the right expects "
            "cabinet seats this time. That demand is now on the record."
        )
    elif seats["M"] > seats["SD"]:
        lines.append(
            "The Moderates held their position as the largest party on the right, "
            "which strengthens Ulf Kristersson's claim to lead any right-leaning "
            "government and weakens the Sweden Democrats' case for portfolios."
        )

    if shares["L"] >= THRESHOLD:
        lines.append(
            "The Liberals cleared the threshold against expectations, and are openly "
            "crediting tactical vote-lending from Moderate voters. They argue that "
            "they earned their place by making the last government work, and have "
            "restated their resistance to Sweden Democrat cabinet seats."
        )
    else:
        lines.append(
            "The Liberals failed to clear the four-percent threshold and are out of "
            "the chamber. Roughly two points of right-leaning vote were discarded "
            "with them. Simona Mohamsson's position as leader is in question, and "
            "the party is arguing publicly about whether the Moderates abandoned it."
        )

    left_seats = sum(seats[p] for p in LEFT_BLOC)
    if left_seats >= MAJORITY:
        lines.append(
            "The left bloc reached a majority on its own, which makes the Centre "
            "Party's veto on the Left Party the only obstacle to a straightforward "
            "Social Democrat-led government."
        )

    if seats["C"] >= 28:
        lines.append(
            "The Centre Party had a strong night and Elisabeth Thand Ringqvist has "
            "been emphatic that the result is a mandate for both of the party's "
            "stated conditions."
        )

    return lines


def render_context(shares: dict[str, float], seats: dict[str, int]) -> str:
    """Render the election result as the markdown the actors will read as fact."""
    order = sorted(seats, key=lambda p: -seats[p])

    rows = []
    for party in order:
        status = "—" if shares[party] < THRESHOLD else str(seats[party])
        note = " (below threshold)" if shares[party] < THRESHOLD else ""
        rows.append(f"| {PARTY_NAMES[party]} ({party}) | {shares[party]:.1f}% | {status}{note} |")

    left_seats = sum(seats[p] for p in LEFT_BLOC)
    right_seats = sum(seats[p] for p in RIGHT_BLOC)
    c_seats = seats["C"]

    in_chamber = [p for p in order if shares[p] >= THRESHOLD]
    out = [p for p in order if shares[p] < THRESHOLD]

    lines = [
        "## The Election Result",
        "",
        "The final count from 13 September 2026. These figures are settled.",
        "",
        "| Party | Vote share | Seats |",
        "|-------|-----------|-------|",
        *rows,
        "",
        f"Parties in the chamber: {', '.join(in_chamber)}.",
    ]
    # Stated as its own sentence, in both directions. Everything else in this
    # scenario -- the polling, the background, the actor file -- points to the
    # Liberals being out, and a single row in a table does not override that
    # prior: runs drawn with L holding 17 seats still had the Liberals acting
    # "despite lacking parliamentary representation".
    if shares["L"] >= THRESHOLD:
        lines += [
            "",
            f"**The Liberals ARE in the chamber.** They cleared the four-percent "
            f"threshold with {shares['L']:.1f}% and hold {seats['L']} seats. They vote, "
            f"they count toward the 175 needed to block a government, and they can be "
            f"given cabinet posts. Any narrative describing them as outside parliament, "
            f"as lacking representation, or as commentators without votes is wrong.",
        ]
    else:
        lines += [
            "",
            f"**The Liberals are NOT in the chamber.** They took {shares['L']:.1f}%, below "
            f"the four-percent threshold, and hold no seats. They cannot vote, cannot be "
            f"counted toward 175, and cannot receive cabinet posts.",
        ]
    if out:
        lines.append(f"Below the four-percent threshold and out of the chamber: {', '.join(out)}.")
    lines += [
        "",
        f"Left bloc (S, V, MP): **{left_seats}** seats. "
        f"Right bloc (M, SD, KD{', L' if shares['L'] >= THRESHOLD else ''}): **{right_seats}** seats. "
        f"The Centre Party holds **{c_seats}** and sits with neither.",
        "",
        f"An absolute majority is {MAJORITY} of {TOTAL_SEATS}. "
        + (
            f"The left bloc has one on its own. "
            if left_seats >= MAJORITY
            else f"The left bloc is {MAJORITY - left_seats} short of one. "
        )
        + (
            "The right bloc has one on its own."
            if right_seats >= MAJORITY
            else f"The right bloc is {MAJORITY - right_seats} short of one."
        ),
        "",
        "## What the Night Meant for Each Party",
        "",
        "Change against 2022, which is what each party will weigh when judging "
        "whether an extraordinary election would help or hurt it. Note that an "
        "extra election does not start a new four-year term: those elected serve "
        "only until the next ordinary election, so even a party riding high wins "
        "a shortened mandate.",
        "",
        "| Party | Seats | 2022 | Change |",
        "|-------|-------|------|--------|",
    ]
    for party in order:
        held = seats[party]
        was = SEATS_2022[party]
        delta = held - was
        arrow = f"{delta:+d}" if delta else "±0"
        lines.append(f"| {party} | {held} | {was} | {arrow} |")

    lines += [
        "",
        "## What Was Said Before the Vote",
        "",
    ]
    lines += [f"- {line}" for line in commitments_for(shares, seats)]

    return "\n".join(lines) + "\n"


def build_draw(rng: random.Random, batch: str, condition: str, seed: int, index: int) -> dict:
    """Produce one starting-state draw."""
    accepts = CONDITIONS[condition]
    for _ in range(MAX_CONDITION_ATTEMPTS):
        shares = sample_shares(rng)
        if accepts(shares):
            break
    else:
        raise RuntimeError(
            f"Could not draw a world satisfying condition '{condition}' in "
            f"{MAX_CONDITION_ATTEMPTS} attempts. Check the calibration."
        )

    seats = allocate_seats(shares)
    assert sum(seats.values()) == TOTAL_SEATS, "Seat allocation must sum to 349"

    left_seats = sum(seats[p] for p in LEFT_BLOC)
    right_seats = sum(seats[p] for p in RIGHT_BLOC)

    # notes is greppable on purpose: it is how runs get grouped afterwards.
    note_fields = [
        f"batch={batch}",
        f"seed={seed}",
        f"draw={index:03d}",
        f"l_in_parliament={'true' if shares['L'] >= THRESHOLD else 'false'}",
        f"left_seats={left_seats}",
        f"right_seats={right_seats}",
        f"c_seats={seats['C']}",
        f"sd_share={shares['SD']:.2f}",
        *(f"{p}={seats[p]}" for p in ["S", "SD", "M", "C", "V", "KD", "MP", "L"]),
    ]

    return {
        # Metric starting values are deliberately left alone: on election night
        # every constellation is unresolved, and letting the model read the
        # arithmetic itself keeps the reasoning in the prompts where it belongs.
        "metrics": {},
        "context": render_context(shares, seats),
        "notes": "; ".join(note_fields),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--count", type=int, default=20, help="Number of draws to generate")
    parser.add_argument("--seed", type=int, required=True, help="Base seed, recorded in every draw")
    parser.add_argument("--out", type=Path, required=True, help="Directory to write draws into")
    parser.add_argument(
        "--condition",
        choices=sorted(CONDITIONS),
        default="none",
        help=(
            "Condition the draws. 'l-crosses' keeps only worlds where the Liberals "
            "clear 4%%; 'sd-overperforms' keeps worlds where the Sweden Democrats land "
            "at least %.1f points above their polling. Conditioned batches say what a "
            "world would mean, never how likely it is." % OVERPERFORMANCE_MARGIN
        ),
    )
    args = parser.parse_args()

    if args.count < 1:
        parser.error("--count must be at least 1")

    batch = "honest" if args.condition == "none" else args.condition
    args.out.mkdir(parents=True, exist_ok=True)

    rng = random.Random(f"{args.seed}:{batch}")
    crossings = 0
    mean_sd = 0.0

    for index in range(1, args.count + 1):
        draw = build_draw(rng, batch, args.condition, args.seed, index)
        if "l_in_parliament=true" in draw["notes"]:
            crossings += 1
        mean_sd += float(re.search(r"sd_share=([\d.]+)", draw["notes"]).group(1))
        path = args.out / f"draw-{index:03d}.json"
        path.write_text(json.dumps(draw, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    print(f"Wrote {args.count} draw(s) to {args.out}")
    print(f"Batch: {batch}, base seed {args.seed}")
    print(f"Liberals in parliament: {crossings}/{args.count}")
    print(f"Mean SD share: {mean_sd / args.count:.1f}% (polling: {BASE_SHARES['SD']:.1f}%)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

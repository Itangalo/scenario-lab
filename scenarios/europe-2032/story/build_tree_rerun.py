#!/usr/bin/env python3
"""Generate story/tree.json for the Muse Spark + store rerun (2026-09-10/11).

Inputs (all committed): stage-1/2/3-blocks-rerun.json manifests (run, seed,
parent per rep), PATHS locks (rep 1 throughout, no promotions), pool
directories (samples), turn-01 option files. Editorial content below --
stances, standings, support counts, choice notes -- is the recorded human
record of what the pools showed and what was picked; measure/category/
finishes_turn are parsed from the sample files themselves, never retyped.

Usage: python scenarios/europe-2032/story/build_tree_rerun.py [--check]
--check verifies every referenced run dir, option file, pool and sample
exists, and writes nothing.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

STORY = Path(__file__).resolve().parent
SCENARIO = STORY.parent
RUNS = SCENARIO / "runs"

# --- path runs and seeds (rep 1 per block; see stage-N-PATHS.md) ---------------
STAGE1 = {
    "A1": ("run-20260910-223510", 16131371758201131071, "run-20260910-223233", "turn-01/option-02-1.md"),
    "A2": ("run-20260910-224240", 3275500770907618172, "run-20260910-223233-05", "turn-01/option-02-2.md"),
    "V1": ("run-20260910-224841-01", 16469017358909379730, "run-20260910-223233-01", "turn-01/option-02-1.md"),
    "V2": ("run-20260910-225257", 12706129862752494420, "run-20260910-223233-02", "turn-01/option-02-2.md"),
    "P1": ("run-20260910-230000", 11600467019858866220, "run-20260910-223233-04", "turn-01/option-02-1.md"),
    "P2": ("run-20260910-230729", 18172784517538253575, "run-20260910-223233-03", "turn-01/option-02-2.md"),
}

STAGE2 = {  # block: (run, seed, parent, fixture, option)
    "A11": ("run-20260911-002005", 14477735025383896940, "run-20260910-223510", "run-20260911-000401-04", "pool-06-A1-20260911/sample-01.md"),
    "A12": ("run-20260911-003254", None, "run-20260910-223510", "run-20260911-000401-04", "pool-06-A1-20260911/sample-02.md"),
    "A21": ("run-20260911-003912", None, "run-20260910-224240", "run-20260911-000401-03", "pool-06-A2-20260911/sample-09.md"),
    "A22": ("run-20260911-004522", None, "run-20260910-224240", "run-20260911-000401-03", "pool-06-A2-20260911-ext/sample-05.md"),
    "V11": ("run-20260911-005258", None, "run-20260910-224841-01", "run-20260911-001039", "pool-06-V1-20260911/sample-03.md"),
    "V12": ("run-20260911-005959", None, "run-20260910-224841-01", "run-20260911-001039", "pool-06-V1-20260911/sample-09.md"),
    "V21": ("run-20260911-010919", None, "run-20260910-225257", "run-20260911-000401-01", "pool-06-V2-20260911/sample-02.md"),
    "V22": ("run-20260911-011551", None, "run-20260910-225257", "run-20260911-000401-01", "pool-06-V2-20260911/sample-04.md"),
    "P11": ("run-20260911-012117", None, "run-20260910-230000", "run-20260911-000401-02", "pool-06-P1-20260911/sample-01.md"),
    "P12": ("run-20260911-012701", None, "run-20260910-230000", "run-20260911-000401-02", "pool-06-P1-20260911/sample-02.md"),
    "P21": ("run-20260911-013336", None, "run-20260910-230729", "run-20260911-001039-01", "pool-06-P2-20260911/sample-01.md"),
    "P22": ("run-20260911-013951", None, "run-20260910-230729", "run-20260911-001039-01", "pool-06-P2-20260911/sample-02.md"),
}

# --- turn-1 and turn-6 choices (option node, sample, stance, standing, support)
T1_CHOICE = {
    "pool": "turn-01/pool-20260910", "draws": 30, "split": "emergent",
    "note": "Straight picks from the 30-draw store-branch pool (cat5 14 / cat6 16; no build draws at all). No synthesis. Build lives on in the turn-0 seeded programmes, so the choice is what new direction to add: harden first or evaluate first. Turn-1 resolution differs per arm (ai_capability 55.0/54.0/53.5), so it is not shown before the choice.",
    "options": [
        {"node": "option-02-1", "leads": ["A1", "V1", "P1"], "sample": "sample-24",
         "stance": "shield", "standing": "plurality category", "support": "cat6, 16/30"},
        {"node": "option-02-2", "leads": ["A2", "V2", "P2"], "sample": "sample-06",
         "stance": "know", "standing": "second category", "support": "cat5, 14/30"},
    ],
}

T6_CHOICES = {
    # after_block: (pool, draws, note, [(node, leads, sample, stance, standing, support)])
    "A1": ("pool-06-A1-20260911", 10, "Embodied deployment meets the Alliance window: contain the robots or buy the access.",
           [("option-06-A11", "A11", "sample-01", "buy access", "minority", "cat8, 3/10"),
            ("option-06-A12", "A12", "sample-02", "contain", "majority", "cat6, 6/10")]),
    "A2": ("pool-06-A2-20260911", 20, "A single mild event; N=10 converged on triage holds, extended with 10 more draws for the wait minority (pool-06-A2-20260911-ext).",
           [("option-06-A21", "A21", "sample-09", "hold deployment", "majority", "cat1, 18/20"),
            ("option-06-A22", "A22", "pool-06-A2-20260911-ext/sample-05", "wait", "minority", "no new measure, 2/20")]),
    "V1": ("pool-06-V1-20260911", 10, "Jump plus opacity plus open release plus defection: know the new systems or patch against them.",
           [("option-06-V11", "V11", "sample-03", "assure", "minority", "cat5, 2/10"),
            ("option-06-V12", "V12", "sample-09", "patch", "majority", "cat6, 5/10")]),
    "V2": ("pool-06-V2-20260911", 10, "Cyberattack plus defection at capital 4: repair visibly or retrench to the compact.",
           [("option-06-V21", "V21", "sample-02", "repair", "minority", "cat6, 3/10"),
            ("option-06-V22", "V22", "sample-04", "retrench", "majority", "no new measure, 7/10 (4 with deletes)")]),
    "P1": ("pool-06-P1-20260911", 10, "Cutoff plus loss-of-control: build the switch or triage on what exists.",
           [("option-06-P11", "P11", "sample-01", "switch", "majority", "cat6, 8/10"),
            ("option-06-P12", "P12", "sample-02", "triage", "minority", "no new measure, 2/10")]),
    "P2": ("pool-06-P2-20260911", 10, "Unanimous no-new-measure at capital 2; the axis is the mandate itself.",
           [("option-06-P21", "P21", "sample-01", "redirect mandate", "minority", "commitment modify, 3/10"),
            ("option-06-P22", "P22", "sample-02", "hold mandate", "majority", "no changes, 7/10")]),
}

# --- Stage-3 blocks: block -> Stage-2 parent (run/fixture/option per pick) -----
STAGE3_PARENTS = {
    "A111": "A11", "A112": "A11", "A121": "A12", "A122": "A12",
    "A211": "A21", "A212": "A21", "A221": "A22", "A222": "A22",
    "V111": "V11", "V112": "V11", "V121": "V12", "V122": "V12",
    "V211": "V21", "V212": "V21", "V221": "V22", "V222": "V22",
    "P111": "P11", "P112": "P11", "P121": "P12", "P122": "P12",
    "P211": "P21", "P212": "P21", "P221": "P22", "P222": "P22",
}

T10_CHOICES = {
    "A11": ("pool-10-A11-20260911", 10, "War: shield the infrastructure or wait out the exchange.",
            [("option-10-A111", "A111", "sample-01", "shield", "majority", "wartime shields, 9/10"),
             ("option-10-A112", "A112", "sample-06", "wait", "minority", "no new measure, 1/10")]),
    "A12": ("pool-10-A12-20260911", 10, "Scandal plus breakthroughs: enforce redress or let the Corps land.",
            [("option-10-A121", "A121", "sample-01", "redress", "majority", "redress registries, 7/10"),
             ("option-10-A122", "A122", "sample-04", "wait", "minority", "no new measure, 3/10")]),
    "A21": ("pool-10-A21-20260911", 20, "War: all 20 draws (pool extended) build shelters; the choice is what leads -- shelter-first or care-first.",
            [("option-10-A211", "A211", "sample-06", "shelter-first", "priority axis", "shelters, 12/20 self-priority"),
             ("option-10-A212", "A212", "sample-02", "care-first", "priority axis", "shelters, 8/20 bio-network priority")]),
    "A22": ("pool-10-A22-20260911", 10, "Rogue agent plus agreement: livelihoods or containment.",
            [("option-10-A221", "A221", "sample-01", "livelihoods", "half", "cat7, 5/10"),
             ("option-10-A222", "A222", "sample-02", "containment", "half", "cat6, 5/10")]),
    "V11": ("pool-10-V11-20260911", 10, "Cyber plus loss-of-control: lock down or finish the fallback.",
            [("option-10-V111", "V111", "sample-05", "lockdown", "majority", "lockdowns, 9/10"),
             ("option-10-V112", "V112", "sample-01", "wait", "minority", "no new measure, 1/10")]),
    "V12": ("pool-10-V12-20260911", 10, "Quiet turn, single invitation: which allied structure to join.",
            [("option-10-V121", "V121", "sample-01", "threat response", "minority", "accessions, 3/10"),
             ("option-10-V122", "V122", "sample-02", "cyber command", "majority", "accessions, 7/10")]),
    "V21": ("pool-10-V21-20260911", 10, "Bio plus cutoff: fallback as tools or as staffed corps.",
            [("option-10-V211", "V211", "sample-01", "stack", "majority", "fallback stacks, 8/10"),
             ("option-10-V212", "V212", "sample-06", "corps", "minority", "bio corps, 2/10")]),
    "V22": ("pool-10-V22-20260911", 10, "Cyber sweep plus displacement: jobs or recovery.",
            [("option-10-V221", "V221", "sample-01", "jobs", "half", "transition income, 5/10"),
             ("option-10-V222", "V222", "sample-03", "recovery", "half", "cyber recovery, 5/10")]),
    "P11": ("pool-10-P11-20260911", 10, "Bio release: quarantine-and-manual vs surge-and-treat.",
            [("option-10-P111", "P111", "sample-04", "cordons", "strand", "triage cordons within unanimous containment"),
             ("option-10-P112", "P112", "sample-10", "surge", "strand", "treatment surge within unanimous containment")]),
    "P12": ("pool-10-P12-20260911", 10, "Defence gain plus bio signal: push the advantage or fund absorption.",
            [("option-10-P121", "P121", "sample-01", "sprint", "majority", "patch/sentinel, 8/10"),
             ("option-10-P122", "P122", "sample-06", "jobs", "minority", "transition guarantee, 2/10")]),
    "P21": ("pool-10-P21-20260911", 10, "Capital zero: two draws build shields, eight hold.",
            [("option-10-P211", "P211", "sample-02", "shield", "minority", "adds, 2/10"),
             ("option-10-P212", "P212", "sample-01", "hold", "majority", "no new measure, 8/10")]),
    "P22": ("pool-10-P22-20260911", 10, "Sabotage plus collapse: claim the dividend or guard the fallback.",
            [("option-10-P221", "P221", "sample-08", "showcase", "minority", "adds, 2/10"),
             ("option-10-P222", "P222", "sample-01", "hold", "majority", "no new measure, 8/10")]),
}


def sample_measure(pool: str, sample: str) -> tuple[str | None, int | None, int | None]:
    """Measure name/category/finish from the sample's store add, else Nones."""
    text = (STORY / pool / f"{sample}.md").read_text(encoding="utf-8")
    m = re.search(r'"op":\s*"add".*?"name":\s*"([^"]+)".*?"category":\s*(\d+).*?"finish_turn":\s*(\d+)',
                  text, re.S)
    if not m:
        return None, None, None
    return m.group(1), int(m.group(2)), int(m.group(3))


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--check", action="store_true", help="verify, write nothing")
    args = ap.parse_args()

    old = json.loads((STORY / "tree.json").read_text(encoding="utf-8"))
    problems: list[str] = []

    def need_dir(path: str) -> None:
        if not (RUNS / path).is_dir():
            problems.append(f"missing run dir: {path}")

    def need_file(path: str) -> None:
        if not (STORY / path).is_file():
            problems.append(f"missing file: {path}")

    # --- opening ------------------------------------------------------------
    base_seeds = {
        ("acceleration", "option-02-1.md"): 11393420347447850519,
        ("acceleration", "option-02-2.md"): 18390941728457876666,
        ("verification-bounded", "option-02-1.md"): 3258927143480286315,
        ("verification-bounded", "option-02-2.md"): 1519680248815227832,
        ("plateau", "option-02-1.md"): 8278137031818086528,
        ("plateau", "option-02-2.md"): 562049392789732589,
    }
    base_dirs = {
        ("acceleration", "option-02-1.md"): "run-20260910-223233",
        ("acceleration", "option-02-2.md"): "run-20260910-223233-05",
        ("verification-bounded", "option-02-1.md"): "run-20260910-223233-01",
        ("verification-bounded", "option-02-2.md"): "run-20260910-223233-02",
        ("plateau", "option-02-1.md"): "run-20260910-223233-04",
        ("plateau", "option-02-2.md"): "run-20260910-223233-03",
    }
    pin_runs = {}
    for (arm, opt), seed in base_seeds.items():
        key = {"option-02-1.md": "o1", "option-02-2.md": "o2"}[opt]
        pin_runs[f"{arm[0].upper()}-{key}"] = {"dir": base_dirs[(arm, opt)], "seed": seed}
    opening = {
        "node": "turn-01", "turn": 1, "period": "H2 2026",
        "pinned_event": "cyber_test_shot", "pin_runs": pin_runs,
        "options": [
            {"node": "option-02-1", "file": "turn-01/option-02-1.md",
             "pool": T1_CHOICE["pool"], "sample": "sample-24",
             "leads_to": ["A1", "V1", "P1"]},
            {"node": "option-02-2", "file": "turn-01/option-02-2.md",
             "pool": T1_CHOICE["pool"], "sample": "sample-06",
             "leads_to": ["A2", "V2", "P2"]},
        ],
    }

    # --- blocks ---------------------------------------------------------------
    s2 = {t["dir"]: t for t in
          json.loads((STORY / "stage-2-blocks-rerun.json").read_text())}
    s3 = {t["dir"]: t for t in
          json.loads((STORY / "stage-3-blocks-rerun.json").read_text())}
    seed_of = {}
    for t in json.loads((STORY / "stage-1-blocks-rerun.json").read_text()):
        seed_of[(t["path"], t["rep"])] = (t["dir"], t["seed"])
    for t in json.loads((STORY / "stage-2-blocks-rerun.json").read_text()):
        seed_of[(t["path"], t["rep"])] = (t["dir"], t["seed"])
    for t in json.loads((STORY / "stage-3-blocks-rerun.json").read_text()):
        seed_of[(t["path"], t["rep"])] = (t["dir"], t["seed"])

    blocks: list[dict] = []
    for branch, (run, seed, parent, opt) in STAGE1.items():
        blocks.append({"block": branch, "arm": branch[0], "stage": 1,
                       "turns": [2, 3, 4, 5], "parent_block": None,
                       "run": run, "seed": seed, "branch_from_run": parent,
                       "branch_turn": 1, "pinned_turn": None,
                       "option_node": "option-02-1" if opt.endswith("1.md") else "option-02-2",
                       "option_file": f"turn-01/{opt.split('/')[-1]}",
                       "path_rep": 1, "promotion_reason": None})
    for branch, (run, _s, parent, fixture, opt) in STAGE2.items():
        _d, seed = seed_of.get((branch, 1), (run, None))
        assert _d == run, f"manifest mismatch {branch}"
        blocks.append({"block": branch, "arm": branch[0], "stage": 2,
                       "turns": [6, 7, 8, 9], "parent_block": branch[:2],
                       "run": run, "seed": seed, "branch_from_run": parent,
                       "branch_turn": 5, "pinned_turn": 6,
                       "option_node": f"option-06-{branch}",
                       "option_file": opt, "path_rep": 1,
                       "promotion_reason": None})
    s3paths = {t["path"]: (t["dir"], t["seed"]) for t in
               json.loads((STORY / "stage-3-blocks-rerun.json").read_text())
               if t["rep"] == 1}
    s2parents = {"A11": "run-20260911-002005", "A12": "run-20260911-003254",
                 "A21": "run-20260911-003912", "A22": "run-20260911-004522",
                 "V11": "run-20260911-005258", "V12": "run-20260911-005959",
                 "V21": "run-20260911-010919", "V22": "run-20260911-011551",
                 "P11": "run-20260911-012117", "P12": "run-20260911-012701",
                 "P21": "run-20260911-013336", "P22": "run-20260911-013951"}
    s3fixtures = {"A11": "run-20260911-014820-07", "A12": "run-20260911-014820-04",
                  "A21": "run-20260911-014820-01", "A22": "run-20260911-014820-08",
                  "V11": "run-20260911-014820-09", "V12": "run-20260911-014819",
                  "V21": "run-20260911-014820-02", "V22": "run-20260911-014820-05",
                  "P11": "run-20260911-014820-03", "P12": "run-20260911-014846",
                  "P21": "run-20260911-014820", "P22": "run-20260911-014820-06"}
    for block3, parent2 in STAGE3_PARENTS.items():
        run, seed = s3paths[block3]
        entry = [o for o in T10_CHOICES[parent2][3] if o[1] == block3][0]
        opt_file = f"{T10_CHOICES[parent2][0]}/{entry[2]}.md"
        fixture = s3fixtures[parent2]
        blocks.append({"block": block3, "arm": block3[0], "stage": 3,
                       "turns": [10, 11, 12, 13], "parent_block": parent2,
                       "run": run, "seed": seed,
                       "branch_from_run": s2parents[parent2],
                       "branch_turn": 9, "pinned_turn": 10,
                       "option_node": f"option-10-{block3}",
                       "option_file": opt_file, "path_rep": 1,
                       "promotion_reason": None,
                       "pinned_fixture": fixture})

    # --- choices ----------------------------------------------------------------
    choices: list[dict] = []
    t1_opts = []
    for o in T1_CHOICE["options"]:
        sample = o["sample"]
        measure, cat, fin = sample_measure(T1_CHOICE["pool"], sample)
        t1_opts.append({"node": o["node"], "leads_to_block": o["leads"],
                        "sample": sample, "stance": o["stance"],
                        "standing": o["standing"], "support": o["support"],
                        "measure": measure, "category": cat,
                        "finishes_turn": fin})
    choices.append({"after_block": "turn-01", "choice_turn": 2,
                    "pool": T1_CHOICE["pool"], "draws": T1_CHOICE["draws"],
                    "split": T1_CHOICE["split"], "note": T1_CHOICE["note"],
                    "options": t1_opts})
    for after, (pool, draws, note, opts) in T6_CHOICES.items():
        out = []
        for node, leads, sample, stance, standing, support in opts:
            samp = sample.split("/")[-1]
            src_pool = pool if "/" not in sample else sample.rsplit("/", 1)[0]
            if "/" in sample:
                src_pool = {"pool-06-A2-20260911-ext/sample-05":
                            "pool-06-A2-20260911-ext"}[sample]
            measure, cat, fin = sample_measure(src_pool, samp)
            out.append({"node": node, "leads_to_block": leads,
                        "sample": samp, "stance": stance, "standing": standing,
                        "support": support, "measure": measure, "category": cat,
                        "finishes_turn": fin})
        choices.append({"after_block": after, "choice_turn": 6, "pool": pool,
                        "draws": draws, "split": "emergent", "note": note,
                        "options": out})
    for after, (pool, draws, note, opts) in T10_CHOICES.items():
        out = []
        for node, leads, sample, stance, standing, support in opts:
            measure, cat, fin = sample_measure(pool, sample)
            out.append({"node": node, "leads_to_block": leads,
                        "sample": sample, "stance": stance, "standing": standing,
                        "support": support, "measure": measure, "category": cat,
                        "finishes_turn": fin})
        choices.append({"after_block": after, "choice_turn": 10, "pool": pool,
                        "draws": draws, "split": "emergent", "note": note,
                        "options": out})

    tree = {"scenario": "europe-2032",
            "note": "Rerun source of truth (Muse Spark + store branch, "
                    "2026-09-10/11). 42 path blocks, all rep 1, no promotions. "
                    "Generated by story/build_tree_rerun.py from the rerun "
                    "manifests; verified against every run's config.json.",
            "arms": old["arms"], "turn_periods": old["turn_periods"],
            "opening": opening, "blocks": blocks, "choices": choices}

    # --- verify -------------------------------------------------------------------
    for b in blocks:
        need_dir(b["run"])
        need_file(b["option_file"])
    for o in opening["options"]:
        need_file(o["file"])
    for c in choices:
        for o in c["options"]:
            pool = c["pool"] if c["after_block"] != "turn-01" else T1_CHOICE["pool"]
            samp = o["sample"]
            if c["after_block"] == "A2" and o["node"] == "option-06-A22":
                pool = "pool-06-A2-20260911-ext"
            need_file(f"{pool}/{samp}.md")
    # seeds match the manifests' record
    for (path, rep), (d, s) in seed_of.items():
        hit = [b for b in blocks if b["block"] == path]
        if rep == 1 and hit and hit[0]["seed"] != s:
            problems.append(f"seed mismatch {path}: tree {hit[0]['seed']} vs manifest {s}")

    if problems:
        print("PROBLEMS:")
        for p in problems:
            print(" ", p)
        return 1
    if args.check:
        print(f"tree verifies: {len(blocks)} blocks, {len(choices)} choices, "
              f"{sum(len(c['options']) for c in choices)} options")
        return 0
    (STORY / "tree.json").write_text(
        json.dumps(tree, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"wrote tree.json: {len(blocks)} blocks, {len(choices)} choices")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

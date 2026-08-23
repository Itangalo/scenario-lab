#!/usr/bin/env python3
"""Compare rulings across interrogation tracks.

Compares verdicts, not prose: two tracks routinely agree on wording while
diverging on interpretation, and only the verdict shows it.
"""

import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent


def load(path: Path) -> dict:
    data = json.loads(path.read_text(encoding="utf-8"))
    out = {}
    for cid, block in data.items():
        for r in block.get("parsed") or []:
            out[r["id"]] = r
    return out


def main() -> int:
    files = sorted(HERE.glob("rulings-*.json"))
    if len(files) < 2:
        print("need at least two tracks", file=sys.stderr)
        return 1
    tracks = {f.stem.replace("rulings-", ""): load(f) for f in files}
    names = list(tracks)
    ids = sorted(set().union(*(set(t) for t in tracks.values())))

    agree = diverge = missing = 0
    for cid in ids:
        verdicts = [tracks[n].get(cid, {}).get("verdict", "-") for n in names]
        if "-" in verdicts:
            missing += 1
            mark = "MISSING"
        elif len(set(verdicts)) == 1:
            agree += 1
            mark = "agree" if verdicts[0] != "UNCLEAR" else "agree(UNCLEAR=open)"
        else:
            diverge += 1
            mark = "*** DIVERGE ***"
        print(f"{cid:6} {' / '.join(v[:7] for v in verdicts):20} {mark}")
        if mark.startswith("***"):
            for n in names:
                r = tracks[n].get(cid, {})
                print(f"       {n}: {r.get('verdict')} - {r.get('reason','')}")

    print(f"\ntracks: {', '.join(names)}")
    print(f"agree {agree}   diverge {diverge}   missing {missing}")
    return 0


if __name__ == "__main__":
    sys.exit(main())

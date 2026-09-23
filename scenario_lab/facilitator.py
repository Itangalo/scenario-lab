"""Facilitator web UI for live workshop games (stdlib only, no new dependencies).

Runs a small localhost server so a workshop leader never has to touch the
terminal: pick a scenario, prepare the turn's menus, collect the teams' picks
in the browser, resolve, and print the handouts – all from one page.

Thin layer only: every game action delegates to ``live.py`` (``run_menu_turn``,
``run_resolve_turn``, ``read_menus`` …), so a GUI-driven game produces exactly
the same artifacts as the CLI flow and the two stay interoperable on the same
run directories. No prompt, rule, or persistence logic lives here.

Usage:
    python -m scenario_lab.facilitator [--port 8000] [--scenarios scenarios]
"""

from __future__ import annotations

import argparse
import itertools
import json
import random
import threading
import urllib.parse
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
from typing import Any, Callable, Optional

from .actor_sampling import is_run_dir
from .live import (
    LiveError,
    completed_turns,
    find_live_runs,
    find_live_scenarios,
    newest_pending_turn,
    open_live_state,
    pending_live_turns,
    read_menus,
    read_run_seed,
    resolve_pick,
    run_menu_turn,
    run_resolve_turn,
    turn_numbers,
)

# Test seam, mirroring the ``llm_client`` parameters on the CLI handlers: a
# real server leaves this None (routers are built from scenario config) while
# tests point it at a fake client to avoid network calls.
LLM_CLIENT: Any = None


# ---------------------------------------------------------------------------
# Pure helpers (no HTTP): game inspection and actions, unit-testable directly.
# ---------------------------------------------------------------------------


def scenarios_root(explicit: Optional[Path] = None) -> Path:
    """Directory holding scenario directories (default: ./scenarios)."""
    return Path(explicit) if explicit is not None else Path.cwd() / "scenarios"


def list_scenarios(root: Optional[Path] = None) -> list[dict[str, str]]:
    """Live-ready scenarios: id is the directory path, name is display text."""
    found = find_live_scenarios(scenarios_root(root))
    return [{"id": str(s.path), "name": s.name} for s in found]


def list_runs(scenario_path: str) -> list[dict[str, Any]]:
    """Existing live games for a scenario, newest first."""
    runs = find_live_runs(Path(scenario_path))
    return [
        {
            "run_dir": str(r.run_dir),
            "name": r.run_dir.name,
            "completed_turns": r.completed_turns,
            "pending_turn": r.pending_turn,
        }
        for r in runs
    ]


def game_state(run_dir: str) -> dict[str, Any]:
    """Everything the frontend needs to render a game: actors and turn flags."""
    run_path = Path(run_dir)
    scenario, _ = open_live_state(run_path, 1)
    pending = pending_live_turns(run_path)
    turns = []
    for n in turn_numbers(run_path):
        turn_dir = run_path / f"turn-{n:02d}"
        resolved = (turn_dir / "2-actors").is_dir() and (turn_dir / "4-metrics.json").exists()
        turns.append(
            {
                "turn": n,
                "has_menus": (turn_dir / "live" / "menu.json").exists(),
                "resolved": resolved,
            }
        )
    return {
        "run_dir": str(run_path),
        "name": run_path.name,
        "scenario_name": scenario.config.name,
        "max_turns": scenario.config.max_turns,
        "actors": [{"id": aid, "name": a.name} for aid, a in scenario.actors.items()],
        "turns": turns,
        "pending_turn": newest_pending_turn(run_path),
        "completed_turns": completed_turns(run_path),
    }


def turn_payload(run_dir: str, turn: int) -> dict[str, Any]:
    """Briefing markdown plus structured menus for one turn (menus may be None)."""
    run_path = Path(run_dir)
    turn_dir = run_path / f"turn-{turn:02d}"
    briefing_path = turn_dir / "live" / "briefing.md"
    briefing = briefing_path.read_text(encoding="utf-8") if briefing_path.exists() else ""
    try:
        menus = read_menus(run_path, turn)
    except LiveError:
        menus = None
    resolved = (turn_dir / "2-actors").is_dir() and (turn_dir / "4-metrics.json").exists()
    return {
        "run_dir": str(run_path),
        "turn": turn,
        "briefing_md": briefing,
        "resolved": resolved,
        "menus": (
            {
                aid: {
                    "actor_id": m.actor_id,
                    "actor_name": m.actor_name,
                    "options": [
                        {"index": o.index, "title": o.title, "text": o.text}
                        for o in m.options
                    ],
                }
                for aid, m in menus.items()
            }
            if menus is not None
            else None
        ),
    }


def validate_picks(run_dir: str, turn: int, picks: dict[str, str]) -> dict[str, str]:
    """Check picks against the recorded menus; raises LiveError with a reason."""
    menus = read_menus(Path(run_dir), turn)
    actor_ids = list(menus)
    unknown = sorted(set(picks) - set(actor_ids))
    if unknown:
        raise LiveError(
            f"Unknown actor(s): {', '.join(unknown)} "
            f"(this run has: {', '.join(actor_ids)})"
        )
    missing = [aid for aid in actor_ids if aid not in picks or not str(picks[aid]).strip()]
    if missing:
        raise LiveError(f"Missing picks for: {', '.join(missing)}.")
    cleaned: dict[str, str] = {}
    for aid in actor_ids:
        spec = str(picks[aid]).strip()
        resolve_pick(spec, menus[aid])  # raises on out-of-range / multi-pick
        cleaned[aid] = spec
    return cleaned


def prepare_turn(
    target: str,
    turn: Optional[int] = None,
    max_options: int = 6,
    strategy: str = "direct",
    samples: int = 4,
    seed: Optional[int] = None,
    model: Optional[str] = None,
    overrides: Optional[list[str]] = None,
    log: Optional[Callable[[str], None]] = None,
) -> dict[str, Any]:
    """Prepare one turn's menus; creates a new live game for a scenario target.

    Mirrors ``run_live_menu_command`` without the terminal interaction.
    Returns {"run_dir": ..., "turn": ...}.
    """
    from .cli import apply_config_overrides, apply_model_override
    from .live import mark_live_run
    from .output import OutputManager

    from .cli import resolve_output_base

    target_path = Path(target)
    if not target_path.exists():
        raise LiveError(f"Target does not exist: {target}")
    if is_run_dir(target_path) and turn is None:
        last = completed_turns(target_path)
        if last is None:
            raise LiveError(f"Cannot read completed turns in {target_path.name}.")
        if newest_pending_turn(target_path) is not None:
            raise LiveError(
                f"Turn {newest_pending_turn(target_path)} menus are already prepared – "
                "collect picks and resolve instead."
            )
        turn = last + 1
    if turn is None:
        turn = 1
    if max_options < 1:
        raise LiveError(f"max_options must be at least 1, got {max_options}")

    def emit(msg: str) -> None:
        if log is not None:
            log(msg)

    try:
        scenario, run_dir = open_live_state(target_path, turn)
    except (FileNotFoundError, ValueError) as e:
        raise LiveError(str(e))
    if scenario.config.requires_initial_state and scenario.initial_state is None:
        raise LiveError("This scenario declares requires_initial_state.")
    if turn > scenario.config.max_turns:
        raise LiveError(
            f"{scenario.config.name} plays {scenario.config.max_turns} turns – "
            f"turn {turn} does not exist. The game is over."
        )
    if model:
        apply_model_override(scenario.config.llm, model)
    apply_config_overrides(scenario, overrides)

    if run_dir is None:
        if seed is not None:
            scenario.config.random_seed = seed
        elif scenario.config.random_seed is None:
            scenario.config.random_seed = random.getrandbits(64)
        output_manager = OutputManager(scenario, resolve_output_base(target_path))
        run_dir = output_manager.start_run(prefix="live-")
        mark_live_run(run_dir)
        emit(f"New live game: {run_dir.name}")
    else:
        seed_from_run = read_run_seed(run_dir)
        if seed_from_run is not None:
            scenario.config.random_seed = seed_from_run
        output_manager = OutputManager(scenario, run_dir.parent.parent)
        output_manager.run_dir = run_dir

    emit(f"Generating menus for turn {turn} (waiting for the model)...")
    menus = run_menu_turn(
        scenario,
        output_manager,
        run_dir,
        turn,
        max_options=max_options,
        strategy=strategy,
        samples=samples,
        llm_client=LLM_CLIENT,
        config_overrides=overrides,
    )
    for menu in menus.values():
        emit(f"  {menu.actor_name}: {len(menu.options)} options")
    return {"run_dir": str(run_dir), "turn": turn}


def resolve_turn(
    run_dir: str,
    turn: int,
    picks: dict[str, str],
    model: Optional[str] = None,
    log: Optional[Callable[[str], None]] = None,
) -> dict[str, Any]:
    """Resolve a turn from validated picks; returns the post-resolve game state."""
    cleaned = validate_picks(run_dir, turn, picks)

    def emit(msg: str) -> None:
        if log is not None:
            log(msg)

    emit(f"Resolving turn {turn} from team picks (waiting for the model)...")
    result = run_resolve_turn(
        Path(run_dir),
        turn,
        cleaned,
        interactive=False,
        model_override=model,
        llm_client=LLM_CLIENT,
    )
    emit(f"Turn {result.turn} resolved.")
    state = game_state(run_dir)
    return {
        "run_dir": str(Path(run_dir)),
        "turn": result.turn,
        "time_period": result.time_period,
        "events": [e.get("id", "?") for e in result.triggered_events],
        "game": state,
    }


def model_warnings(scenario_path: str) -> list[str]:
    """Non-blocking model hygiene warnings for a scenario (info banner only)."""
    from .loader import load_scenario
    from .model_audit import collect_model_hygiene_warnings

    try:
        scenario = load_scenario(Path(scenario_path))
    except (FileNotFoundError, ValueError):
        return []
    llm_config = getattr(scenario.config, "llm", None)
    if llm_config is None:
        return []
    try:
        return [str(w) for w in collect_model_hygiene_warnings(llm_config)]
    except Exception:
        return []


# ---------------------------------------------------------------------------
# Background jobs: LLM calls take minutes, so POSTs return a job id to poll.
# ---------------------------------------------------------------------------

_JOB_SEQ = itertools.count(1)
_JOBS: dict[str, dict[str, Any]] = {}
_JOBS_LOCK = threading.Lock()
# One action per run directory at a time: guards double-submit during slow calls.
_RUN_LOCKS: dict[str, threading.Lock] = {}
_RUN_LOCKS_GUARD = threading.Lock()


def _run_lock(key: str) -> threading.Lock:
    with _RUN_LOCKS_GUARD:
        lock = _RUN_LOCKS.get(key)
        if lock is None:
            lock = threading.Lock()
            _RUN_LOCKS[key] = lock
        return lock


def submit_job(kind: str, fn: Callable[[], dict[str, Any]]) -> str:
    """Run fn in a background thread; the frontend polls /api/job?id=."""
    job_id = f"job-{next(_JOB_SEQ)}"
    with _JOBS_LOCK:
        _JOBS[job_id] = {
            "id": job_id,
            "kind": kind,
            "status": "running",
            "log": ["Started."],
            "result": None,
            "error": None,
        }

    def append(msg: str) -> None:
        with _JOBS_LOCK:
            _JOBS[job_id]["log"].append(msg)

    def work() -> None:
        try:
            result = fn(append)
            with _JOBS_LOCK:
                _JOBS[job_id]["result"] = result
                _JOBS[job_id]["log"].append("Done.")
                _JOBS[job_id]["status"] = "done"
        except LiveError as e:
            with _JOBS_LOCK:
                _JOBS[job_id]["error"] = str(e)
                _JOBS[job_id]["status"] = "error"
        except Exception as e:  # never leave the UI polling forever
            with _JOBS_LOCK:
                _JOBS[job_id]["error"] = f"Unexpected error: {e}"
                _JOBS[job_id]["status"] = "error"

    threading.Thread(target=work, daemon=True).start()
    return job_id


def get_job(job_id: str) -> Optional[dict[str, Any]]:
    """Current job snapshot (copies the log so polling cannot race the worker)."""
    with _JOBS_LOCK:
        job = _JOBS.get(job_id)
        if job is None:
            return None
        return {
            "id": job["id"],
            "kind": job["kind"],
            "status": job["status"],
            "log": list(job["log"]),
            "result": job["result"],
            "error": job["error"],
        }


# ---------------------------------------------------------------------------
# HTTP layer: JSON API plus the single-page frontend. Localhost only.
# ---------------------------------------------------------------------------


class FacilitatorHandler(BaseHTTPRequestHandler):
    """Routes. GET / serves the page; /api/* is JSON (see api_dispatch)."""

    server_version = "ScenarioLabFacilitator/1.0"

    def log_message(self, fmt: str, *args: Any) -> None:
        pass  # keep the facilitator's terminal quiet; job logs live in the UI

    def _send_json(self, payload: Any, status: int = 200) -> None:
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _send_html(self) -> None:
        body = INDEX_HTML.encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _read_json(self) -> dict[str, Any]:
        try:
            length = int(self.headers.get("Content-Length") or 0)
        except ValueError:
            length = 0
        if length <= 0:
            return {}
        try:
            data = json.loads(self.rfile.read(length).decode("utf-8"))
        except (json.JSONDecodeError, UnicodeDecodeError):
            return {}
        return data if isinstance(data, dict) else {}

    def do_GET(self) -> None:
        parsed = urllib.parse.urlparse(self.path)
        query = urllib.parse.parse_qs(parsed.query)
        arg = lambda k: query.get(k, [None])[0]  # noqa: E731
        try:
            if parsed.path == "/":
                self._send_html()
            elif parsed.path == "/api/scenarios":
                root = self.server.scenarios_dir  # type: ignore[attr-defined]
                self._send_json({"scenarios": list_scenarios(root)})
            elif parsed.path == "/api/runs":
                self._send_json({"runs": list_runs(_require(arg("scenario"), "scenario"))})
            elif parsed.path == "/api/game":
                self._send_json(game_state(_require(arg("run"), "run")))
            elif parsed.path == "/api/turn":
                run = _require(arg("run"), "run")
                turn_raw = _require(arg("turn"), "turn")
                self._send_json(turn_payload(run, int(turn_raw)))
            elif parsed.path == "/api/job":
                job = get_job(_require(arg("id"), "id"))
                if job is None:
                    self._send_json({"error": "Unknown job id."}, status=404)
                else:
                    self._send_json(job)
            elif parsed.path == "/api/hygiene":
                self._send_json(
                    {"warnings": model_warnings(_require(arg("scenario"), "scenario"))}
                )
            else:
                self._send_json({"error": "Not found."}, status=404)
        except LiveError as e:
            self._send_json({"error": str(e)}, status=400)
        except (FileNotFoundError, ValueError) as e:
            self._send_json({"error": f"Cannot load: {e}"}, status=400)

    def do_POST(self) -> None:
        parsed = urllib.parse.urlparse(self.path)
        body = self._read_json()
        try:
            if parsed.path == "/api/prepare":
                target = body.get("target")
                if not target or not isinstance(target, str):
                    self._send_json({"error": "Missing 'target'."}, status=400)
                    return
                params = {
                    "target": target,
                    "turn": body.get("turn"),
                    "max_options": int(body.get("max_options") or 6),
                    "strategy": str(body.get("strategy") or "direct"),
                    "samples": int(body.get("samples") or 4),
                    "seed": body.get("seed"),
                    "model": body.get("model") or None,
                    "overrides": body.get("overrides") or None,
                }
                lock_key = f"prepare:{target}"
                job_id = submit_job("prepare", lambda log: _locked(lock_key, log, params))
                self._send_json({"job": job_id})
            elif parsed.path == "/api/resolve":
                run = body.get("run")
                turn = body.get("turn")
                picks = body.get("picks")
                if not run or turn is None or not isinstance(picks, dict):
                    self._send_json(
                        {"error": "Missing 'run', 'turn', or 'picks'."}, status=400
                    )
                    return
                try:
                    validate_picks(str(run), int(turn), {k: str(v) for k, v in picks.items()})
                except LiveError as e:
                    self._send_json({"error": str(e)}, status=400)
                    return
                model = body.get("model") or None
                r, t = str(run), int(turn)
                p = {k: str(v) for k, v in picks.items()}
                job_id = submit_job(
                    "resolve",
                    lambda log: _locked_resolve(f"resolve:{r}:{t}", r, t, p, model, log),
                )
                self._send_json({"job": job_id})
            else:
                self._send_json({"error": "Not found."}, status=404)
        except (ValueError, TypeError) as e:
            self._send_json({"error": f"Bad request: {e}"}, status=400)


def _require(value: Optional[str], name: str) -> str:
    if not value:
        raise LiveError(f"Missing query parameter: {name}.")
    return value


def _locked(lock_key: str, log: Callable[[str], None], params: dict[str, Any]) -> dict[str, Any]:
    lock = _run_lock(lock_key)
    if not lock.acquire(blocking=False):
        raise LiveError("An action for this game is already running – wait for it.")
    try:
        return prepare_turn(log=log, **params)
    finally:
        lock.release()


def _locked_resolve(
    lock_key: str,
    run: str,
    turn: int,
    picks: dict[str, str],
    model: Optional[str],
    log: Callable[[str], None],
) -> dict[str, Any]:
    lock = _run_lock(lock_key)
    if not lock.acquire(blocking=False):
        raise LiveError("An action for this turn is already running – wait for it.")
    try:
        return resolve_turn(run, turn, picks, model=model, log=log)
    finally:
        lock.release()


def create_server(
    port: int = 8000, host: str = "127.0.0.1", scenarios_dir: Optional[Path] = None
) -> HTTPServer:
    """Build (not yet serve) the facilitator server; tests use port 0."""
    server = HTTPServer((host, port), FacilitatorHandler)
    server.scenarios_dir = scenarios_root(scenarios_dir)  # type: ignore[attr-defined]
    return server


def main(argv: Optional[list[str]] = None) -> int:
    """Entry point: `python -m scenario_lab.facilitator`."""
    parser = argparse.ArgumentParser(
        description="Facilitator web UI for live workshop games (localhost only)."
    )
    parser.add_argument("--port", type=int, default=8000)
    parser.add_argument("--host", type=str, default="127.0.0.1")
    parser.add_argument("--scenarios", type=Path, default=None)
    args = parser.parse_args(argv)
    server = create_server(args.port, args.host, args.scenarios)
    url = f"http://{args.host}:{server.server_port}/"
    print(f"Facilitator UI: {url}")
    print("Open it in a browser – leave this running for the whole workshop.")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nStopped.")
    return 0


# ---------------------------------------------------------------------------
# Frontend: single self-contained page (no build step, no external assets).
# Setup wizard -> turn view (briefing + per-team picks) -> print stylesheets.
# ---------------------------------------------------------------------------

INDEX_HTML = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Scenario Lab – Workshop Facilitator</title>
<style>
:root { color-scheme: light; }
body { font-family: system-ui, -apple-system, sans-serif; margin: 0; background: #f4f4f2; color: #222; }
header { background: #1d2a3a; color: #fff; padding: 12px 20px; }
header h1 { font-size: 18px; margin: 0; font-weight: 600; }
header p { margin: 2px 0 0; font-size: 13px; opacity: .8; }
main { max-width: 960px; margin: 0 auto; padding: 20px; }
.card { background: #fff; border-radius: 8px; padding: 16px 20px; margin-bottom: 16px; box-shadow: 0 1px 3px rgba(0,0,0,.08); }
.card h2 { margin-top: 0; font-size: 17px; }
button { background: #1d2a3a; color: #fff; border: 0; border-radius: 6px; padding: 9px 18px; font-size: 14px; cursor: pointer; }
button:disabled { opacity: .45; cursor: default; }
button.secondary { background: #e3e6ea; color: #222; }
select, input[type=text], input[type=number], textarea { font-size: 14px; padding: 7px 9px; border: 1px solid #c9cdd3; border-radius: 6px; width: 100%; box-sizing: border-box; }
label { font-size: 13px; font-weight: 600; display: block; margin: 10px 0 4px; }
.row { display: flex; gap: 12px; flex-wrap: wrap; }
.row > div { flex: 1; min-width: 150px; }
.option { border: 1px solid #dfe3e8; border-radius: 6px; padding: 8px 10px; margin: 6px 0; cursor: pointer; }
.option:hover { border-color: #1d2a3a; }
.option.selected { border-color: #1d2a3a; background: #eef3f8; }
.option .t { font-weight: 600; font-size: 14px; }
.option .d { font-size: 13px; color: #444; margin-top: 3px; white-space: pre-wrap; }
.joblog { background: #101820; color: #c8e6c9; border-radius: 6px; padding: 10px 12px; font-family: monospace; font-size: 12.5px; white-space: pre-wrap; }
.err { background: #fdecea; color: #8d1a1a; border-radius: 6px; padding: 10px 12px; font-size: 14px; }
.warn { background: #fff7e0; color: #6b5300; border-radius: 6px; padding: 10px 12px; font-size: 13.5px; }
.briefing { font-size: 14.5px; line-height: 1.55; }
.briefing table { border-collapse: collapse; width: 100%; font-size: 13.5px; }
.briefing th, .briefing td { border: 1px solid #cfd4da; padding: 5px 8px; text-align: left; }
.hidden { display: none !important; }
.team-head { display: flex; justify-content: space-between; align-items: baseline; }
.team-head span { font-size: 12.5px; color: #666; }
#print-area { display: none; }
@media print {
  header, main, .no-print { display: none !important; }
  #print-area { display: block !important; }
  .sheet { page-break-after: always; }
  .sheet h1 { font-size: 20px; }
  .sheet h2 { font-size: 16px; margin-bottom: 4px; }
  .sheet p, .sheet li { font-size: 13px; }
}
</style>
</head>
<body>
<header><h1>Scenario Lab – Workshop Facilitator</h1><p>No terminal needed: prepare menus, collect picks, resolve, print.</p></header>
<main>
<section id="screen-setup" class="card">
  <h2>1. Game</h2>
  <label for="sel-scenario">Scenario</label>
  <select id="sel-scenario"></select>
  <div id="hygiene"></div>
  <label for="sel-run">Game</label>
  <select id="sel-run"></select>
  <div class="row">
    <div><label for="inp-maxopts">Options per team (max)</label><input id="inp-maxopts" type="number" value="6" min="1"></div>
    <div><label for="sel-strategy">Menu strategy</label><select id="sel-strategy"><option value="direct">direct (fast)</option><option value="sample-distill">sample-distill (faithful, slower)</option></select></div>
    <div><label for="inp-lang">Handout language (blank = scenario default)</label><input id="inp-lang" type="text" placeholder="e.g. German, Swedish"></div>
  </div>
  <p style="margin-top:14px"><button id="btn-new">Start new game</button>
  <button id="btn-open" class="secondary">Open selected game</button></p>
  <div id="setup-msg"></div>
</section>
<section id="screen-turn" class="card hidden">
  <h2 id="turn-title">Turn</h2>
  <div id="turn-nav" class="no-print" style="margin-bottom:10px"></div>
  <div id="briefing" class="briefing"></div>
  <div id="menus"></div>
  <div id="turn-msg"></div>
  <p class="no-print"><button id="btn-resolve">Resolve this turn</button>
  <button id="btn-print" class="secondary">Print handouts</button></p>
  <div id="confirm-box" class="hidden">
    <h3>Confirm picks</h3>
    <div id="confirm-list"></div>
    <p><button id="btn-confirm">Confirm and resolve</button>
    <button id="btn-back" class="secondary">Back to editing</button></p>
  </div>
</section>
<section id="screen-job" class="card hidden">
  <h2 id="job-title">Working…</h2>
  <div id="job-log" class="joblog"></div>
</section>
</main>
<div id="print-area"></div>
<script>
"use strict";
const $ = (id) => document.getElementById(id);
const state = { runDir: null, game: null, turn: null, turnData: null, picks: {} };

async function api(path, opts) {
  const r = await fetch(path, opts);
  const data = await r.json();
  if (!r.ok) throw new Error(data.error || ("HTTP " + r.status));
  return data;
}
function esc(s) {
  return String(s).replace(/[&<>"]/g, (c) => ({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;"}[c]));
}
/* Minimal markdown renderer: headings, tables, lists, bold, code. Enough for
   briefings; menus render from structured JSON instead. */
function md(src) {
  const lines = String(src || "").split("\\n");
  let out = "", inList = false, inTable = false;
  const inline = (t) => esc(t)
    .replace(/`([^`]+)`/g, "<code>$1</code>")
    .replace(/\\*\\*([^*]+)\\*\\*/g, "<strong>$1</strong>");
  const closeList = () => { if (inList) { out += "</ul>"; inList = false; } };
  const closeTable = () => { if (inTable) { out += "</tbody></table>"; inTable = false; } };
  for (const line of lines) {
    const cells = line.trim().split("|").map((c) => c.trim());
    if (line.trim().startsWith("|") && line.trim().endsWith("|")) {
      const body = cells.slice(1, -1);
      if (body.every((c) => /^:?-{2,}:?$/.test(c))) continue; // separator row
      if (!inTable) { closeList(); out += "<table><tbody>"; inTable = true; }
      out += "<tr>" + body.map((c) => "<td>" + inline(c) + "</td>").join("") + "</tr>";
      continue;
    }
    closeTable();
    let m;
    if ((m = line.match(/^(#{1,3})\\s+(.*)/))) {
      closeList();
      const lvl = m[1].length + 1;
      out += "<h" + lvl + ">" + inline(m[2]) + "</h" + lvl + ">";
    } else if (/^\\s*[-*]\\s+/.test(line)) {
      if (!inList) { out += "<ul>"; inList = true; }
      out += "<li>" + inline(line.replace(/^\\s*[-*]\\s+/, "")) + "</li>";
    } else if (line.trim() === "") {
      closeList();
    } else {
      closeList();
      out += "<p>" + inline(line) + "</p>";
    }
  }
  closeList(); closeTable();
  return out;
}

async function loadScenarios() {
  const data = await api("/api/scenarios");
  const sel = $("sel-scenario");
  sel.innerHTML = data.scenarios.map((s) => `<option value="${esc(s.id)}">${esc(s.name)}</option>`).join("");
  if (!data.scenarios.length) {
    $("setup-msg").innerHTML = '<div class="err">No live-ready scenarios found. A scenario becomes live-ready by declaring a <code>workshop:</code> block in scenario.yaml.</div>';
    return;
  }
  await loadRuns();
}
async function loadRuns() {
  const sid = $("sel-scenario").value;
  const [runs, hyg] = await Promise.all([
    api("/api/runs?scenario=" + encodeURIComponent(sid)),
    api("/api/hygiene?scenario=" + encodeURIComponent(sid)),
  ]);
  $("hygiene").innerHTML = hyg.warnings.length
    ? '<div class="warn" style="margin-top:8px">Model notes: ' + hyg.warnings.map(esc).join(" ") + "</div>"
    : "";
  const sel = $("sel-run");
  sel.innerHTML = runs.runs.map((r) => {
    const s = r.pending_turn != null ? ` – turn ${r.pending_turn} menus ready`
      : (r.completed_turns != null ? ` – ${r.completed_turns} turn(s) complete` : "");
    return `<option value="${esc(r.run_dir)}">${esc(r.name)}${esc(s)}</option>`;
  }).join("") || '<option value="">(no games yet – start a new one)</option>';
}
async function pollJob(jobId, title, onDone) {
  $("screen-setup").classList.add("hidden");
  $("screen-turn").classList.add("hidden");
  $("screen-job").classList.remove("hidden");
  $("job-title").textContent = title;
  for (;;) {
    await new Promise((r) => setTimeout(r, 1000));
    const job = await api("/api/job?id=" + encodeURIComponent(jobId));
    $("job-log").textContent = job.log.join("\\n");
    if (job.status === "done") { onDone(job.result); return; }
    if (job.status === "error") {
      $("job-log").outerHTML = '<div class="err">' + esc(job.error) + '</div>';
      const b = document.createElement("button");
      b.textContent = "Back";
      b.onclick = () => location.reload();
      $("screen-job").appendChild(b);
      return;
    }
  }
}
async function openGame(runDir, turn) {
  const game = await api("/api/game?run=" + encodeURIComponent(runDir));
  state.runDir = runDir; state.game = game;
  const t = turn || game.pending_turn || (game.completed_turns != null ? game.completed_turns + 1 : 1);
  await showTurn(Math.min(t, game.max_turns));
}
async function showTurn(n) {
  const data = await api("/api/turn?run=" + encodeURIComponent(state.runDir) + "&turn=" + n);
  state.turn = n; state.turnData = data; state.picks = {};
  $("screen-setup").classList.add("hidden");
  $("screen-job").classList.add("hidden");
  $("screen-turn").classList.remove("hidden");
  $("turn-msg").innerHTML = "";
  $("confirm-box").classList.add("hidden");
  $("turn-title").textContent = `Turn ${n} of ${state.game.max_turns} – ${state.game.name}`;
  const nav = state.game.turns.map((t) =>
    `<button class="secondary" data-turn="${t.turn}" ${t.turn === n ? "disabled" : ""}>${t.turn}${t.resolved ? " ✓" : (t.has_menus ? " …" : "")}</button>`
  ).join(" ");
  $("turn-nav").innerHTML = nav || "";
  $("turn-nav").querySelectorAll("button[data-turn]").forEach((b) =>
    b.addEventListener("click", () => showTurn(Number(b.dataset.turn))));
  $("briefing").innerHTML = md(data.briefing_md);
  const box = $("menus");
  if (!data.menus) {
    box.innerHTML = data.resolved
      ? "<p><em>This turn is resolved; its menus were superseded by the next turn.</em></p>"
      : '<div class="err">No menus for this turn yet. <button id="btn-prep" class="secondary">Prepare menus now</button></div>';
    const prep = $("btn-prep");
    if (prep) prep.onclick = prepareCurrent;
    return;
  }
  box.innerHTML = "";
  for (const aid of Object.keys(data.menus)) {
    const m = data.menus[aid];
    const div = document.createElement("div");
    div.innerHTML = `<div class="team-head"><h3>${esc(m.actor_name)}</h3><span>choose exactly one</span></div>`;
    m.options.forEach((o) => {
      const d = document.createElement("div");
      d.className = "option";
      d.innerHTML = `<div class="t">${o.index}. ${esc(o.title)}</div><div class="d">${esc(o.text)}</div>`;
      d.addEventListener("click", () => {
        state.picks[aid] = String(o.index);
        div.querySelectorAll(".option").forEach((x) => x.classList.remove("selected"));
        d.classList.add("selected");
        const free = div.querySelector("textarea");
        if (free) free.value = "";
      });
      div.appendChild(d);
    });
    div.insertAdjacentHTML("beforeend",
      `<label>Or your own wording (overrides the selected option)</label><textarea rows="2" data-free="${esc(aid)}" placeholder="Free-text move…"></textarea>`);
    box.appendChild(div);
  }
  box.querySelectorAll("textarea[data-free]").forEach((t) =>
    t.addEventListener("input", () => {
      const aid = t.dataset.free;
      if (t.value.trim()) {
        state.picks[aid] = t.value;
        t.closest("div").parentElement.querySelectorAll(".option").forEach((x) => x.classList.remove("selected"));
      } else if (/^\\d+$/.test(state.picks[aid] || "")) {
        // keep an earlier radio choice if the box is cleared
      } else {
        delete state.picks[aid];
      }
    }));
}
function prepareOverrides() {
  const lang = $("inp-lang").value.trim();
  return lang ? ["output_language=" + lang] : null;
}
async function prepareCurrent() {
  const body = { target: state ? state.runDir : null, turn: state ? state.turn : 1,
    max_options: Number($("inp-maxopts").value) || 6, strategy: $("sel-strategy").value,
    overrides: prepareOverrides() };
  const { job } = await api("/api/prepare", { method: "POST", body: JSON.stringify(body),
    headers: { "Content-Type": "application/json" } });
  await pollJob(job, "Preparing menus – the teams can stretch their legs…", (res) => openGame(res.run_dir, res.turn));
}
function collectPicks() {
  const picks = {};
  for (const aid of Object.keys(state.turnData.menus)) {
    const v = (state.picks[aid] || "").trim();
    if (v) picks[aid] = v;
  }
  return picks;
}
$("btn-resolve").addEventListener("click", () => {
  const picks = collectPicks();
  const missing = Object.keys(state.turnData.menus).filter((a) => !picks[a]);
  if (missing.length) {
    $("turn-msg").innerHTML = '<div class="err">Missing picks for: ' + missing.map(esc).join(", ") + ".</div>";
    return;
  }
  $("confirm-list").innerHTML = Object.keys(state.turnData.menus).map((a) => {
    const m = state.turnData.menus[a];
    const v = picks[a];
    const label = /^\\d+$/.test(v)
      ? `option ${v} (${esc((m.options.find((o) => String(o.index) === v) || {}).title || "")})`
      : "free text: " + esc(v);
    return `<p><strong>${esc(m.actor_name)}:</strong> ${label}</p>`;
  }).join("");
  $("confirm-box").classList.remove("hidden");
  $("confirm-box").scrollIntoView();
});
$("btn-back").addEventListener("click", () => $("confirm-box").classList.add("hidden"));
$("btn-confirm").addEventListener("click", async () => {
  $("confirm-box").classList.add("hidden");
  const { job } = await api("/api/resolve", { method: "POST",
    body: JSON.stringify({ run: state.runDir, turn: state.turn, picks: collectPicks() }),
    headers: { "Content-Type": "application/json" } });
  await pollJob(job, "Resolving the turn (waiting for the model)…", (res) => {
    const ev = res.events.length ? "Events: " + res.events.join(", ") : "No events.";
    alert(`Turn ${res.turn} (${res.time_period}) resolved. ${ev}`);
    openGame(res.run_dir, res.game.pending_turn || res.turn + 1);
  });
});
$("btn-print").addEventListener("click", () => {
  const d = state.turnData;
  let h = `<div class="sheet"><h1>Briefing – turn ${d.turn}</h1>${md(d.briefing_md)}</div>`;
  if (d.menus) for (const aid of Object.keys(d.menus)) {
    const m = d.menus[aid];
    h += `<div class="sheet"><h1>${esc(m.actor_name)} – turn ${d.turn}</h1><p>Choose exactly ONE option.</p>` +
      m.options.map((o) => `<h2>${o.index}. ${esc(o.title)}</h2><p>${esc(o.text).replace(/\\n/g, "<br>")}</p>`).join("") + "</div>";
  }
  $("print-area").innerHTML = h;
  window.print();
});
$("btn-new").addEventListener("click", async () => {
  const body = { target: $("sel-scenario").value, turn: 1,
    max_options: Number($("inp-maxopts").value) || 6, strategy: $("sel-strategy").value,
    overrides: prepareOverrides() };
  const { job } = await api("/api/prepare", { method: "POST", body: JSON.stringify(body),
    headers: { "Content-Type": "application/json" } });
  await pollJob(job, "Starting a new game (waiting for the model)…", (res) => openGame(res.run_dir, res.turn));
});
$("btn-open").addEventListener("click", async () => {
  const run = $("sel-run").value;
  if (!run) return;
  await openGame(run);
});
$("sel-scenario").addEventListener("change", loadRuns);
loadScenarios().catch((e) => {
  $("setup-msg").innerHTML = '<div class="err">' + esc(e.message) + "</div>";
});
</script>
</body>
</html>"""


if __name__ == "__main__":
    raise SystemExit(main())

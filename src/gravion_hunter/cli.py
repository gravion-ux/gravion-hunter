"""Command line driver: hunt.py

Usage:
    hunt init   --scope scope.md --state campaign.json [--autopilot]
    hunt add    --state campaign.json --host api.example.com --class idor --endpoint /v1/orders/{id}
    hunt next   --state campaign.json
    hunt start  --state campaign.json --row 1
    hunt close  --state campaign.json --row 1 --outcome confirmed
    hunt gate   --state campaign.json --row 1 --answers exploitable_now,accepted_impact,...
    hunt dedupe --state campaign.json --row 1 --sources "h1-disclosed,changelog,wordfence"
    hunt report --state campaign.json --row 1
    hunt submit --state campaign.json --row 1 [--approve]
    hunt outcome --state campaign.json --row 1 --result valid
    hunt status --state campaign.json
"""

from __future__ import annotations

import argparse
import sys

from .campaign import GATE_QUESTIONS, Campaign
from .scope import Scope


def _load(path: str) -> Campaign:
    with open(path, encoding="utf-8") as fh:
        return Campaign.from_json(fh.read())


def _save(campaign: Campaign, path: str) -> None:
    with open(path, "w", encoding="utf-8") as fh:
        fh.write(campaign.to_json())


def main(argv: list | None = None) -> int:
    parser = argparse.ArgumentParser(prog="hunt", description="gravion-hunter campaign driver")
    sub = parser.add_subparsers(dest="cmd", required=True)

    p = sub.add_parser("init"); p.add_argument("--scope", required=True)
    p.add_argument("--state", required=True); p.add_argument("--autopilot", action="store_true")

    p = sub.add_parser("add"); p.add_argument("--state", required=True)
    p.add_argument("--host", required=True); p.add_argument("--class", dest="vuln_class", required=True)
    p.add_argument("--endpoint", required=True)

    for name in ("next", "status"):
        p = sub.add_parser(name); p.add_argument("--state", required=True)

    p = sub.add_parser("start"); p.add_argument("--state", required=True); p.add_argument("--row", type=int, required=True)

    p = sub.add_parser("close"); p.add_argument("--state", required=True)
    p.add_argument("--row", type=int, required=True)
    p.add_argument("--outcome", choices=["confirmed", "ruled_out", "open_proof_gap"], required=True)

    p = sub.add_parser("gate"); p.add_argument("--state", required=True)
    p.add_argument("--row", type=int, required=True)
    p.add_argument("--answers", required=True, help="comma list of passed questions; 'all' passes everything")
    p.add_argument("--fail", default="", help="comma list of failed questions")

    p = sub.add_parser("dedupe"); p.add_argument("--state", required=True)
    p.add_argument("--row", type=int, required=True); p.add_argument("--sources", required=True)

    p = sub.add_parser("report"); p.add_argument("--state", required=True); p.add_argument("--row", type=int, required=True)

    p = sub.add_parser("submit"); p.add_argument("--state", required=True)
    p.add_argument("--row", type=int, required=True); p.add_argument("--approve", action="store_true")

    p = sub.add_parser("outcome"); p.add_argument("--state", required=True)
    p.add_argument("--row", type=int, required=True)
    p.add_argument("--result", choices=["valid", "informative", "duplicate", "na"], required=True)

    args = parser.parse_args(argv)

    if args.cmd == "init":
        scope = Scope.from_file(args.scope)
        campaign = Campaign(scope=scope, autopilot=args.autopilot)
        _save(campaign, args.state)
        print(f"campaign initialised for {scope.program or 'programme'} "
              f"({len(scope.in_scope)} in-scope patterns, autopilot={args.autopilot})")
        return 0

    campaign = _load(args.state)

    if args.cmd == "add":
        row = campaign.add_row(args.host, args.vuln_class, args.endpoint)
        print(f"row {row.id}: {row.vuln_class} on {row.host}{row.endpoint} [{row.state}]")
    elif args.cmd == "next":
        row = campaign.next_row()
        print(f"row {row.id}: {row.vuln_class} {row.host}{row.endpoint} [{row.state}]" if row else "no open rows")
    elif args.cmd == "start":
        row = campaign.start(args.row); print(f"row {row.id} -> working")
    elif args.cmd == "close":
        row = campaign.close(args.row, args.outcome); print(f"row {row.id} -> {row.state}")
    elif args.cmd == "gate":
        passed = set(GATE_QUESTIONS) if args.answers == "all" else {a.strip() for a in args.answers.split(",") if a.strip()}
        failed = {a.strip() for a in args.fail.split(",") if a.strip()}
        answers = {q: (q in passed and q not in failed) for q in GATE_QUESTIONS}
        row = campaign.record_gate(args.row, answers); print(f"row {row.id} -> {row.state}")
    elif args.cmd == "dedupe":
        row = campaign.record_dedupe(args.row, args.sources.split(",")); print(f"row {row.id} -> deduped")
    elif args.cmd == "report":
        row = campaign.mark_reported(args.row); print(f"row {row.id} -> reported")
    elif args.cmd == "submit":
        row = campaign.submit(args.row, approved=args.approve); print(f"row {row.id} -> submitted")
    elif args.cmd == "outcome":
        row = campaign.record_outcome(args.row, args.result); print(f"row {row.id} outcome={row.outcome}")
    elif args.cmd == "status":
        board = campaign.board()
        print("  ".join(f"{k}={v}" for k, v in board.items() if v))
        print(f"autopilot={campaign.autopilot} brake_tripped={campaign.brake_tripped()}")
    _save(campaign, args.state)
    return 0


if __name__ == "__main__":
    sys.exit(main())

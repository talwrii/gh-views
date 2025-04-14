#!/usr/bin/python3

import argparse
import json
import logging
import os
import subprocess
import sys
from pathlib import Path

PARSER = argparse.ArgumentParser(description='Get information about github download stats')

PARSER.add_argument('repo', nargs="?", help="Repository to get data for. Omit to list repositories")
PARSER.add_argument("--fetch", action="store_true", help="Fetch data. Omit repo to fetch all data.")
PARSER.add_argument("--debug", action="store_true", help="Include debug output")
PARSER.add_argument("-a", "--all", action="store_true", help="Show data for all repos")
PARSER.add_argument("-t", "--timeseries", action="store_true", help="Output a timeseries rather than summary")

args = PARSER.parse_args()

STATS_PATH = Path(os.path.expanduser("~")) / ".local" / "state" / "gh-views"
STATS_PATH.mkdir(exist_ok=True)

def read_timeseries(filename: Path) -> list[dict]:
    raw_data = []
    with open(filename) as stream:
        for line in stream:
            raw_data.append(json.loads(line))

    data = []
    timestamps = set()
    for x in raw_data:
        if x["timestamp"] in timestamps:
            continue
        data.append(x)
        timestamps.add(x["timestamp"])

    return data


def get_repos():
    found = set()
    for path in STATS_PATH.iterdir():
        path: Path
        name, ext = os.path.splitext(path.name)
        if ext != ".jsonl":
            continue

        name = name.replace("--", "/").rsplit("/", 1)[0]
        if name not in found:
            yield name
        found.add(name)

def main():
    if args.debug:
        logging.basicConfig(level=logging.DEBUG, stream=sys.stderr)
    else:
        logging.basicConfig(level=logging.INFO, stream=sys.stderr)

    display_func = display_timeseries if args.timeseries else display_summary

    if args.repo is None:
        if args.fetch:
            repos = list(get_repos())
            for r in repos:
                fetch(r)
        elif args.all:
            for r in sorted(list(get_repos())):
                print(r)
                display_func(r)
                print()
        else:
            repos = list(get_repos())
            for repo in sorted(repos):
                print(repo)
        return

    if args.fetch:
        fetch(args.repo)

    display_func(args.repo)

def display_summary(repo):
    clone_ts = read_timeseries(clone_path(repo))
    view_ts = read_timeseries(views_path(repo))

    if not clone_ts and not view_ts:
        print("No data yet")

    clone_start = min(d["timestamp"] for d in clone_ts) if clone_ts else None
    view_start = min(d["timestamp"] for d in view_ts) if clone_ts else None

    if clone_start and view_start:
        start = max([clone_start, view_start])
    else:
        start = clone_start or view_start

    clone_ts = ts_after(start, clone_ts)
    view_ts = ts_after(start, view_ts)

    print("Since", min(d["timestamp"] for d in clone_ts))
    print(f"views: unique:{uniques(view_ts)} total:{total(view_ts)}")
    print(f"clones: unique:{uniques(clone_ts)} total:{total(clone_ts)}")


def display_timeseries(repo):
    clone_ts = read_timeseries(clone_path(repo))
    view_ts = read_timeseries(views_path(repo))

    clone_start = min(d["timestamp"] for d in clone_ts)
    view_start = min(d["timestamp"] for d in view_ts)
    start = max([clone_start, view_start])

    clone_ts = ts_after(start, clone_ts)
    view_ts = ts_after(start, view_ts)

    for update in merge(dict(clone=clone_ts, views=view_ts)):
        print(json.dumps(update))


def merge(series):
    "Merge series together"
    series = {k: iter(v) for k, v in series.items()}
    series_peeks = {}

    while True:
        for k in series:
            if k not in series_peeks:
                try:
                    series_peeks[k] = next(series[k])
                except StopIteration:
                    series_peeks[k] = None

        if all(x is None for x in series_peeks.values()):
            break

        peek_timestamps = [p["timestamp"] for p in series_peeks.values() if p]
        min_timestamp = min(peek_timestamps)

        result = {"timestamp": min_timestamp}

        to_delete = set()
        for k, v in series_peeks.items():
            if v is not None and v["timestamp"] == min_timestamp:
                result.update({f"{k}_{k_}": v_ for k_, v_ in v.items() if k_ != "timestamp"})
                to_delete.add(k)

        for k in to_delete:
            del series_peeks[k]


        yield result

def ts_after(start, ts):
    return [d for d in ts if d["timestamp"] > start]


def fetch_clones(repo):
    data = fetch_data(f"repos/{repo}/traffic/clones")

    output = clone_path(repo)
    logging.debug("Writing to %r", output)
    update_timeseries(output, data["clones"])

def fetch_views(repo):
    data = fetch_data(f"repos/{repo}/traffic/views")
    output = views_path(repo)
    logging.debug("Writing to %r", output)
    update_timeseries(output, data["views"])


def update_timeseries(path, new_ts):
    if os.path.exists(path):
        ts = read_timeseries(path)
    else:
        ts = None

    timestamps = ts and set(d["timestamp"] for d in ts)
    with open(path, "a") as f:
        for x in new_ts:
            if timestamps and x["timestamp"] not in timestamps:
                f.write(json.dumps(x) + "\n")

def fetch_data(url):
    return json.loads(subprocess.check_output(["gh", "api", url]))


def clone_path(repo):
    return STATS_PATH / (repo.replace("/", "--") + "--" + "clones.jsonl")


def views_path(repo):
    return STATS_PATH / (repo.replace("/", "--") + "--" + "views.jsonl")


def uniques(ts):
    return sum(d["uniques"] for d in ts)

def total(ts):
    return sum(d["count"] for d in ts)


def fetch(repo):
    logging.info("Fetching clones for %r...", repo)
    fetch_clones(repo)
    logging.info("Fetching downloads for %r...", repo)
    fetch_views(repo)

if __name__ == '__main__':
    main()

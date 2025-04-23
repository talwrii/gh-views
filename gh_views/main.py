#!/usr/bin/python3

import argparse
import datetime
import json
import logging
import os
import subprocess
import sys
from pathlib import Path

PARSER = argparse.ArgumentParser(description='Get information about github download stats')
action_mx = PARSER.add_mutually_exclusive_group()
PARSER.add_argument('repos', nargs="*", help="Repository to get data for. Omit to list repositories")
PARSER.add_argument("-f", "--fetch", action="store_true", help="Fetch data. Omit repo to fetch all data.")
PARSER.add_argument("--debug", action="store_true", help="Include debug output")
PARSER.add_argument("-a", "--all", action="store_true", help="Show data for all repos")
PARSER.add_argument("--json", action='store_true', help="Output results in json")
PARSER.add_argument("--common-start", action='store_true', help="When dealing with multiple repos use the latest start date")

# Ddd a --date option in isoformat
PARSER.add_argument("-d", "--date", type=datetime.date.fromisoformat, help="Display data for this day (in UTC)")



action_mx.add_argument("--delete", action="store_true",
                       help="Delete data related to and stop fetching data for a repository")
action_mx.add_argument("-t", "--timeseries", action="store_true", help="Output a timeseries rather than summary")
action_mx.add_argument("-p", "--path",  action='store_true', help="Output the config path")
action_mx.add_argument("--last-fetch",  action='store_true', help="Output the last fetch of a repo (or the least recent last fetch of all repos if no repo is provided)")

STATS_PATH = Path(os.path.expanduser("~")) / ".local" / "state" / "gh-views"

def read_timeseries(filename: Path) -> list[dict]:
    if not os.path.exists(filename):
        return None

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
    args = PARSER.parse_args()

    if args.last_fetch:
        repos = args.repos or get_repos()
        print(min(get_fetch(r) for r in repos))
        return

    if args.path:
        print(str(STATS_PATH))
        return


    todays_data = {}
    STATS_PATH.mkdir(exist_ok=True)

    if args.debug:
        logging.basicConfig(level=logging.DEBUG, stream=sys.stderr)
    else:
        logging.basicConfig(level=logging.INFO, stream=sys.stderr)

    if args.timeseries:
        display_func = display_timeseries
    else:
        display_func = display_summary


    if args.delete:
        if args.all:
            print("Refusing to delete all data.")
            print("You can manually delete {STATS_PATH} to clear all data")
            return

        if not args.repos:
            raise Exception('Must specify a repo to delete')

        for r in args.repos:
            delete(r)
        return

    def prepare_series(r):
        series = read_series(r)
        if todays_data:
            add_data(series, todays_data[r])


        if args.date:
            series = series_on_date(args.date, series)

        return series


    if not args.repos:
        if args.fetch:
            repos = list(get_repos())
            for r in repos:
                todays_data[r] = fetch(r)
        elif args.all:
            if args.json:
                result = []
                for r in sorted(get_repos()):
                    series = prepare_series(r)
                    result.append(display_summary_data(r, series))
                print(json.dumps(result, indent=2))
            else:
                for r in sorted(get_repos()):
                    series = prepare_series(r)
                    print(r)
                    display_func(r, series)
                    print()
        else:
            repos = list(get_repos())
            for repo in sorted(repos):
                print(repo)
        return

    if args.fetch:
        for r in args.repos:
            todays_data[r] = fetch(r)

    if args.common_start:
        start = max(get_start(r) for r in args.repos)
    else:
        start = None


    if args.json:
        result = []
        for r in args.repos:
            series = prepare_series(r)
            result.append(display_summary_data(r, series, start=start))
        print(json.dumps(result, indent=2))
    else:
        for r in args.repos:
            series = prepare_series(r)
            display_func(r, series=series, start=start)


def add_data(series, data):
    for k, v in data.items():
        if v is not None:
            series[k].append(v)



def delete(repo):
    for d in [fetch_path(repo), clone_path(repo), views_path(repo)]:
        d.unlink()

def get_fetch(repo):
    return read_timeseries(fetch_path(repo))[-1]["timestamp"]

def get_first_fetch(repo):
    return read_timeseries(fetch_path(repo))[0]["timestamp"]

def get_start(repo) -> str:
    if not os.path.exists(fetch_path(repo)):
        raise Exception('Fetch data does not exist (added in 2.1.0) rerun --fetch. This means old data is ignored. If you care tweak the fetch file by hand.')

    ts = get_first_fetch(repo)
    fetch_ts = NaiveUtcDate.parse(ts)

    window_ts = (fetch_ts.replace(hour=0, minute=0, second=0, microsecond=0) - NaiveUtcDate.timedelta(days=12))

    return window_ts.isoformat() + "Z"


class NaiveUtcDate:
    # This mostly exists work work around the fact that python will not add Z's
    # for the utc timezone and that is the format we get dates in

    from datetime import timedelta
    timedelta = timedelta

    @classmethod
    def now(cls):
        import datetime
        return datetime.datetime.utcnow().replace(tzinfo=None)

    @classmethod
    def today(cls):
        import datetime
        return datetime.datetime.utcnow().date()


    @classmethod
    def format(cls, dt):
        if dt.tzinfo != None:
            raise Exception(f"{dt} has timezone")

        return dt.isoformat() + "Z"

    @classmethod
    def parse(cls, s: str):
        import datetime
        if not (s[-2].isdigit() and s[-1] == "Z"):
            raise Exception(f'timestamp ({s}) is not in UTC')

        return datetime.datetime.fromisoformat(s).replace(tzinfo=None)


def read_series(repo):
    return {
        "clones": read_timeseries(clone_path(repo)),
        "views": read_timeseries(views_path(repo))
        }


def display_summary_data(repo, series, start=None):
    repo_start = get_start(repo)
    if start and start < repo_start:
        raise Exception('start {start} must be after window for repo data (started at {start})')

    start = start or repo_start

    series = series_after(start, series)
    view_ts = series["views"]
    clone_ts = series["clones"]

    start_dt = NaiveUtcDate.parse(start)

    days = (NaiveUtcDate.now() - start_dt).days

    return {
        "repo": repo,
        "start": start,
        "days": days,
        "unique_views": uniques(view_ts),
        "unique_views_per_day": round(uniques(view_ts) / days, 3),
        "unique_clones": uniques(clone_ts),
        "unique_clones_per_day": round(uniques(clone_ts) / days, 3),
        "total_clones": total(clone_ts),
        "total_clones_per_day": round(total(clone_ts) / days, 3),
        "total_views": total(view_ts),
        "total_views_per_day": round(total(view_ts) / days, 3),
    }

def display_summary(repo, series, start=None):
    data = display_summary_data(repo, series, start=start)
    if data is None:
        return
    print(f"Since {data['start']} ({data['days']} days)")
    print(f"VIEWS  unique:{data['unique_views']} ({data['unique_views_per_day']:.1f} per day) total:{data['total_views']} ({data['total_views_per_day']:.1f} per day)")
    print(f"CLONES unique:{data['unique_clones']} ({data['unique_clones_per_day']:.1f} per day) total:{data['total_clones']} ({data['total_clones_per_day']:.1f} per day)")

def display_summary_json(repo, series, start=None):
    data = display_summary_data(repo, series, start=start)
    print(json.dumps(data, indent=2))

def display_timeseries(repo, series, start=None):
    repo_start = get_start(repo)
    if start and start < repo_start:
        raise Exception(f'start ({start}) must be after start of repo data ({repo_start})')

    start = start or repo_start

    clone_ts = ts_after(start, series["clones"])
    view_ts = ts_after(start, series["views"])

    for update in merge(dict(clone=clone_ts, views=view_ts)):
        print(json.dumps(dict(repo=repo, **update)))

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

def ts_on_date(date, ts):
    return [d for d in ts if d["timestamp"].split("T")[0] == date.isoformat()]

def series_after(start, series):
    return {k: ts_after(start, v) for k, v in series.items()}

def series_on_date(date, series):
    return {k: ts_on_date(date, v) for k, v in series.items()}

def fetch_clones(repo):
    data = fetch_data(f"repos/{repo}/traffic/clones")
    output = clone_path(repo)
    logging.debug("Writing to %r", output)
    update_timeseries(output, data["clones"])
    return get_todays_point(data["clones"])

def get_todays_point(ts):
    if not ts:
        return None
    last_point = ts[-1]
    if NaiveUtcDate.parse(last_point["timestamp"]).date() == NaiveUtcDate.today():
        return last_point
    else:
        return None

def fetch_views(repo):
    data = fetch_data(f"repos/{repo}/traffic/views")
    output = views_path(repo)
    logging.debug("Writing to %r", output)
    update_timeseries(output, data["views"])
    return get_todays_point(data["views"])


def update_timeseries(path, new_ts):
    if os.path.exists(path):
        ts = read_timeseries(path)
    else:
        ts = None

    timestamps = ts and set(d["timestamp"] for d in ts)
    with open(path, "a") as f:
        for x in new_ts:
            ts = NaiveUtcDate.parse(x["timestamp"])
            if ts.date() == NaiveUtcDate.today():
                # Exclude today because it could change
                continue
            if not timestamps or x["timestamp"] not in timestamps:
                f.write(json.dumps(x) + "\n")

def fetch_data(url):
    return json.loads(subprocess.check_output(["gh", "api", url]))



def clone_path(repo) -> Path:
    return STATS_PATH / (repo.replace("/", "--") + "--" + "clones.jsonl")

def views_path(repo) -> Path:
    return STATS_PATH / (repo.replace("/", "--") + "--" + "views.jsonl")

def fetch_path(repo) -> Path:
    return STATS_PATH / (repo.replace("/", "--") + "--fetchs.jsonl")


def uniques(ts):
    return sum(d["uniques"] for d in ts)

def total(ts):
    return sum(d["count"] for d in ts)

def fetch(repo: str):
    record_fetch(repo)
    logging.info("Fetching clones for %r...", repo)
    todays_clones = fetch_clones(repo)
    logging.info("Fetching downloads for %r...", repo)
    todays_views = fetch_views(repo)
    return {"clones": todays_clones, "views": todays_views}


def record_fetch(repo: str):
    path = fetch_path(repo)
    ts = NaiveUtcDate.now()
    with open(path, "a") as f:
        f.write(json.dumps({"timestamp": NaiveUtcDate.format(ts)}) + "\n")


if __name__ == '__main__':
    main()

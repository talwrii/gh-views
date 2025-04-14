# Github command-line views
@readwithai - [X](https://x.com/readwithai) - [blog](https://readwithai.substack.com) -  [machine-aided-reading](https://www.reddit.com/r/machineAidedReading/)

Fetch (and maintain) information about the number of views or clones a github repository has.

# Motivation
It can be quite natural to host some material such as documentation, cookbooks and list on github. `github` provides an API to query the number of views a repository has with some limitations. The main limitation is that data is only detained for two weeks. This script, if run periodically, will collect data about the numbers of downloads and views of a repository and provided aggregates.

It can also output a completely timeline.

# Alternatives and prior work
This makes use of the [github REST API](https://docs.github.com/en/rest?apiVersion=2022-11-28) specifically [the traffic endpoints](https://docs.github.com/en/rest/metrics/traffic?apiVersion=2022-11-28). You can call these directly with the [gh command-line client](https://github.com/cli/cli).

There are some repositories [intended for uses as github actions](https://github.com/sangonzal/repository-traffic-action) to sore these actions. I find github actions unwieldy and difficult to debug. [repohistory](https://github.com/repohistory/repohistory?tab=readme-ov-file) provides similar functionality through a web GUI - it has no intructions for running locally but provides a web log in. [ghstats](https://github.com/vladkens/ghstats) is another GUI interface but has instructions on how to run it, collects more information and provides an end-point for querying (I may have used this if I discovered it earlier). There are [tools for forward this data to splunk](https://github.com/josehelps/github-traffic-collector).

This appears to be the only command-line tool


# Installation
Make sure you have the github command line-interface, [gh](https://github.com/cli/cli), installed and that you have logged in to the command-line.

You can then install gh-views with [pipx](https://github.com/pypa/pipx).

```
pipx install gh-views
```

# Usage
```
gh-views talwrii/plugin-repl --fetch
```

Will fetch the clone and view statistics for the repository `talwrii/plugin-repl`. After you have run this you can run `gh-views talwrii/plugin-repl

To show all the repositories for which stats are collected you can run:
```
gh-views
```

To display all statistics you can run
```
gh-views --all
```

To update all stats for tracked repositories you can run
```
gh-views --fetch
```

You may wish to run this periodically for example using a [systemd timer](https://www.freedesktop.org/software/systemd/man/latest/systemd.timer.html) or [cron job](https://kubernetes.io/docs/concepts/workloads/controllers/cron-jobs/) to ensure that all data is collected.

You can run:
```
gh-views talwrii/plugin-repl --timeseries
```
to output a complete timeseries of statistics for each day.

# Support
If you found this tool particularly useful you can give me some money (maybe $3?) on [my ko-fi](https://ko-fi.com/readwithai).

This will incentivise me to respond to tickets on this repository and release [similar command-line tools](https://readwithai.substack.com/p/my-productivity-tools).

# About me
I am @readwithai I create tools for reading, research and agency sometimes using [Obsidian](https://readwithai.substack.com/p/what-exactly-is-obsidian).

If this sounds interesting, of you found this tool useful you might like to:

1. [Follow me on X](https://x.com/readwithai) where I post about these sort of tools.
1. [Look at my collection of productivity tools](https://readwithai.substack.com/p/my-productivity-tools
) similar to this
1. Read about [taking better notes with the note taking app, Obsidian](https://readwithai.substack.com/p/making-better-notes-with-obsidian)


If you rae interested in reading and research you can [follow me on my blog](https://readwithai.substack.com).

![logo](logo.png)

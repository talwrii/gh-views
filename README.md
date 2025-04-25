# Github command-line views
@readwithai - [X](https://x.com/readwithai) - [blog](https://readwithai.substack.com) -  [machine-aided-reading](https://www.reddit.com/r/machineAidedReading/)

Fetch (and update) information about the number of views or clones of a Github repository.

This tools requires the [gh Github command-line tool](https://github.com/cli/cli) which is used to handle authentication.

# Motivation
It can be quite natural to host some material such as documentation, cookbooks and lists on Github. Github provides an API to query the number of views and clones a repository has received on a daily basis, with some limitations. The main limitation is that data is only retained for two weeks. `gh-views`, if run periodically, will collect data about the number of downloads and views of a repository and can provide both aggregates of this data such as the total number of views to date or a complete timelines of statistics.


# Alternatives and prior work
This makes use of the [Github REST API](https://docs.github.com/en/rest?apiVersion=2022-11-28) specifically [traffic endpoints](https://docs.github.com/en/rest/metrics/traffic?apiVersion=2022-11-28). You can use the API yourself with [gh command-line client](https://github.com/cli/cli) command, `gh api` or, indeed perform HTTP requests yourself directly or with a library after you have obtained a Github token. The `gh` command-line makes it very easy to authenticate with Github.

There are some repositories [intended for use as github actions](https://github.com/sangonzal/repository-traffic-action) which maintain a similar sort of timeline. I find Github actions unwieldy and difficult to debug.

[repohistory](https://github.com/repohistory/repohistory?tab=readme-ov-file) provides similar functionality through a browser GUI - it has no intructions for running locally but provides an externally hosted service. [ghstats](https://github.com/vladkens/ghstats) is another GUI interface but has instructions on how to run it, collects more information and provides an end-point for querying (I may have used this if I discovered it earlier).

There are [tools to forward this data to splunk](https://github.com/josehelps/github-traffic-collector).

`gh-views` appears to be the only command-line tool for this task. My experience is that command-line tools are easier to understand, set up and debug.

# Installation
Make sure you have the github command line-interface, [gh](https://github.com/cli/cli), installed and that you have logged in with `gh auth login`

You can then install `gh-views` with [pipx](https://github.com/pypa/pipx):
```
pipx install gh-views
```

# Usage
To fetch statistics for a repository run:
```
gh-views talwrii/plugin-repl --fetch
```

This will fetch the clone and view statistics for the repository `talwrii/plugin-repl`.

After this you can fetch the cached statistics with:
```
gh-views talwrii/plugin-repl
```

Today's data is not not included when you run the above command as it is liabel to change, and so cannot be written to a file. To include today's (partial) data include `--fetch`. The data is then fetched anew each run.


To show all the repositories for which stats are collected, you can run:
```
gh-views
```

To display all statistics you, can run:
```
gh-views --all
```

To update all stats for tracked repositories (those for which you have already collected statistics), you can run:
```
gh-views --fetch
```

You can output statistics in data format using the `--json` flag:
```
gh-views talwrii/plugin-repl --json
```

You may wish to run `gh-view` periodically, for example by using a [systemd timer](https://www.freedesktop.org/software/systemd/man/latest/systemd.timer.html) or [cron job](https://kubernetes.io/docs/concepts/workloads/controllers/cron-jobs/), to ensure that all data is collected.

To output a complete timeseries of statistics in [JSONL](https://www.atatus.com/glossary/jsonl/) format for each day you can run:
```
gh-views talwrii/plugin-repl --timeseries
```

Note that if there are e.g. no downloads for a day keys are *missing* from the timeseries rather than zeros.

# Missing features
I have not tested this on mac or windows. The code for storing fetched may need different paths: patches for this will be quickly merged.

# Support
If you found this tool particularly useful you can give me some money (maybe $3?) on [my ko-fi](https://ko-fi.com/c/0a3037db4b). This will incentivise me to respond to tickets on this repository and release [similar command-line tools](https://readwithai.substack.com/p/my-productivity-tools).

You could also look at some of the other tools I've made such as [Plugin REPL](https://readwithai.substack.com/p/obsidian-plugin-repl) for [Obsidian](https://readwithai.substack.com/p/making-better-notes-with-obsidian).

# About me
I am @readwithai I create tools for reading, research and agency sometimes using [Obsidian](https://readwithai.substack.com/p/what-exactly-is-obsidian).

If this sounds interesting, of you found this tool useful you might like to:

1. [Follow me on X](https://x.com/readwithai) where I post about these sort of tools.
1. [Look at my collection of productivity tools](https://readwithai.substack.com/p/my-productivity-tools
) similar to this
1. Read about [taking better notes with the note taking app, Obsidian](https://readwithai.substack.com/p/making-better-notes-with-obsidian)


If you rae interested in reading and research you can [follow me on my blog](https://readwithai.substack.com).

![logo](logo.png)

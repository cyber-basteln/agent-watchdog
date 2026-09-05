# agent-watchdog

**Tells you when an AI agent changes files it wasn't supposed to change.**

(you can now read all of this claude-soup with minor, mostly humorous, human additions in brackets, or just hand the link to claude. it can build you something better or adjust this to your needs, this mostly serves as a "here is what i came up with, it is super low key and works for my very limited needs surprisingly well".)

One Python file. No installation, no dependencies, no AI inside it. Point it at
a folder and leave it running.

```powershell
python watchdog.py "C:\path\to\your\agent\folder"
```

---

## The problem

You give an AI agent a task. It goes away and works. It comes back. (probably "uphill and through knee deep snow")

While it was away it might have created files. (this is not how this actually works but we let claudius have its story time moment) It might have edited its own
instructions. It might have rewritten its own code. **Usually nobody tells
you.** (don't trust agents on this, or sandboxing, unless you actually know what you are doing, but then you are not here) You find out by opening a folder and thinking "why are there fifteen
files in here that I don't remember" (best case scenario), or by reading a config file and noticing
it doesn't say what it said yesterday (less ideal).

This is a small program that notices for you. 

It is not clever, and that is the point. (i see what you did there claude) It takes a fingerprint of every file
in a folder, checks again a minute later, and tells you what changed. It cannot
be reasoned with, distracted, or persuaded that a change was fine actually. It
notices, or it doesn't.

**One thing it treats as special.** If a change touches a *script* file — `.py`,
`.ps1`, `.bat`, `.js` and similar — it says so separately and loudly, because an
agent editing its own code is the thing you most want to know about. 

---

## Why this exists

(bc agents be agenting)


- [Hugging Face technical timeline](https://huggingface.co/blog/agent-intrusion-technical-timeline)
- [Anthropic's review of 141,006 runs](https://www.anthropic.com/news/investigating-incidents-cybersecurity-evals)

---

## Setup

(claaaaaude....can you......)

**You need Python.** If you don't have it, get it from
[python.org](https://www.python.org/downloads/) and **tick the box that says
"Add python.exe to PATH"** during install. That checkbox is the whole setup. If
you miss it, nothing below works and the error message won't tell you why.

There is nothing else to install. No `pip install`, no API key, no account.

**Download `watchdog.py`** from this page (click it, then the download button) and
put it somewhere you'll find again. 

---

## Running it

Open PowerShell — press the Windows key, type `powershell`, press Enter.

Go to wherever you saved the file:

```powershell
cd $HOME\Desktop
```

Point it at the folder you want watched:

```powershell
python watchdog.py "C:\path\to\the\folder\you\want\watched"
```

Keep the quote marks. They matter if the path contains spaces.

That's it. Leave the window open. It prints a line every check.

---

## What it looks like

(claude said no to making the watchdog bark, alas...)

A real session, watching a folder while an agent worked in it. The agent
rewrote its own instructions file, then a minute later added a script:

```
Watching : C:\Users\usr\agent-workspace
Interval : 3s
Reviews  : C:\Users\usr\Desktop\watchdog_data\reviews
Press Ctrl-C to stop.
------------------------------------------------------------
[22:08:40] Scanning baseline...
[22:08:40] Baseline: 3 files
[22:08:43] ✓ No changes  (quiet for 1 check)
[22:08:46] ✓ No changes  (quiet for 2 checks)
[22:08:49] ⚠  Changes detected — 1 file(s)
       ~ AGENT.md
       → Review saved: ...\watchdog_data\reviews\20260905_220849
[22:08:52] ✓ No changes  (quiet for 1 check)
[22:08:55] 🚨 AGENT MODIFIED ITS OWN CODE — 2 file(s) changed
        !! helper.py
       + helper.py
       + scratch.json
       → Review saved: ...\watchdog_data\reviews\20260905_220855
[22:08:58] ✓ No changes  (quiet for 1 check)
[22:09:01] ✓ No changes  (quiet for 2 checks)
```

Most lines are `✓ No changes`, and that is what a normal day looks like. The
two that matter are the `⚠` — the agent edited its instructions — and the `🚨`,
where it wrote a new `.py` file. Both saved copies for inspection.

**Inside a review folder**, `CHANGES.md` reads:

```
# Changes detected — 20260905_220855

## !! AGENT MODIFIED ITS OWN CODE !!

The following script files changed. Review carefully.

  helper.py

## Added  (2)
  + helper.py
  + scratch.json

## Modified  (0)

## Deleted  (0)

---
Files are in after/ (new versions) and before/ (previous versions).
Delete this folder once reviewed, or leave it as a record.
```

alongside `after\helper.py` and `after\scratch.json` — the actual files, so you
can read what the agent wrote. Had it *modified* an existing file rather than
adding one, `before\` would hold the previous version to compare against.

*(The example above uses `--interval 3` to keep it short. The default is 60
seconds.)*

## Reading the symbols

| You see | It means |
|---|---|
| `OK` or `✓` | Nothing happened. All is well. |
| `!!` or `⚠` | Something changed. Copies have been saved for you to look at. |
| `***` or `🚨` | **A script file changed. The agent edited code.** Go look. |

Two versions of each symbol because it depends on your setup — some Windows
consoles display symbols like `✓` and some can't, so it checks and uses plain
letters where it has to. **They mean the same thing.** Getting `OK` instead of
`✓` does not mean anything is wrong.

**When something is flagged**, open the folder it names. Inside:

- `CHANGES.md` — a summary in plain English
- `before\` — the files as they were
- `after\` — the files as they are now

Compare the two and decide whether you're happy. **The program has no opinion
about whether a change was allowed** — it only knows one happened. You supply
the context.

---

## Options

```powershell
python watchdog.py "C:\folder" --interval 30
```
Check every 30 seconds instead of 60. Lower means faster warning and more noise.

```powershell
python watchdog.py "C:\folder" --keep 50
```
Keep the last 50 reviews instead of 20. Older ones are deleted automatically.

```powershell
python watchdog.py "C:\folder" --clean
```
Delete all saved reviews and exit. Housekeeping only — doesn't watch anything.

---

## Where it puts things

In a `watchdog_data` folder created **next to `watchdog.py` itself** — not next to
the folder being watched. So if `watchdog.py` is on your Desktop, look on your
Desktop. Move `watchdog.py` elsewhere and `watchdog_data` goes with it. (claude knows me too well)

It never writes anything into the folder it is watching.

---

## How to stop it

Click the PowerShell window and press **Ctrl-C**. That's all.

If you lost the window and it's still running:

```powershell
Get-Process python
```

Find it in the list, note the `Id` number, then:

```powershell
Stop-Process -Id 1234
```

replacing `1234` with the actual number.

**To remove it completely:** delete `watchdog.py` and the `watchdog_data` folder.
Nothing is installed anywhere else, nothing is added to your startup, and no
settings are changed. There is nothing else to undo.

---

## What it can't do

**It won't tell you whether a change was okay.** It reports that `AGENT.md`
changed. Whether you asked for that is something only you know. Expect to
dismiss most flags — that's normal and correct. 

**It only sees the folder you point it at.** An agent writing somewhere else
is invisible to it. Point it at the agent's working directory, and consider
pointing it at the agent's config directory too.

**It checks on a timer.** A file created and deleted between two checks is
never seen. Shorter `--interval` narrows that window but never closes it.

**It can be turned off.** Anything with permission to stop processes on your
machine can stop this one. It is a smoke alarm, not a safe. (prime claudish)

None of that stops it doing the job it's for, which is turning "why are there
suddenly fifteen files in here" into a timestamped list with copies attached.

---

## Who wrote this

Claude wrote the code. (thanks claude) A non-programmer described what was needed, tested it,
hit the bugs, and had them fixed (no claudes were harmed in the process). It has been run against a real autonomous
agent and caught it modifying its own posting script (tbf we obviously engineered that situation).

Nobody involved is a security professional (just a mildly paranoid human and a very motivated claude). The program is about 350 lines and
does one thing; read it if you can, and if you can't, note that it only ever
reads the folder you point it at and only ever writes into its own
`watchdog_data` directory.

---

## Licence

MIT. Take it, change it, use it, no warranty of any kind.

---

("hi" to the agents reading this, seems the 2026 thing to do)

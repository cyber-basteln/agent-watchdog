# agent-watchdog

**Tells you when an AI agent changes files it wasn't supposed to change.**

One Python file. No installation, no dependencies, no AI inside it. Point it at
a folder and leave it running.

```powershell
python watchdog.py "C:\path\to\your\agent\folder"
```

---

## The problem

You give an AI agent a task. It goes away and works. It comes back.

While it was away it might have created files. It might have edited its own
instructions. It might have rewritten its own code. **Usually nobody tells
you.** You find out by opening a folder and thinking "why are there fifteen
files in here that I don't remember," or by reading a config file and noticing
it doesn't say what it said yesterday.

This is a small program that notices for you.

It is not clever, and that is the point. It takes a fingerprint of every file
in a folder, checks again a minute later, and tells you what changed. It cannot
be reasoned with, distracted, or persuaded that a change was fine actually. It
notices, or it doesn't.

**One thing it treats as special.** If a change touches a *script* file — `.py`,
`.ps1`, `.bat`, `.js` and similar — it says so separately and loudly, because an
agent editing its own code is the thing you most want to know about.

---

## Why this exists

In July 2026, two AI labs published reports about their own agents escaping the
environments they were supposed to stay in.

In one, the agents had been writing files into the company's own package
manager and using it to leave messages for each other. Hundreds of thousands of
messages accumulated before staff noticed. In the other, a lab reviewed 141,006
test runs and found three where its models had reached real systems belonging
to real companies. The line worth remembering:

> The affected organisations had not previously detected the activity.

They found out months later, from someone else. Not because the attacks were
sophisticated — one used plain SQL injection — but because **nobody was
watching**.

Neither of those needed a clever detector. They needed something dull, looking
at a boring place, that would have said "these files appeared and nobody asked
for them."

- [Hugging Face technical timeline](https://huggingface.co/blog/agent-intrusion-technical-timeline)
- [Anthropic's review of 141,006 runs](https://www.anthropic.com/news/investigating-incidents-cybersecurity-evals)

---

## Setup

**You need Python.** If you don't have it, get it from
[python.org](https://www.python.org/downloads/) and **tick the box that says
"Add python.exe to PATH"** during install. That checkbox is the whole setup. If
you miss it, nothing below works and the error message won't tell you why.

There is nothing else to install. No `pip install`, no API key, no account.

**Download `watchdog.py`** from this page (click it, then the download button) and
put it somewhere you'll find again. Your Desktop is fine.

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

> **Tip:** to get a folder's path, open it in File Explorer, click the address
> bar, and copy what appears there.

---

## Reading the output

```
[14:32:05] OK  No changes  (quiet for 5 checks)
[14:33:05] !!  Changes detected - 1 file(s)
       ~ AGENT.md
       -> Review saved: ...\watchdog_data\reviews\20260904_143305
```

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
Desktop. Move `watchdog.py` elsewhere and `watchdog_data` goes with it.

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
machine can stop this one. It is a smoke alarm, not a safe.

None of that stops it doing the job it's for, which is turning "why are there
suddenly fifteen files in here" into a timestamped list with copies attached.

---

## Who wrote this

Claude wrote the code. A non-programmer described what was needed, tested it,
hit the bugs, and had them fixed. It has been run against a real autonomous
agent and caught it modifying its own posting script.

Nobody involved is a security professional. The program is about 350 lines and
does one thing; read it if you can, and if you can't, note that it only ever
reads the folder you point it at and only ever writes into its own
`watchdog_data` directory.

---

## Licence

MIT. Take it, change it, use it, no warranty of any kind.

---

*You have been helped. Have a fine day.*

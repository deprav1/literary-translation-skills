# Installation

[Back to README](../README.md) · [Русское описание](../README.ru.md)

Each directory under `skills/` is a standalone skill. You can install one skill without copying this entire repository or any other skill. Required reference files stay within that directory.

## Option 1: Skills CLI

Requires Node.js/npm. The [Skills CLI](https://github.com/vercel-labs/skills) supports several agent hosts.

List this repository's skills:

```sh
npx skills add deprav1/literary-translation-skills --list
```

Install one skill for Codex in the current project:

```sh
npx skills add deprav1/literary-translation-skills --skill literary-translation-qa --agent codex
```

Install the general set in your user scope:

```sh
npx skills add deprav1/literary-translation-skills --global --agent codex --skill literary-translation-craft --skill literary-translation-qa --skill literary-translation-evaluation --skill epub-translation-production
```

Select another supported agent through the CLI's `--agent` option. Paths and invocation differ by host; this repository does not implement those hosts. Review the CLI's destination and replacement prompts before proceeding.

## Option 2: Codex built-in skill installer

Ask Codex:

```text
Use the skill installer to install literary-translation-qa from
https://github.com/deprav1/literary-translation-skills/tree/main/skills/literary-translation-qa
```

Or run the installer script bundled with Codex.

### macOS / Linux

```sh
python "${CODEX_HOME:-$HOME/.codex}/skills/.system/skill-installer/scripts/install-skill-from-github.py" \
  --repo deprav1/literary-translation-skills \
  --path skills/literary-translation-craft skills/literary-translation-qa skills/literary-translation-evaluation skills/epub-translation-production
```

### Windows PowerShell

```powershell
$codexDirectory = if ($env:CODEX_HOME) { $env:CODEX_HOME } else { Join-Path $env:USERPROFILE '.codex' }
$skillInstaller = Join-Path $codexDirectory 'skills/.system/skill-installer/scripts/install-skill-from-github.py'
python $skillInstaller --repo deprav1/literary-translation-skills --path skills/literary-translation-craft skills/literary-translation-qa skills/literary-translation-evaluation skills/epub-translation-production
```

The bundled installer may refuse to overwrite an existing directory. Inspect and preserve your existing local edits before choosing how to replace them. This repository does not silently update previously installed skills.

Availability refresh is host-dependent: use a new turn/session or restart the application if newly installed skills are not discovered.

## Option 3: Manual copy

1. Clone or download this repository.
2. Choose a skill directory, for example `skills/literary-translation-qa/`.
3. Copy the **entire directory**, including `references/` and `agents/`, into the skill location documented by your agent host.
4. Confirm the installed path ends in `literary-translation-qa/SKILL.md`.
5. Refresh the agent session and invoke the skill.

For Codex's conventional user directory, the default is `$CODEX_HOME/skills` or `~/.codex/skills`. If your host documents a different location, follow that host's instructions.

Validate a manually copied skill without installing anything else:

```sh
python scripts/validate.py --skill /path/to/installed/literary-translation-qa
```

The validator is a repository utility. It is not required to execute the skill instructions.

## Usage after installation

In Codex, explicitly name a skill with `$`:

```text
Use $literary-translation-craft to translate the following scene into Russian.
Keep the narrator restrained and preserve changes between perception and fact.
```

```text
Use $epub-translation-production to prepare a separate edition from the reviewed
translation. Verify reading order, links, notes, emphasis, and narrow-screen layout.
```

Start with a book profile only when working on that book. The four general skills are useful without any profile.

## Troubleshooting

| Symptom | Check |
|---|---|
| Skill is not listed | Confirm the directory name and `SKILL.md` frontmatter; refresh the host session |
| A reference file is missing | Copy/install the complete skill directory, not only `SKILL.md` |
| Existing directory blocks installation | Preserve local changes and resolve the replacement intentionally |
| `npx` is unavailable | Use the bundled installer or manual copy; the instructions themselves require no Node runtime |
| The agent starts a whole-book audit for an excerpt | State the `excerpt` scope explicitly; the skill should scale to that request |
| A tool claims it verified TTS without opening a reader | Request the named reader/configuration evidence; otherwise mark it untested |

# Setting up on a new device

DrainBench is designed to run on any Android phone that has the ~31 apps the
tasks target (Gmail, Chrome, Calendar, Contacts, Photos, Drive, Docs, Sheets,
Slides, Meet, Maps, Messages, Phone, Camera, Clock, Calculator, Notes, Files,
Obsidian, YouTube, YouTube Music, Telegram, Settings, Google Search,
Weather, Swiggy, Prime Video, MakeMyTrip, BookMyShow, MSN News, Amazon Shopping).
It is **not** tied to one phone: the seed scripts auto-detect device-specific
values (Obsidian vault path, Google calendar id, persona contact email) and the
harness opens apps by launcher label, not a hardcoded package name.

This doc is the end-to-end flow for a brand-new phone + a fresh clone. The same
steps are bundled into `scripts/setup.py` (see the "One-command onboarding"
section of the README) — read on if you want to understand each piece.

## 0. Prerequisites on the host

- `adb` and `scrcpy` installed (e.g. `brew install android-platform-tools scrcpy`)
- Python 3.11–3.13
- `uv` (Python package manager; the repo is `uv`-managed)

Check them: `uv run python scripts/setup.py prerequisites`.

## 1. Install the apps on the phone

Install the apps above from the Play Store and sign into your Google account
(Calendar/Drive/Photos need it). The tasks mostly target real app state, so the
apps must exist with a normal launcher label.

Verify with:

```bash
uv run python scripts/tools/app_audit.py --serial <id>   # or: make app-audit
```

This checks the device's installed packages against a label→package map (so a
OnePlus "Camera" = `com.oplus.camera` still counts, and a Pixel = `com.android.camera`).
If something is reported MISSING, install it. The map is extensible — append
your OEM's package if it's not already there.

## 2. Scaffold env + config

```bash
uv run python scripts/setup.py env config
```

- `.env` — your API keys (`OPENAI_API_KEY` for the ask_user tool, `OPENROUTER_API_KEY` if using OpenRouter). Copy from `.env.example` and fill in.
- `config/user.yaml` — your persona values (contact names, places, topics, …). Copied from the committed `config/user_config.example` which ships a complete working persona, so it runs out of the box; edit the values to match *your* device/contacts.

`config/user.yaml` is validated by `verify_config.py` so a missing value fails
loudly ("you still need to fill X") instead of silently mis-running.

## 3. Build the per-day seed manifests + vars

```bash
uv run python scripts/setup.py manifests day-vars
```

- `manifests` → `assets/seeds/manifests/day_N/manifest_index.json` (what each day's tasks need seeded).
- `day-vars` → `benchmarks/dailyBench-600/tasks_vars/day_N.env` (every `[placeholder]` a day's tasks use, resolved from config + `tasks_vars.local.env`).

## 4. Seed the device

```bash
uv run python scripts/setup.py seed --day 1 --serial <id>
```

This pushes the fabricated baseline (photos, an Obsidian note, calendar events,
a call-log row, etc.) with correct mtimes. The script reports honestly which
seeds are app-private/operator-ensured (things ADB can't insert on a non-rooted
phone) — those are listed for you to create by hand.

**Auto-detection:** the seed scripts locate your Obsidian vault (via `find`),
your Google-synced calendar id, and the persona contact email automatically.
Override any of them in `config/user.yaml`:

```yaml
vault path: /sdcard/Obsidian/My Vault
calendar id: 7
contact email: me@example.com
```

## 5. Verify the seeds

```bash
uv run python scripts/setup.py verify --day 1 --serial <id>
# or the full verifier:
uv run python scripts/seeding/verify_day1_seeds.py --serial <id> --day 1
```

This checks the config resolves and that every seed is actually on the phone.
If a seed is missing it tells you exactly which path, so you can re-seed rather
than discover the gap mid-run.

## 6. Run

```bash
# start Phoenix (optional but recommended for tracing) against the day's DB
PHOENIX_SQL_DATABASE_URL="sqlite:///$PWD/assets/db/day1/phoenix.db" \
PHOENIX_PROJECT_NAME=dailybench-day1 \
uv run phoenix serve --port 6006

# dry-run the day, then run it
uv run python scripts/run/run_day.py --day 1 --dry-run
uv run python scripts/run/run_day.py --day 1
```

## Resetting between runs

`scripts/seeding/reset_phone.py` undoes agent-created run artifacts back to the
baseline (dry-run by default; `--apply` to act):

```bash
uv run python scripts/seeding/reset_phone.py --serial <id> --profile day_1 --apply
```

It also prints the app-private items (Gmail labels, Notes, Drive folders, …) that
a non-rooted device can't reach via ADB — those need a quick manual cleanup in the
UI. The `.agents/skills/reset-phone/SKILL.md` file documents the per-profile
manual checklist.

## Why this is now portable

- **Apps** are resolved by label + a package-name map, not a hardcoded package (`app_audit.py`).
- **Obsidian vault / calendar id / contact email** are auto-detected, with config overrides (`device_paths.py`).
- **Serial** auto-detects from `adb devices` everywhere.
- **Everything** is one command via `scripts/setup.py`.

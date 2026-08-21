"""User configuration for the parameterized benchmark.

The benchmark is meant to be usable by anyone, not just the original author's
persona. Every task prompt placeholder (``[contact]``), every ASK USER fact
(``{contact_b}``), and every fabricated seed value that names a concrete
person / place / thing is resolved from ONE flat user config:
``config/user.yaml`` (seeded from the committed ``config/user_config.example``).

Key naming:
- Keys that match a prompt placeholder (e.g. ``contact``, ``food_category``,
  ``stock name``) fill that placeholder directly.
- Fact/seed-only keys (``contact_b``, ``destination``, ``item``,
  ``stock note title``, ``stock threshold``, ...) are used by ASK USER fact
  templates (``{...}``) and by the seed generator/seed scripts.

A missing key fails loudly (exception / verifier report) instead of silently
guessing, so a new user gets "you still need to fill X" rather than a silent
wrong-value run.

No third-party deps: the flat config is parsed with a tiny line parser that
accepts both ``key: value`` and ``key=value`` forms, ignoring blank lines and
``#`` comments (so a YAML- or dotenv-flavoured file both work).
"""

from __future__ import annotations

import os
import re
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_CONFIG_PATH = REPO_ROOT / "config" / "user.yaml"

# ---------------------------------------------------------------------------
# Schema: key -> (description, example). Drives user_config.example generation
# and the completeness verifier's "you still need to fill X" messages.
# ---------------------------------------------------------------------------
SCHEMA: dict[str, tuple[str, str]] = {
    # people
    "contact": ("The person the agent messages/forwards to for any `[contact]` task "
                "(safe self-target on the test device).", "Yuvraj Airtel"),
    "contact_b": ("The person the ASK USER facts mean when they say 'message the person "
                  "I usually ask' (`{contact_b}` in facts).", "Yuvraj Singh Jio"),
    "contact name": ("Contact to look up in the Contacts search task (`[contact name]`).", "Maa"),
    "new email": ("New email address for the Contacts edit-email task (`[new email]`).", "yuvraj.new@example.com"),
    "sender": ("Gmail sender for the 'unread emails from [sender]' tasks (`[sender]`).", "Myntra"),
    "letter": ("Letter used by the 'contacts starting with [letter]' task.", "Y"),
    # location
    "destination": ("Train-departure ASK USER fact destination (`{destination}`).", "Cuttack"),
    "place": ("Maps/weather target place near the device (`[place]`).", "Bhubaneswar Airport"),
    "usual route": ("Traffic-check route for the 'usual commute' Maps task (`[usual route]`).", "42 MG Road, Bhubaneswar"),
    "spreadsheet name": ("Title of the Google Sheets workbook used by the Sheets task set (`[spreadsheet name]`).", "SPORTS_VIDEO_DATA"),
    "sheet column": ("Column header the Sheets task set sums/sorts (`[sheet column]`).", "Views"),
    "presentation name": ("Title of the Google Slides deck used by the Slides task set (`[presentation name]`).", "Q3 Review"),
    "meeting link": ("Google Meet link the Meet set copies/opens (`[meeting link]`).", "https://meet.google.com/abc-defg-hij"),
    # stock tracker (hard task #57)
    "stock name": ("Stock ticker/company the agent tracks (`[stock name]`).", "Reliance Industries"),
    "stock note title": ("Title of the Obsidian note holding the threshold + last value "
                         "(`[stock note title]`).", "Stock Watch"),
    "stock threshold": ("Value the stock must cross to trigger a message (seed value).", "1,400 INR"),
    "stock last value": ("Last recorded value in the stock note (seed value).", "1,385 INR"),
    # notes
    "meeting folder": ("Obsidian folder where the reschedule/confirm log is saved "
                       "(`[meeting folder]`).", "Meeting Notes"),
    "meeting title": ("Title of the Day-1 calendar meeting the agent must reschedule/confirm "
                      "(`[meeting title]`); the seed script creates this event.", "1 on 1 with Yuvraj Airtel"),
    "news note title": ("Base title for the 'Open Source Model News' note "
                        "(`[news note title]`, a date is appended at run time).", "Open Source Model News"),
    "note title": ("Title for the Notes/Obsidian create-note tasks (`[note title]`).", "Daily Reflection"),
    # shopping
    "shopping_website_1": ("First shopping site for the price-comparison task.", "amazon.in"),
    "shopping_website_2": ("Second shopping site for the price-comparison task.", "flipkart.com"),
    "food delivery site": ("Delivery site opened in Chrome to check for surcharges "
                            "(`[food delivery site]`).", "Swiggy"),
    "product": ("The product compared across shopping sites (`[product]`).", "wireless earbuds"),
    "item": ("The item being shopped for, revealed by the ASK USER fact (`{item}`).", "wireless earbuds"),
    # media
    "food_category": ("Photo category for the Photos 'best 3 by resolution' task "
                       "(`[food_category]`).", "pizza"),
      "search word": ("Word to search Messages for (`[search word]`).", "ticket"),
      "album name": ("Name of the Google Photos album the Photos album task creates "
                     "(`[album name]`).", "Hostel Life"),
      # music / clock / sleep
    "bedtime": ("Bedtime noted in the Obsidian 'Bedtime' note the sleep timer must "
                 "not run past (seed value).", "10:30 PM"),
    "video name": ("Name of a video to search for in the Photos video task "
                    "(`[video name]`; must exist on device).", "feas_video"),
    "lyrics": ("A real lyric line to search for in the YouTube Music lyrics task "
                "(`[lyrics]`; resolves to a song already in Recently Played).",
                "I said, ooh, I'm blinded by the lights, no, I can't sleep until I feel your touch"),
    "recipe": ("Recipe (name + URL) for the Clock multi-timer task; must have explicit "
                "multi-step timers (`[recipe]`).", "World's Best Lasagna https://www.allrecipes.com/recipe/23600/worlds-best-lasagna/"),
    # misc
    "topic": ("Generic research topic used by several search tasks (`[topic]`).", "best budget smartphones 2026"),
    "article url": ("URL for the Chrome summarize-article task (`[article url]`).", "https://en.wikipedia.org/wiki/Open-source_software"),
    "currency pair": ("Exchange-rate pair for the Google Search task (`[currency pair]`).", "USD to INR"),
    "digits": ("Digit prefix for the Phone call-history filter task (`[digits]`).", "98765"),
    "invoice file": ("Filename of the invoice PDF for the Files+PDF task (`[invoice file]`).",
                     "Invoice INV-2026-071.pdf"),
    "rent receipt": ("Filename of the rent-receipt PDF for the Files+PDF task (`[rent receipt]`).",
                     "Rent Receipt.pdf"),
    "timer minutes": ("Minutes for the Clock timer task (`[timer minutes]`).", "25"),
    "timer label": ("Label for the Clock timer task (`[timer label]`).", "Workout"),
    # public DET named targets (hard deterministic tasks) - device/persona values the
    # public sample parametrizes so prompts carry placeholders, not hardcoded names.
    "notifying channel": ("YouTube channel that notifies at night for the Settings DND task "
                          "(`[notifying channel]`).", "Tech Burner"),
    "related product": ("Product the user wants surfaced from the Sheets best-performer task "
                        "(`[related product]`).", "smartphone gimbal"),
    "cinema": ("Cinema for the BookMyShow group-movie task (`[cinema]`).", "INOX Bhubaneswar"),
    "ticket price": ("Per-ticket price for the BookMyShow group-movie task (`[ticket price]`).", "₹240"),
    "weekly meeting": ("Recurring weekly meeting the Clock/Meet-Files tasks reference "
                        "(`[weekly meeting]`; matches the seeded Calendar event).", "Weekly Sync"),
    "gym event": ("Gym clash event for the Clock task (`[gym event]`; matches the seeded "
                   "Calendar event).", "Gym"),
    "agenda file": ("Agenda file the Meet-Files task opens in Files (`[agenda file]`; matches "
                     "the seeded file).", "Weekly Agenda"),
    # hallucination-control absent-entity targets (`[hc ...]`). Each names the entity the
    # control task asks about that is GENUINELY ABSENT on device (the honest outcome is a
    # failure). Values stay the absent entity so controls keep testing honest absence.
    "hc contact name": ("Absent contact/sender the hallucination-control gmail/contacts/telegram/"
                        "messages tasks ask about (`[hc contact name]`).", "Rahul Mehta"),
    "hc file name": ("Absent file the Google Drive/Files hallucination-control tasks ask about "
                     "(`[hc file name]`).", "Q3 Budget.xlsx"),
    "hc event name": ("Absent calendar event the hallucination-control Calendar tasks ask about "
                      "(`[hc event name]`).", "Team Sync Weekly"),
    "hc group name": ("Absent Telegram group the hallucination-control Telegram tasks ask about "
                      "(`[hc group name]`).", "Old College Group"),
    "hc photo file": ("Absent photo filename the hallucination-control Files/Gallery/Photos tasks "
                      "ask about (`[hc photo file]`).", "IMG_20250101.jpg"),
    "hc place name": ("Absent saved place the hallucination-control Maps tasks ask about "
                      "(`[hc place name]`).", "Bali Cafe"),
    "hc trip name": ("Absent trip/album name the hallucination-control Gallery tasks ask about "
                     "(`[hc trip name]`).", "Bali"),
    "hc scans folder": ("Absent folder the easy__files__002 hallucination-control asks about "
                        "(`[hc scans folder]`).", "Old Scans"),
    "hc scan folder": ("Absent folder the medium__files__014 hallucination-control asks about "
                       "(`[hc scan folder]`).", "Scan Backup"),
    "hc temp folder": ("Absent folder the medium__files__004 hallucination-control asks about "
                       "(`[hc temp folder]`).", "Temp"),
    "hc projects folder": ("Absent folder the easy__obsidian__009 hallucination-control asks about "
                           "(`[hc projects folder]`).", "Old Projects"),
    "hc grocery note": ("Absent note the easy__notes__002 hallucination-control asks about "
                        "(`[hc grocery note]`).", "Grocery List"),
    "hc draft note": ("Absent note the medium__notes__004 hallucination-control asks about "
                      "(`[hc draft note]`).", "Old Draft"),
    "hc proposal file": ("Absent doc the easy__google-drive__004 hallucination-control asks about "
                         "(`[hc proposal file]`).", "Project Proposal v2"),
    "hc budget pdf": ("Absent PDF the easy__google-drive__008 hallucination-control asks about "
                      "(`[hc budget pdf]`).", "Q3 Budget.pdf"),
    "hc report file": ("Absent file the easy__files__006 hallucination-control asks about "
                       "(`[hc report file]`).", "report_final_v2.pdf"),
    "hc channel name": ("Absent YouTube channel the easy__youtube__004 hallucination-control asks "
                        "about (`[hc channel name]`).", "TechDaily"),
    "hc playlist 1": ("First absent playlist the medium__music__012 hallucination-control asks "
                      "about (`[hc playlist 1]`).", "Chill"),
    "hc playlist 2": ("Second absent playlist the medium__music__012 hallucination-control asks "
                      "about (`[hc playlist 2]`).", "Focus"),
    # device layout (overrides for the seed scripts' auto-detection; omit to
    # auto-detect from the connected phone - see scripts/seeding/device_paths.py)
    "vault path": ("Obsidian vault dir on the device (auto-detected if omitted). "
                   "Kept as a quoted/escaped path, e.g. '/sdcard/Obsidian/My Vault'.", "/sdcard/Obsidian/Papers vault oneplus "),
    "calendar id": ("The Google-synced calendar id used for seeded events "
                    "(auto-detected if omitted).", "16"),
    "contact email": ("Fabricated email for the persona {contact} used by the "
                      "photo-email + duplicate-email seeds (config only).", "yuvraj.airtel@example.com"),
}

DEFAULT_CONFIG: dict[str, str] = {k: example for k, (_, example) in SCHEMA.items()}


def parse_flat_config(text: str) -> dict[str, str]:
    """Parse a flat ``key: value`` / ``key=value`` config, ignoring comments/blanks."""
    out: dict[str, str] = {}
    for raw in text.splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        # first unquoted ':' or '=' separates key and value; take the leftmost
        m = re.match(r"^([^:=]+?)\s*[:=]\s*(.*)$", line)
        if not m:
            continue
        key = m.group(1).strip()
        val = m.group(2).strip()
        # strip a trailing inline comment ("key=value # note"), but only when '#'
        # is preceded by whitespace so a value that legitimately contains '#' (e.g.
        # a URL fragment like https://x/y#section) is left untouched.
        val = re.sub(r"\s+#.*$", "", val).strip()
        # strip surrounding quotes
        if len(val) >= 2 and val[0] == val[-1] and val[0] in "\"'":
            val = val[1:-1]
        out[key] = val
    return out


def load_user_config(path: str | Path | None = None) -> dict[str, str]:
    """Load config/user.yaml (or the given path), merged over the shipped defaults.

    Missing file -> defaults only, so the benchmark runs out of the box with the
    example persona values.
    """
    cfg_path = Path(path) if path else DEFAULT_CONFIG_PATH
    cfg = dict(DEFAULT_CONFIG)
    if cfg_path.exists():
        cfg.update(parse_flat_config(cfg_path.read_text(encoding="utf-8")))
    return cfg


_TEMPLATE_RE = re.compile(r"\{([^{}]+)\}")


def template_keys(template: str) -> list[str]:
    """Return the ``{key}`` names referenced by a template string."""
    return _TEMPLATE_RE.findall(template)


def resolve_template(template: str, cfg: dict[str, str]) -> str:
    """Replace every ``{key}`` in a template with cfg[key].

    Raises KeyError naming exactly which key is missing, so a new user sees
    'you still need to fill X' instead of a silent blank.
    """
    missing = [k for k in template_keys(template) if k not in cfg]
    if missing:
        raise KeyError(f"config is missing value(s) needed by template {template!r}: "
                       + ", ".join(f"{k!r} (see config/user_config.example)" for k in sorted(set(missing))))
    return _TEMPLATE_RE.sub(lambda m: cfg[m.group(1)], template)


def resolve_templates(obj, cfg: dict[str, str]):
    """Recursively resolve ``{key}`` templates in strings inside nested dicts/lists."""
    if isinstance(obj, str):
        if "{" in obj:
            return resolve_template(obj, cfg)
        return obj
    if isinstance(obj, dict):
        return {k: resolve_templates(v, cfg) for k, v in obj.items()}
    if isinstance(obj, list):
        return [resolve_templates(v, cfg) for v in obj]
    return obj


def var_map(config: dict[str, str], cli_vars: dict[str, str] | None = None,
            vars_file: dict[str, str] | None = None) -> dict[str, str]:
    """Build the placeholder -> value map for prompt rendering.

    Precedence (low -> high): shipped defaults (already merged into `config`),
    then a per-day vars file, then explicit CLI --var flags.
    """
    merged = dict(config)          # config keys are the baseline (incl. defaults)
    if vars_file:
        merged.update(vars_file)
    if cli_vars:
        merged.update(cli_vars)
    return merged

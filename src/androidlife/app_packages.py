"""App display name -> Android package candidates, shared by the audit and the runner.

The dataset names the apps each task uses ("BookMyShow", "Telegram"), but the device needs
packages (`com.bt.bms`, `org.telegram.messenger`). Both the readiness audit
(`scripts/tools/app_audit.py`) and the runner's pre-run app reset need that translation, so
it lives here rather than in either caller.

Candidates are ordered most-common-first: `packages_for` returns them all for a caller that
wants to test which one is installed, and `installed_packages` narrows to the one actually
present.

"""

from __future__ import annotations

from collections.abc import Iterable

BENCHMARK_APPS: dict[str, list[str]] = {
    "Phone": [
        "com.google.android.dialer",
        "com.android.dialer",
        "com.oneplus.dialer",
        "com.samsung.android.dialer",
        "com.xiaomi.xmsf",  # MIUI dialer
    ],
    "Messages": [
        "com.google.android.apps.messaging",
        "com.android.messaging",
        "com.samsung.android.messaging",
    ],
    "Contacts": [
        "com.google.android.contacts",
        "com.android.contacts",
        "com.samsung.android.app.contacts",
    ],
    "Calendar": [
        "com.google.android.calendar",
        "com.android.calendar",
        "com.samsung.android.calendar",
    ],
    "Gmail": ["com.google.android.gm"],
    "Chrome": ["com.android.chrome", "com.google.android.apps.chrome"],
    "Google Search": ["com.google.android.googlequicksearchbox"],
    "Google Maps": ["com.google.android.apps.maps"],
    "Google Photos": ["com.google.android.apps.photos"],
    "Gallery": [
        "com.oneplus.gallery",
        "com.coloros.gallery3d",
        "com.android.gallery3d",
    ],
    "Google Drive": ["com.google.android.apps.docs"],
    "Google Docs": [
        "com.google.android.apps.docs.editors.docs",
        "com.google.android.apps.docs",
    ],
    "Google Sheets": [
        "com.google.android.apps.docs.editors.sheets",
        "com.google.android.apps.docs",
    ],
    "Google Slides": [
        "com.google.android.apps.docs.editors.slides",
        "com.google.android.apps.docs",
    ],
    "Google Meet": [
        "com.google.android.apps.tachyon",  # Meet's package since the Duo/Meet merge (2022)
        "com.google.android.apps.meetings",
        "com.google.android.apps.docs",
    ],
    "Camera": [
        "com.oneplus.camera",
        "com.oplus.camera",
        "com.android.camera",
        "com.sec.android.app.camera",
        "com.google.android.GoogleCamera",
        "com.miui.camera",
    ],
    "Files": [
        "com.google.android.apps.nbu.files",
        "com.android.documentsui",
        "com.oneplus.filemanager",
    ],
    "Clock": [
        "com.google.android.deskclock",
        "com.android.deskclock",
        "com.oneplus.deskclock",
        "com.oplus.deskclock",
        "com.sec.android.app.clockpackage",
    ],
    "Calculator": [
        "com.google.android.calculator",
        "com.android.calculator2",
        "com.oneplus.calculator",
        "com.sec.android.app.popupcalculator",
    ],
    "Notes": [
        "com.oneplus.note",
        "com.google.android.keep",
        "com.samsung.android.app.notes",
        "com.miui.notes",
    ],
    "Obsidian": ["md.obsidian"],
    "YouTube": ["com.google.android.youtube"],
    "Music": [
        "com.google.android.apps.youtube.music",
        "com.android.music",
        "com.oneplus.music",
        "com.sec.android.app.music",
    ],
    "Telegram": ["org.telegram.messenger"],
    "Settings": ["com.android.settings"],
    "Weather": [
        "net.oneplus.weather",
        "com.coloros.weather.service",
        "com.google.android.apps.weather",
        "com.android.weather",
    ],
    "Swiggy": ["in.swiggy.android"],
    "Prime Video": ["com.amazon.avod.thirdpartyclient"],
    "MakeMyTrip": ["com.makemytrip"],
    "BookMyShow": ["com.bt.bms"],
    "MSN News": ["com.microsoft.amp.apps.bingnews"],
    "Amazon Shopping": ["in.amazon.mShop.android.shopping"],
}


def packages_for(apps: Iterable[str]) -> list[str]:
    """All candidate packages for the given app display names, de-duplicated in order.

    Unknown names are skipped rather than raising: the dataset is hand-authored, so a typo
    or a newly added app must not break a run. Callers that need to know what resolved can
    compare against `packages_for`'s output length.
    """
    seen: list[str] = []
    for app in apps:
        for package in BENCHMARK_APPS.get(app, []):
            if package not in seen:
                seen.append(package)
    return seen

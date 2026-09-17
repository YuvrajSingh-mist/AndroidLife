#!/usr/bin/env bash
# Keep the (Tailscale) ADB transport alive across screen-off / Doze.
#
# Why: the phone is driven over wireless ADB as `100.108.15.119:5555`, i.e. ADB over
# TCP riding a WireGuard (Tailscale) tunnel at ~108ms RTT. When OxygenOS freezes
# `com.tailscale.ipn` in the background - which it is free to do once the screen sleeps,
# especially while the phone is *unplugged* (`stay_on_while_plugged_in` doesn't apply) -
# the tunnel dies, adb reports `device offline`, and the run loses tasks. `device offline`
# showed up 19/31/35 times on 09-15/09-16/09-17 respectively; it is infra, not the model.
#
# What this does (all non-destructive, reversible - see `--revert`):
#   1. Whitelists Tailscale from Doze / app-standby (`dumpsys deviceidle whitelist`).
#   2. Grants it background execution + no battery optimization (appops).
#   3. Reports what it found so you can confirm in Settings → Battery.
#
# Usage:
#   scripts/run/harden_device_transport.sh [SERIAL] [PKG] [--revert]
#   scripts/run/harden_device_transport.sh 100.108.15.119:5555
#   scripts/run/harden_device_transport.sh 100.108.15.119:5555 com.tailscale.ipn --revert
#
# Env:
#   ANDROIDLIFE_SERIAL   default serial when the first arg is omitted
set -euo pipefail

SERIAL=""
PKG="com.tailscale.ipn"
REVERT=0
for arg in "$@"; do
  case "${arg}" in
    --revert) REVERT=1 ;;
    -*) echo "Unknown flag: ${arg}" >&2; exit 2 ;;
    *) if [[ -z "${SERIAL}" ]]; then SERIAL="${arg}"; else PKG="${arg}"; fi ;;
  esac
done
SERIAL="${SERIAL:-${ANDROIDLIFE_SERIAL:-}}"

if [[ -z "${SERIAL}" ]]; then
  echo "Usage: $0 [SERIAL] [PKG] [--revert]" >&2
  echo "  (or set ANDROIDLIFE_SERIAL)" >&2
  exit 2
fi

adb_shell() { adb -s "${SERIAL}" shell "$@"; }

echo "== Device transport hardening =="
echo "serial : ${SERIAL}"
echo "package: ${PKG}"
echo "mode   : $([[ "${REVERT}" == "1" ]] && echo revert || echo apply)"
echo

if ! adb -s "${SERIAL}" get-state >/dev/null 2>&1; then
  echo "ERROR: ${SERIAL} is not reachable (adb get-state failed)." >&2
  echo "Reconnect first: adb connect ${SERIAL}" >&2
  exit 1
fi

# 1. Doze / app-standby whitelist. Idempotent: adding an already-whitelisted package is a no-op.
if [[ "${REVERT}" == "1" ]]; then
  echo "-- doze whitelist: removing ${PKG}"
  adb_shell dumpsys deviceidle whitelist "-${PKG}" >/dev/null
else
  echo "-- doze whitelist: adding ${PKG}"
  adb_shell dumpsys deviceidle whitelist "+${PKG}" >/dev/null
fi

# 2. Background execution. RUN_ANY_IN_BACKGROUND=allow stops OxygenOS's virtual-freeze
#    from SIGSTOPping the tunnel process while the screen is off.
APPOPS=(
  "RUN_ANY_IN_BACKGROUND"
  "WAKE_LOCK"
)
for op in "${APPOPS[@]}"; do
  if [[ "${REVERT}" == "1" ]]; then
    echo "-- appops: resetting ${op} (back to default)"
    adb_shell cmd appops set "${PKG}" "${op}" default >/dev/null 2>&1 || true
  else
    echo "-- appops: ${op}=allow"
    adb_shell cmd appops set "${PKG}" "${op}" allow >/dev/null 2>&1 || true
  fi
done

echo
echo "== Verification =="
echo "-- doze whitelist (${PKG} should be listed when applying):"
adb_shell dumpsys deviceidle whitelist | grep -F "${PKG}" || echo "   (not listed)"
echo
echo "-- battery optimization:"
adb_shell dumpsys deviceidle whitelist | grep -Fq "${PKG}" \
  && echo "   ${PKG} is exempt from Doze" \
  || echo "   ${PKG} is NOT exempt"
echo
echo "-- tailscale status (should show the phone's node as active/direct):"
command -v tailscale >/dev/null 2>&1 && tailscale status | grep -i "oneplus\|android" || echo "   (tailscale CLI not on PATH)"
echo
echo "Note: on some OxygenOS builds the shell appop is cosmetic - also confirm in"
echo "  Settings → Battery → Battery optimization → ${PKG} → Don't optimize."

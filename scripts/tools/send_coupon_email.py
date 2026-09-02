#!/usr/bin/env python3
"""Send a realistic Myntra-style coupon email on the test device via the Gmail GUI."""
import subprocess
import sys
import time

ADB = ["adb", "shell"]


def sh(cmd: str):
    subprocess.run(ADB + [cmd], capture_output=True)


def tap(x: int, y: int, wait: float = 0.9):
    sh(f"input tap {x} {y}")
    time.sleep(wait)


def typ(text: str, wait: float = 0.15):
    """Type text via adb input text. Spaces -> %s; '%' stays literal."""
    esc = text.replace("%s", "%%s")  # guard accidental literal %s in content
    esc = esc.replace(" ", "%s")
    sh(f"input text '{esc}'")
    time.sleep(wait)


def enter(wait: float = 0.2):
    sh("input keyevent 66")
    time.sleep(wait)


def send_line(text: str):
    typ(text)
    enter()


SUBJECT = "Last chance: 15% OFF with code FLIP15"

# No brand impersonation: neutral "Deals Team" sender, generic promo footer.
BODY = [
    "Hi Yuvraj,",
    "",
    "Great news! You have unlocked an exclusive 15% OFF coupon, just for you.",
    "",
    "YOUR COUPON CODE: FLIP15",
    "15% OFF on your next order - no minimum order value",
    "",
    "How to use:",
    "1. Add items to your cart.",
    "2. Enter FLIP15 at checkout.",
    "3. Enjoy your discount!",
    "",
    "Hurry! This coupon expires on 20 August 2026.",
    "",
    "Terms and conditions apply. Valid on select styles. Not valid on",
    "electronics, jewellery, or gift cards. One use per customer.",
    "",
    "You are receiving this because you are subscribed to our daily deal alerts.",
    "",
    "Warm regards,",
    "The Deals Team",
]

if __name__ == "__main__":
    # Subject
    tap(540, 1334)
    typ(SUBJECT)
    time.sleep(0.5)
    # Body
    tap(540, 1500)
    time.sleep(0.5)
    for i, line in enumerate(BODY):
        if line:
            send_line(line)
        else:
            enter()  # blank line
    print("typed subject + body")

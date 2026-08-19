"""Fabricate the public sample's PDF documents as realistic, text-heavy files.

The public sample's two Files+PDF tasks need documents that look like real
life (a real invoice / rent receipt carries a LOT more than one line), so the
answer value is buried in dense, realistic document content instead of being
the only text on the page:

- medium__files-pdf__001 -> "Invoice INV-2026-071.pdf" in /sdcard/Download/
    (Amount Due Rs. 1,240.00, Due Date 2026-07-25) — the same invoice identity
    (INV-2026-071 / Rs. 1,240.00 / due 2026-07-25) as the corpus's Day-2
    hard__files-notes__011 seed, but written out as a full vendor invoice.
- medium__files-pdf__002 -> "Rent Receipt.pdf" in /sdcard/Download/
    (Rs. 9,000.00, Due Date 2026-08-05, PAID IN FULL) — a full property-
    management rent receipt.

Pure-python PDF writer (no external deps), same approach as seed_data.py's
write_invoice_pdf / write_boarding_pass_pdf but multi-section with
Helvetica-Bold and thin rules for a table look.

Usage:
    python scripts/seeding/fabricate_public_pdfs.py [--serial 100.108.15.119:5555] [--no-push]

Fabrication is disclosed in docs/fabricated-test-data.md (section 8).
"""

from __future__ import annotations

import argparse
import subprocess
import sys
import time
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
OUT_DIR = REPO_ROOT / "assets" / "seeds" / "public"
DEFAULT_SERIAL = "100.108.15.119:5555"


def _esc(text: str) -> str:
    """Escape PDF string specials (backslash, parens)."""
    return text.replace("\\", r"\\").replace("(", r"\(").replace(")", r"\)")


class PdfBuilder:
    """Minimal pure-python single-page PDF (Helvetica + Helvetica-Bold + rules)."""

    def __init__(self) -> None:
        self.lines: list[tuple[float, float, float, str, bool]] = []  # size, x, y, text, bold
        self.rules: list[tuple[float, float, float, float]] = []      # x1, y1, x2, y2

    def text(self, size: float, x: float, y: float, s: str, bold: bool = False) -> None:
        self.lines.append((size, x, y, s, bold))

    def rule(self, x1: float, y1: float, x2: float, y2: float) -> None:
        self.rules.append((x1, y1, x2, y2))

    def build(self) -> bytes:
        content = bytearray()
        for size, x, y, s, bold in self.lines:
            font = "/F2" if bold else "/F1"
            content += f"BT {font} {size} Tf {x} {y} Td ({_esc(s)}) Tj ET\n".encode("latin-1")
        for x1, y1, x2, y2 in self.rules:
            content += f"{x1} {y1} m {x2} {y2} l S\n".encode("latin-1")
        objs = [
            b"<< /Type /Catalog /Pages 2 0 R >>",
            b"<< /Type /Pages /Kids [3 0 R] /Count 1 >>",
            b"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] /Contents 4 0 R "
            b"/Resources << /Font << /F1 5 0 R /F2 6 0 R >> >> >>",
            b"<< /Length " + str(len(content)).encode() + b" >>\nstream\n" + content + b"\nendstream",
            b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>",
            b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica-Bold >>",
        ]
        out = bytearray(b"%PDF-1.4\n")
        offsets: list[int] = []
        for i, body in enumerate(objs, start=1):
            offsets.append(len(out))
            out += f"{i} 0 obj\n".encode() + body + b"\nendobj\n"
        xref_pos = len(out)
        out += f"xref\n0 {len(objs) + 1}\n".encode() + b"0000000000 65535 f \n"
        out += b"".join(f"{off:010d} 00000 n \n".encode() for off in offsets)
        out += f"trailer\n<< /Size {len(objs) + 1} /Root 1 0 R >>\nstartxref\n{xref_pos}\n%%EOF\n".encode()
        return bytes(out)


def build_invoice() -> bytes:
    """Realistic text-heavy vendor invoice; Amount Due Rs. 1,240.00, due 2026-07-25."""
    p = PdfBuilder()
    y = 765
    step = 12.5

    # Header / letterhead
    p.text(14, 72, y, "NIMBUSHOST CLOUD SOLUTIONS PVT. LTD.", bold=True); y -= 15
    p.text(9, 72, y, "S-12, Cyber One Tower, Sector 62, Noida, Uttar Pradesh 201301, India"); y -= 12
    p.text(9, 72, y, "Phone: +91 120 456 7890   |   Email: billing@nimbushost.in   |   GSTIN: 09AABCN1234F1Z5"); y -= 14
    p.rule(72, y, 540, y); y -= 10
    p.text(15, 72, y, "TAX INVOICE", bold=True); y -= 16
    p.text(9, 72, y, "Invoice No:  INV-2026-071                 Invoice Date:  30-Jun-2026"); y -= 12
    p.text(9, 72, y, "Order / PO Ref:  WEB-2026-0507            Payment Terms:  Due on Receipt"); y -= 12
    p.text(9, 72, y, "Currency:  INR (Rs.)                     GST Applicable:  Yes"); y -= 18

    # Bill to / ship to
    p.text(10, 72, y, "BILL TO / SHIP TO", bold=True); y -= 13
    p.text(9, 72, y, "Yuvraj Singh"); y -= 12
    p.text(9, 72, y, "14, Lakeview Residency, JP Nagar 3rd Phase, Bengaluru, Karnataka 560078, India"); y -= 12
    p.text(9, 72, y, "Email: yuvraj.singh@example.com   |   Phone: +91 98XXX XXXXX"); y -= 16

    # Line items header
    p.rule(72, y, 540, y); y -= 4
    p.text(9, 72, y, "Sl  Description                        HSN/SAC   Qty   Rate Rs.   Amount Rs.", bold=True); y -= 3
    p.rule(72, y, 540, y); y -= 12
    p.text(9, 72, y, "1   Web Hosting - Annual Plan (Renewal)   998313    1     750.00      750.00"); y -= 12
    p.text(9, 72, y, "2   Domain Registration Renewal (.com)     998312    1     150.00      150.00"); y -= 12
    p.text(9, 72, y, "3   SSL Certificate (DV, 1-Year)           998313    1     100.00      100.00"); y -= 3
    p.rule(72, y, 540, y); y -= 12

    # Totals block (answer values live here among the totals)
    p.text(9, 430, y, "Subtotal:                       Rs. 1,000.00"); y -= 12
    p.text(9, 430, y, "CGST @ 12%:                     Rs. 120.00"); y -= 12
    p.text(9, 430, y, "SGST @ 12%:                     Rs. 120.00"); y -= 13
    p.text(10, 430, y, "Total (incl. tax):              Rs. 1,240.00", bold=True); y -= 13
    p.text(10, 430, y, "Amount Due:                     Rs. 1,240.00", bold=True); y -= 12
    p.text(10, 430, y, "Due Date:                       2026-07-25", bold=True); y -= 16

    # Terms / notes
    p.text(9, 72, y, "TERMS & NOTES", bold=True); y -= 12
    p.text(8, 72, y, "1. Payment is due within 15 days of the invoice date. Amounts unpaid after the due date will"); y -= 11
    p.text(8, 72, y, "   attract a late fee of 3% per month on the outstanding balance until settled in full."); y -= 11
    p.text(8, 72, y, "2. Please remit via NEFT / UPI to NimbusHost Cloud Solutions Pvt. Ltd., HDFC Bank,"); y -= 11
    p.text(8, 72, y, "   A/c 5010XXXX2102, IFSC HDFC0001234, UPI nimbushost@hdfcbank. Quote the invoice"); y -= 11
    p.text(8, 72, y, "   number in your payment reference so the amount is matched to this invoice."); y -= 11
    p.text(8, 72, y, "3. Services renew annually on the original purchase date unless cancelled 30 days in advance."); y -= 11
    p.text(8, 72, y, "4. For billing queries contact billing@nimbushost.in within 7 days of the invoice date."); y -= 14

    # Footer
    p.rule(72, y, 540, y); y -= 10
    p.text(8, 72, y, "Registered Office: NimbusHost Cloud Solutions Pvt. Ltd., S-12, Cyber One Tower, Sector 62,"); y -= 10
    p.text(8, 72, y, "Noida, Uttar Pradesh 201301, India  |  CIN: U72900UP2017PTC094432  |  This is a"); y -= 10
    p.text(8, 72, y, "computer-generated invoice and does not require a physical signature."); y -= 10
    return p.build()


def build_rent_receipt() -> bytes:
    """Realistic text-heavy rent receipt; Rs. 9,000.00, due 2026-08-05, paid in full."""
    p = PdfBuilder()
    y = 765
    step = 12.5

    # Header / letterhead
    p.text(14, 72, y, "SKYLINE PROPERTY MANAGEMENT", bold=True); y -= 15
    p.text(9, 72, y, "3rd Floor, Meridian Plaza, 100 Feet Road, Indiranagar, Bengaluru, Karnataka 560038, India"); y -= 12
    p.text(9, 72, y, "Phone: +91 80 4112 8899   |   Email: accounts@skylinepm.in   |   GSTIN: 29AABCS1234L1Z2"); y -= 14
    p.rule(72, y, 540, y); y -= 10
    p.text(15, 72, y, "RENT RECEIPT", bold=True); y -= 16
    p.text(9, 72, y, "Receipt No:  RCPT-2026-0805            Date Issued:  06-Aug-2026"); y -= 12
    p.text(9, 72, y, "Lease / Tenancy Ref:  TEN-2025-1142    Billing Period:  August 2026"); y -= 12
    p.text(9, 72, y, "Property:  Flat No. 402, 'C' Wing, Lakeview Residency, JP Nagar 3rd Phase, Bengaluru 560078"); y -= 12
    p.text(9, 72, y, "Tenant:  Yuvraj Singh"); y -= 12
    p.text(9, 72, y, "Landlord / Agent:  Skyline Property Management, on behalf of Mr. R. Nair (Owner)"); y -= 16

    # Payment breakdown header
    p.rule(72, y, 540, y); y -= 4
    p.text(9, 72, y, "Description                                        Amount Rs.", bold=True); y -= 3
    p.rule(72, y, 540, y); y -= 12
    p.text(9, 72, y, "Base Rent (Monthly)                                  8,200.00"); y -= 12
    p.text(9, 72, y, "Maintenance Charges (Common Area)                     500.00"); y -= 12
    p.text(9, 72, y, "Water & Utilities (Fixed)                             300.00"); y -= 3
    p.rule(72, y, 540, y); y -= 12
    p.text(9, 72, y, "Total Rent for August 2026                            9,000.00", bold=True); y -= 13
    p.text(9, 72, y, "Amount Received / Paid                                9,000.00", bold=True); y -= 12
    p.text(9, 72, y, "Due Date:  2026-08-05"); y -= 13
    p.text(10, 72, y, "Status:  PAID IN FULL - No balance remaining.", bold=True); y -= 16

    # Payment details
    p.text(9, 72, y, "PAYMENT DETAILS", bold=True); y -= 12
    p.text(8, 72, y, "Payment Method:  UPI (GPay)     |     Transaction Ref:  UTR4137XXXX0912"); y -= 11
    p.text(8, 72, y, "Date Paid:  05-Aug-2026        |     Bank:  HDFC Bank, A/c 5010XXXX3321"); y -= 11
    p.text(8, 72, y, "Credited to:  Skyline Property Management (R. Nair)   |   UPI: skylinepm@hdfcbank"); y -= 15

    # Notes
    p.text(9, 72, y, "NOTES", bold=True); y -= 12
    p.text(8, 72, y, "1. Rent for subsequent months is due on or before the 5th of each month. Late payment"); y -= 11
    p.text(8, 72, y, "   attracts a penalty of Rs. 200 per day after the due date."); y -= 11
    p.text(8, 72, y, "2. This receipt confirms that the above amount has been received in full for the stated"); y -= 11
    p.text(8, 72, y, "   billing period. No balance remains for August 2026."); y -= 11
    p.text(8, 72, y, "3. Kindly retain this receipt for your records and for rent-deduction documentation."); y -= 11
    p.text(8, 72, y, "4. For any discrepancy, contact accounts@skylinepm.in within 7 days of issue."); y -= 16

    # Signature block
    p.text(10, 72, y, "Authorized Signatory", bold=True); y -= 12
    p.text(10, 72, y, "For Skyline Property Management"); y -= 12
    p.text(10, 72, y, "R. Nair (Owner) / Authorized Representative"); y -= 14

    # Footer
    p.rule(72, y, 540, y); y -= 10
    p.text(8, 72, y, "Skyline Property Management  |  GSTIN: 29AABCS1234L1Z2  |  CIN: U70100KA2019PTC124567"); y -= 10
    p.text(8, 72, y, "This is a computer-generated receipt and does not require a physical signature."); y -= 10
    return p.build()


def adb(serial: str, *args: str) -> subprocess.CompletedProcess:
    return subprocess.run(["adb", "-s", serial, *args], capture_output=True, text=True, check=False)


def push_pdf(serial: str, local: Path, dest_name: str, mtime: str) -> None:
    """Push a PDF to /sdcard/Download, pin its mtime, and media-scan."""
    if not local.exists():
        raise FileNotFoundError(local)
    adb(serial, "shell", "mkdir", "-p", "/sdcard/Download")
    r = adb(serial, "push", str(local), f"/sdcard/Download/{dest_name}")
    print(f"  push {dest_name}: {r.stdout.strip() or r.returncode}")
    adb(serial, "shell", "touch", "-m", "-t", mtime, f"/sdcard/Download/{dest_name}")
    adb(serial, "shell", "content", "call", "--uri", "content://media/none",
        "--method", "scan_volume", "--arg", "external_primary")


def main() -> int:
    ap = argparse.ArgumentParser(description="Fabricate realistic text-heavy public PDFs (invoice + rent receipt).")
    ap.add_argument("--serial", default=DEFAULT_SERIAL, help="ADB device serial (default: wireless).")
    ap.add_argument("--no-push", action="store_true", help="Only write the PDFs to assets/seeds/public, do not push.")
    args = ap.parse_args()

    OUT_DIR.mkdir(parents=True, exist_ok=True)

    invoice = OUT_DIR / "Invoice INV-2026-071.pdf"
    rent = OUT_DIR / "Rent Receipt.pdf"
    invoice.write_bytes(build_invoice())
    rent.write_bytes(build_rent_receipt())
    print(f"generated {invoice} ({invoice.stat().st_size} bytes)")
    print(f"generated {rent} ({rent.stat().st_size} bytes)")

    if not args.no_push:
        # Preserve the mtimes the files already had on-device.
        push_pdf(args.serial, invoice, "Invoice INV-2026-071.pdf", "202608130326.00")
        push_pdf(args.serial, rent, "Rent Receipt.pdf", "202608192128.00")
        print("pushed both PDFs to /sdcard/Download and media-scanned.")
    return 0


if __name__ == "__main__":
    sys.exit(main())

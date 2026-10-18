#!/usr/bin/env python3
"""Compile locale/sq/LC_MESSAGES/django.po into django.mo without gettext tooling."""
from __future__ import annotations

import gettext
import re
import struct
from pathlib import Path

BASE = Path(__file__).resolve().parents[1]
PO = BASE / "locale/sq/LC_MESSAGES/django.po"
MO = BASE / "locale/sq/LC_MESSAGES/django.mo"


def flat_po_string(raw: str) -> str:
    chunks = re.findall(r'"(.*?)"', raw, flags=re.S)
    out = []
    for c in chunks:
        out.append(
            c.replace("\\\\", "\0")
            .replace("\\n", "\n")
            .replace('\\"', '"')
            .replace("\\t", "\t")
            .replace("\0", "\\")
        )
    return "".join(out)


def parse_po(text: str) -> dict[str, str]:
    entries: dict[str, str] = {}
    parts = re.split(r"\n(?=msgid )", text)
    for part in parts:
        if not part.startswith("msgid "):
            continue
        m = re.match(
            r"msgid ((?:\".*?\"(?:\n|$))+)\s*msgstr ((?:\".*?\"(?:\n|$))+)",
            part,
            flags=re.S,
        )
        if not m:
            continue
        mid = flat_po_string(m.group(1))
        mstr = flat_po_string(m.group(2))
        if mid == "":
            continue
        entries[mid] = mstr
    return entries


def write_mo(catalog: dict[str, str], path: Path) -> None:
    # Ensure header
    data = {"": "Content-Type: text/plain; charset=UTF-8\n"}
    data.update({k: v for k, v in catalog.items() if v})
    keys = sorted(data.keys())
    encoded = [(k.encode("utf-8"), data[k].encode("utf-8")) for k in keys]
    count = len(encoded)

    ids_blob = b""
    strs_blob = b""
    id_index = []
    str_index = []
    for k, v in encoded:
        id_index.append((len(k), len(ids_blob)))
        ids_blob += k + b"\0"
        str_index.append((len(v), len(strs_blob)))
        strs_blob += v + b"\0"

    header_size = 7 * 4
    otu = header_size
    ott = otu + 8 * count
    ids_start = ott + 8 * count
    strs_start = ids_start + len(ids_blob)

    out = bytearray()
    out += struct.pack("<Iiiiiii", 0x950412DE, 0, count, otu, ott, 0, 0)
    for length, offset in id_index:
        out += struct.pack("<II", length, ids_start + offset)
    for length, offset in str_index:
        out += struct.pack("<II", length, strs_start + offset)
    out += ids_blob + strs_blob
    path.write_bytes(bytes(out))


def main() -> None:
    entries = parse_po(PO.read_text(encoding="utf-8"))
    translated = sum(1 for v in entries.values() if v)
    print(f"parsed={len(entries)} translated={translated}")
    print("sample:", entries.get("Learn from home. Train with purpose."))
    write_mo(entries, MO)
    print(f"wrote {MO} ({MO.stat().st_size} bytes)")

    t = gettext.translation("django", localedir=str(BASE / "locale"), languages=["sq"])
    for s in [
        "Home",
        "About",
        "Learn from home. Train with purpose.",
        "Who we are",
        "Browse Courses",
        "Unlock for",
        "Explore Courses",
    ]:
        print(f"{s!r} => {t.gettext(s)!r}")


if __name__ == "__main__":
    main()

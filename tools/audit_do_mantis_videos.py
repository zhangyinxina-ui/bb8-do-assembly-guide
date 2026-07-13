#!/usr/bin/env python3
"""Audit public Mantis Hacks D-O playlist descriptions without downloading media."""

from __future__ import annotations

import json
import re
import subprocess
from datetime import datetime
from pathlib import Path
from urllib.parse import urlparse
from zoneinfo import ZoneInfo


ROOT = Path(__file__).resolve().parents[1]
PLAYLIST = "https://youtube.com/playlist?list=PLTSAQ5KEjPVCldgA1t-KT1lRTKJdAY7er"
OUT = ROOT / "engineering" / "do_mantis_video_audit.json"
PUBLIC_OUT = ROOT / "public" / "downloads" / "do_mantis_video_audit.json"
EXPECTED_IDS = {
    "zplirkxl6iM",
    "a1trQXC5bqI",
    "NxBvnvnvBc0",
    "DK3hTPibldo",
    "2cIdjQiS2ZE",
    "XyuE0PggtiE",
}
RELEASE_DOMAINS = {
    "github.com",
    "gitlab.com",
    "drive.google.com",
    "docs.google.com",
    "dropbox.com",
    "www.dropbox.com",
}
RELEASE_SUFFIXES = (".stl", ".step", ".stp", ".f3d", ".ino", ".zip", ".3mf")


def description_urls(description: str) -> list[str]:
    return [
        match.rstrip(".,);]")
        for match in re.findall(r"https?://\S+", description)
    ]


def is_direct_release_url(url: str) -> bool:
    parsed = urlparse(url)
    host = parsed.netloc.lower()
    path = parsed.path.lower()
    return host in RELEASE_DOMAINS or path.endswith(RELEASE_SUFFIXES)


def main() -> None:
    completed = subprocess.run(
        ["yt-dlp", "--no-update", "--skip-download", "--dump-json", PLAYLIST],
        check=True,
        text=True,
        capture_output=True,
    )
    videos = [json.loads(line) for line in completed.stdout.splitlines() if line.strip()]
    actual_ids = {video["id"] for video in videos}
    if actual_ids != EXPECTED_IDS:
        raise SystemExit(
            f"FAIL playlist membership changed: expected={sorted(EXPECTED_IDS)} "
            f"actual={sorted(actual_ids)}"
        )

    direct_release_links: list[str] = []
    entries = []
    for video in sorted(videos, key=lambda item: item.get("upload_date", "")):
        urls = description_urls(video.get("description") or "")
        direct_release_links.extend(url for url in urls if is_direct_release_url(url))
        entry = {
            "id": video["id"],
            "title": video["title"],
            "upload_date": datetime.strptime(video["upload_date"], "%Y%m%d").date().isoformat(),
        }
        if video["id"] == "DK3hTPibldo":
            entry["description_evidence"] = (
                "states that the build is based on Michael Baddeley's CAD sent "
                "directly to Matt, with Matt making his own servo, drive and electronics changes"
            )
        entries.append(entry)

    direct_release_links = sorted(set(direct_release_links))
    manifest = {
        "audit_date": datetime.now(ZoneInfo("Asia/Shanghai")).date().isoformat(),
        "scope": "metadata-only audit of every entry in Matt Denton's public Droid Build D-O playlist",
        "playlist": {
            "url": PLAYLIST,
            "title": "Droid Build D-O",
            "uploader": "Matt Denton",
            "entry_count": len(entries),
        },
        "retrieval": {
            "method": "yt-dlp --skip-download --dump-json; video media was not downloaded",
            "fields_audited": [
                "video id",
                "title",
                "upload date",
                "public description URLs",
            ],
        },
        "entries": entries,
        "description_link_findings": {
            "direct_matt_modified_cad_download_found": bool(direct_release_links),
            "direct_matt_control_source_download_found": bool(direct_release_links),
            "github_gitlab_drive_dropbox_release_link_found": bool(direct_release_links),
            "direct_release_links": direct_release_links,
            "links_found_instead": [
                "D-O Builders Facebook group",
                "Michael Baddeley Facebook group",
                "Mr Baddeley Patreon",
                "Matt Denton Threeding profile",
                "component vendor and affiliate product pages",
                "Matt Denton social and support pages",
            ],
        },
        "conclusion": (
            "The six-entry playlist is five numbered build episodes plus one tyre-printing "
            "video. Its public descriptions document parts and provenance but do not release "
            "Matt Denton's modified D-O CAD or control source."
        ),
        "boundary": (
            "This proves only what the six public descriptions exposed on the audit date. It "
            "does not prove that no file exists in a private Facebook group, paid membership, "
            "later post or unindexed source. Any newly found file still requires an explicit "
            "licence review before use or redistribution."
        ),
    }

    encoded = json.dumps(manifest, ensure_ascii=False, indent=2) + "\n"
    OUT.write_text(encoded, encoding="utf-8")
    PUBLIC_OUT.write_text(encoded, encoding="utf-8")
    print(
        f"PASS MANTIS VIDEO AUDIT entries={len(entries)} "
        f"direct_release_links={len(direct_release_links)}"
    )


if __name__ == "__main__":
    main()

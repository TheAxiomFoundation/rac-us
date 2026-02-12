#!/usr/bin/env python3
"""
USC Statute Scraper

Fetches US Code titles from uscode.house.gov in USLM XML format,
splits by section, and stores using atlas.

Usage:
    python scraper.py                    # Fetch all configured titles
    python scraper.py --title 26         # Fetch only Title 26 (IRC)
    python scraper.py --title 26 --dry-run  # Show what would be fetched

Storage structure (via lawarchive):
    {output_dir}/us/statute/{title}/{section}/{effective_date}/
        original.xml     - Raw XML from source
        canonical.json   - Normalized format

Sources:
    - https://uscode.house.gov/download/download.shtml
    - USLM User Guide: http://uscode.house.gov/download/resources/USLM-User-Guide.pdf
"""

import argparse
import io
import logging
import re
import zipfile
from dataclasses import dataclass, field
from datetime import date, datetime
from pathlib import Path
from typing import Dict, Iterator, List, Optional
from xml.etree import ElementTree as ET

import requests

# Import from lawarchive for consistent storage
from lawarchive.writer import (
    CanonicalDocument,
    DocumentWriter,
    LocalBackend,
)

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

# USLM namespace
USLM_NS = {"uslm": "http://xml.house.gov/schemas/uslm/1.0"}

# Current release point (update as new public laws are enacted)
# Check https://uscode.house.gov/download/download.shtml for latest
CURRENT_RELEASE = "119-46"  # As of 2025-12-02

# Base URL for downloads
BASE_URL = "https://uscode.house.gov/download/releasepoints/us/pl"

# Titles we care about for tax/benefit calculations
DEFAULT_TITLES = [
    26,  # Internal Revenue Code
    7,   # Agriculture (SNAP)
    42,  # Public Health and Welfare (Medicaid, TANF, etc.)
]


@dataclass
class ParsedSection:
    """Intermediate representation of a parsed USC section."""

    title: int
    section: str  # e.g., "32" or "32A"
    subsections: List[str] = field(default_factory=list)  # e.g., ["a", "b", "c"]
    heading: str = ""
    content_xml: str = ""
    effective_date: str = ""  # YYYY-MM-DD


class USCScraper:
    """Scrapes US Code from uscode.house.gov."""

    def __init__(
        self,
        output_dir: Path,
        release: str = CURRENT_RELEASE,
        titles: Optional[List[int]] = None,
    ):
        self.output_dir = output_dir
        self.release = release
        self.titles = titles or DEFAULT_TITLES
        self.accessed_date = date.today()

        # Set up document writer
        backend = LocalBackend(root=output_dir)
        self.writer = DocumentWriter(backend=backend)

    def download_url(self, title: int) -> str:
        """Get download URL for a title."""
        pl_parts = self.release.split("-")
        return f"{BASE_URL}/{pl_parts[0]}/{pl_parts[1]}/xml_usc{title:02d}@{self.release}.zip"

    def fetch_title(self, title: int) -> Optional[bytes]:
        """Download a title's XML zip file."""
        url = self.download_url(title)
        logger.info(f"Fetching Title {title} from {url}")

        try:
            response = requests.get(url, timeout=120)
            response.raise_for_status()
            return response.content
        except requests.RequestException as e:
            logger.error(f"Failed to fetch Title {title}: {e}")
            return None

    def parse_title(self, title: int, zip_content: bytes) -> Iterator[ParsedSection]:
        """Parse XML and yield sections."""
        with zipfile.ZipFile(io.BytesIO(zip_content)) as zf:
            # Find the main XML file
            xml_files = [f for f in zf.namelist() if f.endswith(".xml")]
            if not xml_files:
                logger.error(f"No XML files found in Title {title} archive")
                return

            for xml_file in xml_files:
                logger.info(f"Parsing {xml_file}")
                with zf.open(xml_file) as f:
                    yield from self._parse_xml(title, f.read())

    def _parse_xml(self, title: int, xml_content: bytes) -> Iterator[ParsedSection]:
        """Parse USLM XML and extract sections."""
        try:
            root = ET.fromstring(xml_content)
        except ET.ParseError as e:
            logger.error(f"Failed to parse XML for Title {title}: {e}")
            return

        # Find all section elements
        # USLM uses <section> elements with identifier attributes
        for section_elem in root.iter():
            if section_elem.tag.endswith("}section") or section_elem.tag == "section":
                section = self._extract_section(title, section_elem, xml_content)
                if section:
                    yield section

    def _extract_section(
        self, title: int, elem: ET.Element, full_xml: bytes
    ) -> Optional[ParsedSection]:
        """Extract section data from XML element."""
        # Get section identifier (e.g., "/us/usc/t26/s32")
        identifier = elem.get("identifier", "")

        # Parse section number from identifier
        match = re.search(r"/s(\d+[A-Za-z]*)", identifier)
        if not match:
            return None

        section_num = match.group(1)

        # Get heading
        heading = ""
        for child in elem:
            if child.tag.endswith("}heading") or child.tag == "heading":
                heading = "".join(child.itertext()).strip()
                break

        # Get subsections
        subsections = []
        for child in elem.iter():
            tag = child.tag.split("}")[-1] if "}" in child.tag else child.tag
            if tag == "subsection":
                sub_id = child.get("identifier", "")
                sub_match = re.search(r"/(\w+)$", sub_id)
                if sub_match:
                    subsections.append(sub_match.group(1))

        # Extract raw XML for this section
        content_xml = ET.tostring(elem, encoding="unicode")

        # Try to find effective date from document metadata
        # Default to release point date if not found
        effective_date = self._release_to_date(self.release)

        return ParsedSection(
            title=title,
            section=section_num,
            subsections=subsections,
            heading=heading,
            content_xml=content_xml,
            effective_date=effective_date,
        )

    def _release_to_date(self, release: str) -> str:
        """Convert release point to approximate effective date."""
        # This is approximate - actual effective dates vary by provision
        # For now, use a mapping of known release points
        # TODO: Parse actual effective dates from XML
        release_dates = {
            "119-46": "2025-01-01",
            "118-200": "2024-01-01",
        }
        return release_dates.get(release, datetime.now().strftime("%Y-%m-%d"))

    def _extract_text(self, xml_content: str) -> str:
        """Extract text content from XML."""
        try:
            elem = ET.fromstring(xml_content)
            content_text = " ".join(elem.itertext()).strip()
            # Normalize whitespace
            content_text = re.sub(r"\s+", " ", content_text)
            return content_text
        except ET.ParseError:
            return ""

    def section_to_canonical(
        self, section: ParsedSection, source_url: str
    ) -> CanonicalDocument:
        """Convert ParsedSection to CanonicalDocument for lawarchive."""
        content_text = self._extract_text(section.content_xml)
        effective_date = date.fromisoformat(section.effective_date)

        return CanonicalDocument(
            jurisdiction="us",
            doc_type="statute",
            citation=f"{section.title} USC § {section.section}",
            title=section.title,
            section=section.section,
            heading=section.heading,
            effective_date=effective_date,
            accessed_date=self.accessed_date,
            source_url=source_url,
            content_text=content_text,
            release_point=self.release,
            subsections=[{"id": sub} for sub in section.subsections],
        )

    def save_section(self, section: ParsedSection, source_url: str) -> str:
        """Save section using DocumentWriter."""
        canonical = self.section_to_canonical(section, source_url)

        # Write using lawarchive writer (handles directory structure, formats)
        path = self.writer.write(
            doc=canonical,
            original=section.content_xml.encode("utf-8"),
            original_format="xml",
        )

        logger.debug(f"Saved {canonical.citation} to {path}")
        return path

    def run(self, dry_run: bool = False) -> Dict[int, int]:
        """Fetch and process all configured titles."""
        stats = {}

        for title in self.titles:
            logger.info(f"Processing Title {title}")

            if dry_run:
                logger.info(f"  Would fetch: {self.download_url(title)}")
                stats[title] = 0
                continue

            zip_content = self.fetch_title(title)
            if not zip_content:
                stats[title] = 0
                continue

            section_count = 0
            source_url = self.download_url(title)

            for section in self.parse_title(title, zip_content):
                self.save_section(section, source_url)
                section_count += 1

            stats[title] = section_count
            logger.info(f"  Processed {section_count} sections from Title {title}")

        return stats


def main():
    parser = argparse.ArgumentParser(description="Fetch USC statutes")
    parser.add_argument(
        "--title",
        type=int,
        help="Specific title to fetch (default: all configured)",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path(__file__).parent.parent / "lawarchive",
        help="Output directory (default: ../lawarchive)",
    )
    parser.add_argument(
        "--release",
        default=CURRENT_RELEASE,
        help=f"Release point (default: {CURRENT_RELEASE})",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be fetched without downloading",
    )
    args = parser.parse_args()

    titles = [args.title] if args.title else None

    scraper = USCScraper(
        output_dir=args.output,
        release=args.release,
        titles=titles,
    )

    stats = scraper.run(dry_run=args.dry_run)

    print("\nSummary:")
    for title, count in stats.items():
        print(f"  Title {title}: {count} sections")


if __name__ == "__main__":
    main()

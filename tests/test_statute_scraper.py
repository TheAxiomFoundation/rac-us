"""Tests for statute scraper."""

import json
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from statute.scraper import (
    CURRENT_RELEASE,
    ParsedSection,
    USCScraper,
)
from lawarchive.writer import CanonicalDocument


# Sample USLM XML for testing
SAMPLE_XML = """<?xml version="1.0" encoding="UTF-8"?>
<usc xmlns="http://xml.house.gov/schemas/uslm/1.0">
  <section identifier="/us/usc/t26/s32">
    <num value="32">Sec. 32.</num>
    <heading>Earned income</heading>
    <subsection identifier="/us/usc/t26/s32/a">
      <num value="a">(a)</num>
      <heading>Allowance of credit</heading>
      <content>In the case of an eligible individual, there shall be allowed a credit.</content>
    </subsection>
    <subsection identifier="/us/usc/t26/s32/b">
      <num value="b">(b)</num>
      <heading>Percentages</heading>
      <content>The credit percentage shall be determined as follows.</content>
    </subsection>
  </section>
  <section identifier="/us/usc/t26/s24">
    <num value="24">Sec. 24.</num>
    <heading>Child tax credit</heading>
    <subsection identifier="/us/usc/t26/s24/a">
      <num value="a">(a)</num>
      <content>Allowance of credit.</content>
    </subsection>
  </section>
</usc>
""".encode('utf-8')


class TestUSCScraper:
    """Tests for USCScraper class."""

    def test_download_url_format(self):
        """Test URL generation for title downloads."""
        scraper = USCScraper(output_dir=Path("/tmp"), release="119-46")

        url = scraper.download_url(26)
        assert url == "https://uscode.house.gov/download/releasepoints/us/pl/119/46/xml_usc26@119-46.zip"

        url = scraper.download_url(7)
        assert url == "https://uscode.house.gov/download/releasepoints/us/pl/119/46/xml_usc07@119-46.zip"

    def test_download_url_different_release(self):
        """Test URL generation with different release point."""
        scraper = USCScraper(output_dir=Path("/tmp"), release="118-200")

        url = scraper.download_url(42)
        assert url == "https://uscode.house.gov/download/releasepoints/us/pl/118/200/xml_usc42@118-200.zip"

    def test_parse_xml_extracts_sections(self):
        """Test that XML parsing extracts all sections."""
        scraper = USCScraper(output_dir=Path("/tmp"))

        sections = list(scraper._parse_xml(26, SAMPLE_XML))

        assert len(sections) == 2
        assert sections[0].section == "32"
        assert sections[1].section == "24"

    def test_parse_xml_extracts_heading(self):
        """Test that section headings are extracted."""
        scraper = USCScraper(output_dir=Path("/tmp"))

        sections = list(scraper._parse_xml(26, SAMPLE_XML))

        assert sections[0].heading == "Earned income"
        assert sections[1].heading == "Child tax credit"

    def test_parse_xml_extracts_subsections(self):
        """Test that subsection identifiers are extracted."""
        scraper = USCScraper(output_dir=Path("/tmp"))

        sections = list(scraper._parse_xml(26, SAMPLE_XML))

        # Section 32 has subsections a and b
        assert "a" in sections[0].subsections
        assert "b" in sections[0].subsections

        # Section 24 has subsection a
        assert "a" in sections[1].subsections

    def test_parse_xml_sets_title(self):
        """Test that title number is set on sections."""
        scraper = USCScraper(output_dir=Path("/tmp"))

        sections = list(scraper._parse_xml(26, SAMPLE_XML))

        for section in sections:
            assert section.title == 26

    def test_parse_xml_stores_raw_xml(self):
        """Test that raw XML is stored in section."""
        scraper = USCScraper(output_dir=Path("/tmp"))

        sections = list(scraper._parse_xml(26, SAMPLE_XML))

        # XML may have namespace prefixes, so check for content
        assert "Earned income" in sections[0].content_xml
        assert "eligible individual" in sections[0].content_xml


class TestParsedSection:
    """Tests for ParsedSection dataclass."""

    def test_section_defaults(self):
        """Test ParsedSection default values."""
        section = ParsedSection(title=26, section="32")

        assert section.title == 26
        assert section.section == "32"
        assert section.subsections == []
        assert section.heading == ""
        assert section.content_xml == ""
        assert section.effective_date == ""

    def test_section_with_values(self):
        """Test ParsedSection with all values set."""
        section = ParsedSection(
            title=26,
            section="32",
            subsections=["a", "b", "c"],
            heading="Earned income",
            content_xml="<section>...</section>",
            effective_date="2024-01-01",
        )

        assert section.subsections == ["a", "b", "c"]
        assert section.heading == "Earned income"


class TestCanonicalDocument:
    """Tests for CanonicalDocument (from lawarchive)."""

    def test_canonical_to_dict(self):
        """Test conversion to dictionary."""
        from datetime import date
        doc = CanonicalDocument(
            jurisdiction="us",
            doc_type="statute",
            citation="26 USC § 32",
            title=26,
            section="32",
            heading="Earned income",
            effective_date=date(2024, 1, 1),
            accessed_date=date(2025, 6, 15),
            source_url="https://example.com",
            release_point="119-46",
            content_text="The credit shall be allowed.",
            subsections=[{"id": "a"}, {"id": "b"}],
        )

        d = doc.to_dict()

        assert d["citation"] == "26 USC § 32"
        assert d["title"] == 26
        assert d["section"] == "32"
        assert d["effective_date"] == "2024-01-01"
        assert d["accessed_date"] == "2025-06-15"
        assert len(d["subsections"]) == 2

    def test_canonical_to_dict_serializable(self):
        """Test that to_dict produces JSON-serializable output."""
        from datetime import date
        doc = CanonicalDocument(
            jurisdiction="us",
            doc_type="statute",
            citation="26 USC § 32",
            title=26,
            section="32",
            heading="Earned income",
            effective_date=date(2024, 1, 1),
            accessed_date=date(2025, 6, 15),
            source_url="https://example.com",
            release_point="119-46",
            content_text="The credit shall be allowed.",
            subsections=[],
        )

        # Should not raise - JSON serialization works
        json_str = json.dumps(doc.to_dict())
        # § gets escaped to \u00a7 in JSON, so check for the escaped or decoded version
        parsed = json.loads(json_str)
        assert parsed["citation"] == "26 USC § 32"


class TestSectionToCanonical:
    """Tests for section to canonical conversion."""

    def test_section_to_canonical_basic(self):
        """Test basic conversion from ParsedSection to CanonicalDocument."""
        scraper = USCScraper(output_dir=Path("/tmp"))

        section = ParsedSection(
            title=26,
            section="32",
            subsections=["a", "b"],
            heading="Earned income",
            content_xml="<section><content>Test content here</content></section>",
            effective_date="2024-01-01",
        )

        canonical = scraper.section_to_canonical(section, "https://example.com/usc26.zip")

        assert canonical.citation == "26 USC § 32"
        assert canonical.title == 26
        assert canonical.section == "32"
        assert canonical.heading == "Earned income"
        assert canonical.effective_date.isoformat() == "2024-01-01"
        assert canonical.source_url == "https://example.com/usc26.zip"
        assert "Test content here" in canonical.content_text

    def test_section_to_canonical_extracts_text(self):
        """Test that text is extracted from XML content."""
        scraper = USCScraper(output_dir=Path("/tmp"))

        section = ParsedSection(
            title=26,
            section="32",
            content_xml="<section><p>First paragraph.</p><p>Second paragraph.</p></section>",
            effective_date="2024-01-01",
        )

        canonical = scraper.section_to_canonical(section, "https://example.com")

        assert "First paragraph" in canonical.content_text
        assert "Second paragraph" in canonical.content_text


class TestSaveSection:
    """Tests for saving sections to disk."""

    def test_save_section_creates_directory(self):
        """Test that save creates the correct directory structure."""
        with tempfile.TemporaryDirectory() as tmpdir:
            scraper = USCScraper(output_dir=Path(tmpdir))

            section = ParsedSection(
                title=26,
                section="32",
                content_xml="<section>test</section>",
                effective_date="2024-01-01",
            )

            saved_path = scraper.save_section(section, "https://example.com")

            # Path is now us/statutes/26/32/2024-01-01
            expected_dir = Path(tmpdir) / "us" / "statutes" / "26" / "32" / "2024-01-01"
            assert expected_dir.exists()
            assert saved_path == "us/statutes/26/32/2024-01-01"

    def test_save_section_writes_original_xml(self):
        """Test that original XML is saved."""
        with tempfile.TemporaryDirectory() as tmpdir:
            scraper = USCScraper(output_dir=Path(tmpdir))

            section = ParsedSection(
                title=26,
                section="32",
                content_xml="<section>original xml content</section>",
                effective_date="2024-01-01",
            )

            saved_path = scraper.save_section(section, "https://example.com")

            xml_file = Path(tmpdir) / saved_path / "original.xml"
            assert xml_file.exists()
            assert "original xml content" in xml_file.read_text()

    def test_save_section_writes_canonical_json(self):
        """Test that canonical JSON is saved."""
        with tempfile.TemporaryDirectory() as tmpdir:
            scraper = USCScraper(output_dir=Path(tmpdir))

            section = ParsedSection(
                title=26,
                section="32",
                heading="Earned income",
                content_xml="<section>test</section>",
                effective_date="2024-01-01",
            )

            saved_path = scraper.save_section(section, "https://example.com")

            json_file = Path(tmpdir) / saved_path / "canonical.json"
            assert json_file.exists()

            data = json.loads(json_file.read_text())
            assert data["citation"] == "26 USC § 32"
            assert data["heading"] == "Earned income"


class TestDryRun:
    """Tests for dry run mode."""

    def test_dry_run_does_not_fetch(self):
        """Test that dry run mode doesn't make network requests."""
        with tempfile.TemporaryDirectory() as tmpdir:
            scraper = USCScraper(output_dir=Path(tmpdir), titles=[26])

            with patch.object(scraper, 'fetch_title') as mock_fetch:
                stats = scraper.run(dry_run=True)

                mock_fetch.assert_not_called()
                assert stats[26] == 0


class TestReleaseToDate:
    """Tests for release point to date conversion."""

    def test_known_release_dates(self):
        """Test that known release points map to correct dates."""
        scraper = USCScraper(output_dir=Path("/tmp"))

        assert scraper._release_to_date("119-46") == "2025-01-01"
        assert scraper._release_to_date("118-200") == "2024-01-01"

    def test_unknown_release_defaults_to_today(self):
        """Test that unknown release points default to current date."""
        scraper = USCScraper(output_dir=Path("/tmp"))

        date = scraper._release_to_date("999-999")
        # Should be today's date in YYYY-MM-DD format
        assert len(date) == 10
        assert date.count("-") == 2


# Integration test marker - skip by default
@pytest.mark.integration
class TestIntegration:
    """Integration tests that hit real endpoints."""

    def test_fetch_real_title(self):
        """Test fetching a real title from uscode.house.gov."""
        with tempfile.TemporaryDirectory() as tmpdir:
            scraper = USCScraper(output_dir=Path(tmpdir), titles=[26])

            zip_content = scraper.fetch_title(26)

            assert zip_content is not None
            assert len(zip_content) > 0

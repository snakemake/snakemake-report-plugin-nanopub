"""Tests for the Reporter class and related functionality in __init__.py"""

import json
from pathlib import Path
from unittest.mock import Mock, MagicMock, patch
import datetime

import pytest
from rdflib import Literal, URIRef

from snakemake_report_plugin_nanopub import (
    Reporter,
    ReportSettings,
)


class TestReportSettings:
    """Test the ReportSettings dataclass."""

    def test_settings_with_required_workflow_id(self):
        """Test creating ReportSettings with required workflow_id."""
        settings = ReportSettings(
            workflow_id="https://example.com/workflow/123",
            output_path=None,
            main_server=False,
            dry_run=False,
        )
        assert settings.workflow_id == "https://example.com/workflow/123"
        assert settings.output_path is None
        assert settings.main_server is False
        assert settings.dry_run is False

    def test_settings_with_output_path(self):
        """Test creating ReportSettings with output_path."""
        path = Path("/tmp/metadata.json")
        settings = ReportSettings(
            workflow_id="wf123",
            output_path=path,
            main_server=True,
            dry_run=True,
        )
        assert settings.output_path == path
        assert settings.main_server is True
        assert settings.dry_run is True


class MockMetadata:
    """Mock for Snakemake workflow metadata."""

    def __init__(self):
        self.workflow_name = "test_workflow"


class MockDAG:
    """Mock for Snakemake DAG."""

    def __init__(self):
        self.rules = {}


class DummyReporter(Reporter):
    """Reporter subclass with minimal mocking for testing."""

    def __init__(self, **kwargs):
        # Set required attributes from ReporterBase
        self.jobs = kwargs.get("jobs", [])
        self.rules = kwargs.get("rules", [])
        self.results = kwargs.get("results", {})
        self.metadata = kwargs.get("metadata", MockMetadata())
        self.dag = kwargs.get("dag", MockDAG())
        self.workflow_description = kwargs.get("workflow_description", "Test workflow")
        self.generated_at = datetime.datetime.now(datetime.UTC).isoformat()

        # Create settings
        self.settings = kwargs.get(
            "settings",
            ReportSettings(
                workflow_id="test-workflow-id",
                output_path=None,
                main_server=False,
                dry_run=False,
            ),
        )

        # Call parent __post_init__
        self.__post_init__()


class TestReporterJsonable:
    """Test the _jsonable method."""

    def test_jsonable_dict(self):
        """Test _jsonable with dictionary."""
        reporter = DummyReporter()
        result = reporter._jsonable({"key": "value", "nested": {"inner": 42}})
        assert result == {"key": "value", "nested": {"inner": 42}}

    def test_jsonable_list(self):
        """Test _jsonable with list."""
        reporter = DummyReporter()
        result = reporter._jsonable([1, "two", 3.0, None])
        assert result == [1, "two", 3.0, None]

    def test_jsonable_path(self):
        """Test _jsonable with Path object."""
        reporter = DummyReporter()
        result = reporter._jsonable(Path("/tmp/file.txt"))
        assert result == "/tmp/file.txt"

    def test_jsonable_primitives(self):
        """Test _jsonable with primitive types."""
        reporter = DummyReporter()
        assert reporter._jsonable("string") == "string"
        assert reporter._jsonable(42) == 42
        assert reporter._jsonable(3.14) == 3.14
        assert reporter._jsonable(True) is True
        assert reporter._jsonable(None) is None

    def test_jsonable_nested_complex(self):
        """Test _jsonable with deeply nested structures."""
        reporter = DummyReporter()
        complex_obj = {
            "list": [1, Path("/tmp"), {"nested": True}],
            "path": Path("/home"),
        }
        result = reporter._jsonable(complex_obj)
        assert result == {
            "list": [1, "/tmp", {"nested": True}],
            "path": "/home",
        }


class TestReporterMakeTerm:
    """Test the make_term method for creating RDF terms."""

    def test_make_term_none(self):
        """Test make_term with None returns None."""
        reporter = DummyReporter()
        assert reporter.make_term(None) is None

    def test_make_term_boolean(self):
        """Test make_term with boolean values."""
        reporter = DummyReporter()
        result = reporter.make_term(True)
        assert isinstance(result, Literal)
        assert str(result) == "true"

    def test_make_term_integer(self):
        """Test make_term with integer."""
        reporter = DummyReporter()
        result = reporter.make_term(42)
        assert isinstance(result, Literal)
        assert str(result) == "42"

    def test_make_term_float(self):
        """Test make_term with float."""
        reporter = DummyReporter()
        result = reporter.make_term(3.14)
        assert isinstance(result, Literal)
        assert float(str(result)) == pytest.approx(3.14)

    def test_make_term_url_string(self):
        """Test make_term with URL string creates URIRef."""
        reporter = DummyReporter()
        result = reporter.make_term("https://example.com/resource")
        assert isinstance(result, URIRef)

    def test_make_term_urn_string(self):
        """Test make_term with URN string creates URIRef."""
        reporter = DummyReporter()
        result = reporter.make_term("urn:uuid:12345")
        assert isinstance(result, URIRef)

    def test_make_term_http_string(self):
        """Test make_term with http string creates URIRef."""
        reporter = DummyReporter()
        result = reporter.make_term("http://example.com/resource")
        assert isinstance(result, URIRef)

    def test_make_term_plain_string(self):
        """Test make_term with plain string creates Literal."""
        reporter = DummyReporter()
        result = reporter.make_term("plain text")
        assert isinstance(result, Literal)
        assert str(result) == "plain text"

    def test_make_term_complex_object(self):
        """Test make_term with complex object (dict/list)."""
        reporter = DummyReporter()
        obj = {"key": "value", "number": 42}
        result = reporter.make_term(obj)
        assert isinstance(result, Literal)
        parsed = json.loads(str(result))
        assert parsed == obj


class TestReporterSafeFragment:
    """Test the safe_fragment method."""

    def test_safe_fragment_simple_string(self):
        """Test safe_fragment with simple string."""
        reporter = DummyReporter()
        result = reporter.safe_fragment("align")
        assert result == "align"

    def test_safe_fragment_with_spaces(self):
        """Test safe_fragment escapes spaces."""
        reporter = DummyReporter()
        result = reporter.safe_fragment("my rule")
        assert " " not in result
        assert "my" in result
        assert "rule" in result.lower() or "%20" in result

    def test_safe_fragment_with_special_chars(self):
        """Test safe_fragment escapes special characters."""
        reporter = DummyReporter()
        result = reporter.safe_fragment("rule:test-v1.2")
        # Should be URL-safe
        assert ":" not in result or "%3A" in result

    def test_safe_fragment_empty_string(self):
        """Test safe_fragment with empty string generates UUID."""
        reporter = DummyReporter()
        result = reporter.safe_fragment("")
        assert result.startswith("item-")
        assert len(result) > 10  # Should have UUID part

    def test_safe_fragment_none_value(self):
        """Test safe_fragment with None generates UUID."""
        reporter = DummyReporter()
        result = reporter.safe_fragment(None)
        assert result.startswith("item-")

    def test_safe_fragment_custom_prefix(self):
        """Test safe_fragment with custom prefix."""
        reporter = DummyReporter()
        result = reporter.safe_fragment("", prefix="rule")
        assert result.startswith("rule-")


class TestReporterPlainText:
    """Test the plain_text method for text normalization."""

    def test_plain_text_none(self):
        """Test plain_text with None returns None."""
        reporter = DummyReporter()
        assert reporter.plain_text(None) is None

    def test_plain_text_simple_string(self):
        """Test plain_text with simple string."""
        reporter = DummyReporter()
        result = reporter.plain_text("  hello world  ")
        assert result == "hello world"

    def test_plain_text_strip_triple_quotes(self):
        """Test plain_text strips triple quotes."""
        reporter = DummyReporter()
        result = reporter.plain_text('"""hello world"""')
        assert result == "hello world"
        result = reporter.plain_text("'''hello world'''")
        assert result == "hello world"

    def test_plain_text_escaped_newlines(self):
        """Test plain_text handles escaped newlines."""
        reporter = DummyReporter()
        result = reporter.plain_text("line1\\nline2\\nline3")
        assert "line1" in result
        assert "line2" in result
        assert "line3" in result

    def test_plain_text_carriage_returns(self):
        """Test plain_text handles carriage returns."""
        reporter = DummyReporter()
        result = reporter.plain_text("line1\r\nline2\rline3")
        lines = result.split("\n")
        assert len(lines) >= 2

    def test_plain_text_html_tags(self):
        """Test plain_text removes HTML tags."""
        reporter = DummyReporter()
        result = reporter.plain_text("<p>hello</p> <b>world</b>")
        assert "<p>" not in result
        assert "<b>" not in result
        assert "hello" in result
        assert "world" in result

    def test_plain_text_with_drop_links(self):
        """Test plain_text with drop_links option."""
        reporter = DummyReporter()
        result = reporter.plain_text(
            "Visit https://example.com for more", drop_links=True
        )
        assert "example.com" not in result
        assert "Visit" in result
        assert "more" in result

    def test_plain_text_with_drop_links_fragment(self):
        """Test plain_text drops link but keeps fragment."""
        reporter = DummyReporter()
        result = reporter.plain_text("See https://example.com#section", drop_links=True)
        assert "section" in result

    def test_plain_text_strip_comment_lines(self):
        """Test plain_text strips YAML comment lines."""
        reporter = DummyReporter()
        text = "# This is a comment\ndescription: value\n# Another comment"
        result = reporter.plain_text(text, strip_comment_lines=True)
        assert "# This is a comment" not in result
        assert "description: value" in result

    def test_plain_text_preserve_indentation(self):
        """Test plain_text preserves leading indentation."""
        reporter = DummyReporter()
        text = "  line1\n    line2\n  line3"
        result = reporter.plain_text(text)
        lines = result.split("\n")
        # Check indentation is preserved
        assert lines[0].startswith("  ")
        assert lines[1].startswith("    ")

    def test_plain_text_multiple_newlines(self):
        """Test plain_text collapses multiple newlines."""
        reporter = DummyReporter()
        result = reporter.plain_text("line1\n\n\n\n\nline2")
        assert "\n\n\n" not in result
        assert "line1" in result
        assert "line2" in result

    def test_plain_text_empty_after_cleanup(self):
        """Test plain_text returns None when empty after cleanup."""
        reporter = DummyReporter()
        result = reporter.plain_text("   \n\n   ")
        assert result is None

    def test_plain_text_html_entities(self):
        """Test plain_text unescapes HTML entities."""
        reporter = DummyReporter()
        result = reporter.plain_text("Hello &amp; goodbye")
        assert "&amp;" not in result
        assert "Hello & goodbye" == result

    def test_plain_text_br_tags(self):
        """Test plain_text converts br tags to newlines."""
        reporter = DummyReporter()
        result = reporter.plain_text("line1<br>line2<br/>line3")
        assert "line1" in result
        assert "line2" in result
        assert "line3" in result


class TestReporterBuildNanopub:
    """Test the build_nanopub method."""

    @patch("snakemake_report_plugin_nanopub.load_profile")
    @patch("snakemake_report_plugin_nanopub.Nanopub")
    def test_build_nanopub_minimal_payload(self, mock_nanopub_class, mock_load_profile):
        """Test build_nanopub with minimal payload."""
        # Setup mocks
        mock_profile = Mock()
        mock_profile.orcid_id = None
        mock_load_profile.return_value = mock_profile

        mock_np = Mock()
        mock_np._metadata = Mock()
        mock_np._metadata.namespace = {
            "dataset": "http://purl.org/nanopub/temp/dataset",
            "workflow-configuration": "http://purl.org/nanopub/temp/workflow-config",
        }
        mock_np._metadata.np_uri = "http://purl.org/nanopub/temp/np"
        mock_np.pubinfo = Mock()
        mock_np.pubinfo.add = Mock()
        mock_np.assertion = Mock()
        mock_np.assertion.add = Mock()
        mock_nanopub_class.return_value = mock_np

        reporter = DummyReporter()
        payload = {
            "workflow": {"description": "Test workflow", "config": "test: value"},
            "jobs_full": [],
            "rules_full": [],
        }

        reporter.build_nanopub(payload)

        # Verify nanopub was created
        assert mock_nanopub_class.called
        assert mock_np.pubinfo.add.called
        assert mock_np.assertion.add.called

    @patch("snakemake_report_plugin_nanopub.load_profile")
    @patch("snakemake_report_plugin_nanopub.Nanopub")
    def test_build_nanopub_with_profile_orcid(
        self, mock_nanopub_class, mock_load_profile
    ):
        """Test build_nanopub extracts ORCID from profile."""
        mock_profile = Mock()
        mock_profile.orcid_id = "0000-1111-2222-3333"
        mock_load_profile.return_value = mock_profile

        mock_np = Mock()
        mock_np._metadata = Mock()
        mock_np._metadata.namespace = {
            "dataset": "http://purl.org/nanopub/temp/dataset",
            "workflow-configuration": "http://purl.org/nanopub/temp/workflow-config",
        }
        mock_np._metadata.np_uri = "http://purl.org/nanopub/temp/np"
        mock_np.pubinfo = Mock()
        mock_np.pubinfo.add = Mock()
        mock_np.assertion = Mock()
        mock_np.assertion.add = Mock()
        mock_nanopub_class.return_value = mock_np

        reporter = DummyReporter()
        payload = {
            "workflow": {},
            "jobs_full": [],
            "rules_full": [],
        }

        reporter.build_nanopub(payload)

        # Check that ORCID was added to pubinfo
        orcid_calls = [
            call
            for call in mock_np.pubinfo.add.call_args_list
            if "orcid.org" in str(call)
        ]
        assert len(orcid_calls) > 0

    @patch("snakemake_report_plugin_nanopub.load_profile")
    @patch("snakemake_report_plugin_nanopub.Nanopub")
    def test_build_nanopub_with_rules(self, mock_nanopub_class, mock_load_profile):
        """Test build_nanopub processes rules correctly."""
        mock_profile = Mock()
        mock_profile.orcid_id = None
        mock_load_profile.return_value = mock_profile

        mock_np = Mock()
        mock_np._metadata = Mock()
        mock_ns_dict = {}

        def namespace_getitem(key):
            if key not in mock_ns_dict:
                mock_ns_dict[key] = f"http://purl.org/nanopub/temp/{key}"
            return mock_ns_dict[key]

        mock_namespace = MagicMock()
        mock_namespace.__getitem__.side_effect = namespace_getitem
        mock_np._metadata.namespace = mock_namespace
        mock_np._metadata.np_uri = "http://purl.org/nanopub/temp/np"
        mock_np.pubinfo = Mock()
        mock_np.pubinfo.add = Mock()
        mock_np.assertion = Mock()
        mock_np.assertion.add = Mock()
        mock_nanopub_class.return_value = mock_np

        reporter = DummyReporter()
        payload = {
            "workflow": {},
            "jobs_full": [],
            "rules_full": [
                {
                    "name": "test_rule",
                    "wrapper": "bio/bwa/mem",
                    "input": ["in.txt"],
                    "output": ["out.txt"],
                    "params": ["--param1"],
                }
            ],
        }

        reporter.build_nanopub(payload)

        # Check that rules were processed
        assert mock_np.assertion.add.called

    def test_post_init_sets_attributes(self):
        """Test __post_init__ sets required attributes."""
        reporter = DummyReporter()
        assert reporter.dry_run is False
        assert reporter.logger is not None
        assert reporter.generated_at is not None

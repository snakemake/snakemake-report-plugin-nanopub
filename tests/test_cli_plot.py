import logging

import pytest

import snakemake_report_plugin_nanopub_graph as cli


def test_clean_whitespace():
    assert cli._clean_whitespace("hello   world") == "hello world"
    assert cli._clean_whitespace("  spaced  ") == "spaced"
    assert cli._clean_whitespace("\t\n  mixed  \n\t") == "mixed"


def test_shorten():
    text = "a" * 100
    shortened = cli._shorten(text, limit=50)
    assert len(shortened) == 50
    assert shortened.endswith("…")
    assert cli._shorten("short", limit=100) == "short"


def test_wrap_for_html():
    wrapped = cli._wrap_for_html("one two three four five", width=10)
    assert "<BR" in wrapped
    assert "one" in wrapped
    assert "five" in wrapped


def test_strip_display_prefix():
    assert cli._strip_display_prefix("https://w3id.org/np/RAexample") == "RAexample"
    assert cli._strip_display_prefix("http://w3id.org/np/RAexample") == "RAexample"
    assert cli._strip_display_prefix("urn:example") == "urn:example"


def test_node_label_strips_http_np_prefix_and_omits_description_when_requested():
    label = cli._node_label(
        title="Workflow Configuration",
        description="this should not be rendered",
        nanopub_id="http://w3id.org/np/RAexample123",
        text_width=60,
        include_description=False,
    )

    assert "http://w3id.org/np/" not in label
    assert "RAexample123" in label
    assert "this should not be rendered" not in label


def test_build_dot_workflow_configuration_has_no_description_and_stripped_id(monkeypatch):
    monkeypatch.setattr(
        cli,
        "deduce_description",
        lambda nanopub_id, logger, node_title: f"description for {node_title}",
    )

    dot = cli.build_dot(
        dataset_id="https://w3id.org/np/RAdataset",
        workflow_id="https://w3id.org/np/RAworkflow",
        workflow_configuration_id="http://w3id.org/np/RAworkflowconfig",
        report_id="https://w3id.org/np/RAreport",
        line_color="dark brick red",
        text_width=60,
        logger=logging.getLogger("test"),
    )

    # Workflow configuration node should not include any description content.
    assert "description for Workflow Configuration" not in dot

    # Prefix should be stripped for this node as well.
    assert "http://w3id.org/np/RAworkflowconfig" not in dot
    assert "RAworkflowconfig" in dot

    # Keep edge labels slightly away from edges without switching to xlabels.
    assert "labelfloat=true" in dot


def test_resolve_line_color():
    assert cli._resolve_line_color("dark brick red") == "#8B3A3A"
    assert cli._resolve_line_color("DARK BRICK RED") == "#8B3A3A"
    assert cli._resolve_line_color("blue") == "blue"


def test_description_from_url():
    desc = cli._description_from_url("https://example.com/path/to/resource")
    assert "example.com" in desc
    assert "resource" in desc


def test_artifact_code_from_nanopub_id():
    assert cli._artifact_code_from_nanopub_id("https://w3id.org/np/RAexample123") == "RAexample123"
    assert cli._artifact_code_from_nanopub_id("https://w3id.org/np/RAexample123/") == "RAexample123"


# ---------------------------------------------------------------------------
# Additional branch coverage
# ---------------------------------------------------------------------------


def test_wrap_for_html_empty_string():
    """Empty input → empty output (covers the 'if not words: return ""' branch)."""
    assert cli._wrap_for_html("") == ""


def test_wrap_for_html_long_word_with_preceding_text():
    """A short word followed by a word longer than width exercises the inner
    while-loop that splits oversized words and flushes the current line first."""
    result = cli._wrap_for_html("hi " + "x" * 25, width=10)
    # The result must contain line-breaks and include the long word split.
    assert "<BR" in result
    assert "hi" in result
    assert "x" * 10 in result


def test_description_from_url_no_tail():
    """URL with no meaningful path segment should return just the host."""
    assert cli._description_from_url("https://example.com") == "example.com"
    assert cli._description_from_url("https://example.com/") == "example.com"


def test_context_is_assertion_none():
    """None context should return False."""
    assert cli._context_is_assertion(None) is False


def test_context_is_assertion_true():
    """A context URI ending with 'assertion' should return True."""
    assert cli._context_is_assertion("http://example.com/np/assertion") is True


def test_context_is_assertion_false():
    """A context URI not ending with 'assertion' should return False."""
    assert cli._context_is_assertion("http://example.com/np/pubinfo") is False


def test_parse_nanopub_graph_content_type_turtle():
    """Valid Turtle data with a 'text/turtle' content-type header should parse."""
    data = '<http://example.com/s> <http://purl.org/dc/terms/description> "hello" .'
    graph = cli._parse_nanopub_graph(data, "text/turtle", logging.getLogger("test"))
    assert graph is not None
    assert len(list(graph)) >= 1


def test_parse_nanopub_graph_content_type_nquads():
    """Valid N-Quads data with 'application/n-quads' header should parse."""
    data = '<http://example.com/s> <http://purl.org/dc/terms/description> "hello" <http://example.com/g> .\n'
    graph = cli._parse_nanopub_graph(data, "application/n-quads", logging.getLogger("test"))
    assert graph is not None


def test_parse_nanopub_graph_content_type_rdf_xml():
    """Valid RDF/XML with 'application/rdf+xml' header should parse."""
    data = (
        '<?xml version="1.0"?>'
        '<rdf:RDF xmlns:rdf="http://www.w3.org/1999/02/22-rdf-syntax-ns#"'
        '         xmlns:dc="http://purl.org/dc/terms/">'
        '  <rdf:Description rdf:about="http://example.com/s">'
        "    <dc:description>hello</dc:description>"
        "  </rdf:Description>"
        "</rdf:RDF>"
    )
    graph = cli._parse_nanopub_graph(data, "application/rdf+xml", logging.getLogger("test"))
    assert graph is not None


def test_parse_nanopub_graph_content_type_jsonld():
    """Valid JSON-LD with 'application/ld+json' header should parse."""
    data = (
        '{"@context": {"dc": "http://purl.org/dc/terms/"},'
        ' "@id": "http://example.com/s",'
        ' "dc:description": "hello"}'
    )
    graph = cli._parse_nanopub_graph(data, "application/ld+json", logging.getLogger("test"))
    assert graph is not None


def test_parse_nanopub_graph_content_type_trig():
    """Valid TriG with 'application/trig' header should parse."""
    data = (
        "@prefix dc: <http://purl.org/dc/terms/> .\n"
        "@prefix ex: <http://example.com/> .\n"
        "ex:g { ex:s dc:description 'hello' . }\n"
    )
    graph = cli._parse_nanopub_graph(data, "application/trig", logging.getLogger("test"))
    assert graph is not None


def test_parse_nanopub_graph_all_formats_fail():
    """Garbage data should cause all format parsers to fail → returns None."""
    garbage = "GARBAGE GARBAGE GARBAGE $$$ !!!"
    graph = cli._parse_nanopub_graph(garbage, "", logging.getLogger("test"))
    assert graph is None


def test_deduce_description_network_failure():
    """When urlopen raises, deduce_description should return the URL-based fallback."""
    from unittest.mock import patch

    logger = logging.getLogger("test")
    with patch("snakemake_report_plugin_nanopub_graph.urlopen", side_effect=Exception("net error")):
        result = cli.deduce_description("https://w3id.org/np/RAtest", logger, "Test Node")

    assert "w3id.org" in result or "RAtest" in result


def test_deduce_description_graph_parse_fails():
    """When urlopen succeeds but the data is unparsable, the fallback is returned."""
    from unittest.mock import patch, MagicMock

    mock_response = MagicMock()
    mock_response.headers.get.return_value = "text/plain"
    mock_response.read.return_value = b"NOT VALID RDF"

    logger = logging.getLogger("test")
    with patch("snakemake_report_plugin_nanopub_graph.urlopen") as mock_urlopen:
        mock_urlopen.return_value.__enter__.return_value = mock_response
        mock_urlopen.return_value.__exit__.return_value = False
        result = cli.deduce_description("https://w3id.org/np/RAtest", logger, "Test Node")

    assert "w3id.org" in result or "RAtest" in result


def test_deduce_description_with_matching_triple():
    """When a graph with a matching predicate/assertion context is returned,
    deduce_description should extract and return the literal value."""
    from unittest.mock import patch, MagicMock

    trig_data = (
        "@prefix dc: <http://purl.org/dc/terms/> .\n"
        "@prefix ex: <http://example.com/np/> .\n"
        "ex:assertion { ex:subject dc:description 'My workflow description' . }\n"
    )
    mock_response = MagicMock()
    mock_response.headers.get.return_value = "application/trig"
    mock_response.read.return_value = trig_data.encode("utf-8")

    logger = logging.getLogger("test")
    with patch("snakemake_report_plugin_nanopub_graph.urlopen") as mock_urlopen:
        mock_urlopen.return_value.__enter__.return_value = mock_response
        mock_urlopen.return_value.__exit__.return_value = False
        result = cli.deduce_description("https://w3id.org/np/RAtest", logger, "Test Node")

    assert "My workflow description" in result

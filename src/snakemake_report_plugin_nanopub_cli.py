"""Standalone CLI to plot a nanopub knowledge graph with Graphviz."""

from __future__ import annotations

import argparse
import html
import logging
import re
import shutil
import subprocess
import sys
import tempfile
import importlib
from pathlib import Path
from urllib.parse import urlparse
from urllib.request import Request, urlopen

PREDICATES = [
    "https://w3id.org/np/snakemake/description",
    "http://purl.org/dc/terms/description",
    "http://purl.org/dc/elements/1.1/description",
    "https://schema.org/description",
    "http://schema.org/description",
    "http://purl.org/dc/terms/title",
    "http://purl.org/dc/elements/1.1/title",
    "http://www.w3.org/2000/01/rdf-schema#label",
    "https://schema.org/name",
    "http://schema.org/name",
    "http://www.w3.org/2000/01/rdf-schema#comment",
]
NP_DISPLAY_PREFIX = "https://w3id.org/np/"
LOGGER_NAME = "snakemake_report_plugin_nanopub.cli"


def _clean_whitespace(value: str) -> str:
    return re.sub(r"\s+", " ", value).strip()


def _shorten(value: str, limit: int = 320) -> str:
    if len(value) <= limit:
        return value
    return value[: limit - 1].rstrip() + "…"


def _wrap_for_html(value: str, width: int = 60) -> str:
    words = value.split()
    if not words:
        return ""

    lines = []
    current = ""

    for original_word in words:
        word = original_word
        while len(word) > width:
            if current:
                lines.append(current)
                current = ""
            lines.append(word[:width])
            word = word[width:]

        if not current:
            current = word
            continue

        candidate = f"{current} {word}"
        if len(candidate) <= width:
            current = candidate
        else:
            lines.append(current)
            current = word

    if current:
        lines.append(current)

    return "<BR ALIGN=\"LEFT\"/>".join(html.escape(line) for line in lines)


def _description_from_url(url: str) -> str:
    parsed = urlparse(url)
    host = parsed.netloc or "nanopub"
    tail = parsed.path.rstrip("/").split("/")[-1]
    if tail:
        return f"{host} / {tail}"
    return host



def _artifact_code_from_nanopub_id(nanopub_id: str) -> str:
    parsed = urlparse(nanopub_id)
    return parsed.path.rstrip("/").split("/")[-1]


def _parse_nanopub_graph(data: str, content_type: str, logger: logging.Logger):
    try:
        rdflib = importlib.import_module("rdflib")
    except Exception:
        return None
    ConjunctiveGraph = rdflib.ConjunctiveGraph

    formats = []
    lowered = (content_type or "").lower()
    if "trig" in lowered:
        formats.append("trig")
    elif "n-quads" in lowered or "nquads" in lowered:
        formats.append("nquads")
    elif "turtle" in lowered:
        formats.append("turtle")
    elif "rdf+xml" in lowered or "xml" in lowered:
        formats.append("xml")
    elif "ld+json" in lowered or "json" in lowered:
        formats.append("json-ld")

    formats.extend(["trig", "nquads", "turtle", "xml", "json-ld"])

    graph = ConjunctiveGraph()
    seen = set()
    for fmt in formats:
        if fmt in seen:
            continue
        seen.add(fmt)
        try:
            graph.parse(data=data, format=fmt)
            logger.debug("Parsed nanopub graph using format '%s'.", fmt)
            return graph
        except Exception:
            logger.error("Failed to parse nanopub graph as format '%s'.", fmt)
            continue
    return None


def _context_is_assertion(context) -> bool:
    if context is None:
        return False
    context_str = str(context)
    return context_str.rstrip("/").endswith("assertion")


def deduce_description(
    nanopub_id: str,
    logger: logging.Logger,
    node_title: str,
) -> str:
    fallback = _description_from_url(nanopub_id)
    logger.debug("[%s] Resolving description for nanopub: %s", node_title, nanopub_id)
    logger.debug("[%s] URL-based fallback description: %s", node_title, fallback)
    fetch_candidates = [nanopub_id]
    if nanopub_id.startswith(NP_DISPLAY_PREFIX) and not nanopub_id.endswith(".trig"):
        fetch_candidates.append(f"{nanopub_id}.trig")

    graph = None
    for candidate in fetch_candidates:
        try:
            req = Request(
                candidate,
                headers={
                    "Accept": (
                        "application/trig, application/n-quads, text/turtle, "
                        "application/rdf+xml, application/ld+json, text/plain"
                    )
                },
            )
            with urlopen(req, timeout=12) as response:
                content_type = response.headers.get("Content-Type", "")
                data = response.read().decode("utf-8", errors="replace")
                logger.debug(
                    "[%s] Downloaded nanopub response from %s (content-type='%s', chars=%d).",
                    node_title,
                    candidate,
                    content_type,
                    len(data),
                )
        except Exception:
            logger.debug(
                "[%s] Failed to download candidate %s",
                node_title,
                candidate,
                exc_info=True,
            )
            continue

        graph = _parse_nanopub_graph(data=data, content_type=content_type, logger=logger)
        if graph is not None:
            break

    if graph is None:
        logger.debug(
            "[%s] RDF parse failed for all supported formats. Using fallback description.",
            node_title,
        )
        return fallback

    try:
        rdflib = importlib.import_module("rdflib")
    except Exception:
        logger.debug(
            "[%s] rdflib import failed during triple scan. Using fallback description.",
            node_title,
            exc_info=True,
        )
        return fallback
    URIRef = rdflib.URIRef

    best_value = None
    best_score = -1

    for idx, predicate in enumerate(PREDICATES):
        logger.debug("[%s] Scanning predicate: %s", node_title, predicate)
        for _, _, obj, context in graph.quads((None, URIRef(predicate), None, None)):
            value = _clean_whitespace(str(obj))
            if not value:
                continue

            score = (len(PREDICATES) - idx) * 100
            if _context_is_assertion(context):
                score += 1_000

            if score > best_score:
                best_score = score
                best_value = value
                logger.debug(
                    "[%s] Candidate via '%s' (context=%s, score=%d): %s",
                    node_title,
                    predicate,
                    context,
                    score,
                    value,
                )

    if best_value:
        logger.debug("[%s] Selected description: %s", node_title, best_value)
        return _shorten(best_value)

    logger.debug(
        "[%s] No matching description triple found. Using fallback description.",
        node_title,
    )
    return fallback


def _node_label(
    title: str,
    description: str,
    nanopub_id: str,
    text_width: int,
) -> str:
    display_id = nanopub_id
    if display_id.startswith(NP_DISPLAY_PREFIX):
        display_id = display_id[len(NP_DISPLAY_PREFIX) :]
    safe_id = _wrap_for_html(display_id, width=text_width)
    
    description_row = ""
    if description and description.strip():
        safe_description = _wrap_for_html(description, width=text_width)
        description_row = f"<TR><TD ALIGN=\"LEFT\">{safe_description}</TD></TR>"
    
    return (
        "<<TABLE BORDER=\"0\" CELLBORDER=\"0\" CELLPADDING=\"2\">"
        f"<TR><TD ALIGN=\"CENTER\"><B>{html.escape(title)}</B></TD></TR>"
        f"{description_row}"
        f"<TR><TD ALIGN=\"LEFT\"><FONT COLOR=\"lightgrey\">{safe_id}</FONT></TD></TR>"
        "</TABLE>>"
    )


def _resolve_line_color(value: str) -> str:
    if value.strip().lower() == "dark brick red":
        return "#8B3A3A"
    return value


def build_dot(
    dataset_id: str,
    workflow_id: str,
    workflow_configuration_id: str,
    report_id: str,
    line_color: str,
    text_width: int,
    logger: logging.Logger,
) -> str:
    dataset_description = deduce_description(
        dataset_id,
        logger=logger,
        node_title="Dataset",
    )
    workflow_description = deduce_description(
        workflow_id,
        logger=logger,
        node_title="Workflow",
    )
    workflow_configuration_description = ""
    report_description = deduce_description(
        report_id,
        logger=logger,
        node_title="Workflow Report",
    )

    dataset_label = _node_label(
        "Dataset",
        dataset_description,
        dataset_id,
        text_width=text_width,
    )
    workflow_label = _node_label(
        "Workflow",
        workflow_description,
        workflow_id,
        text_width=text_width,
    )
    workflow_configuration_label = _node_label(
        "Workflow Configuration",
        workflow_configuration_description,
        workflow_configuration_id,
        text_width=text_width,
    )
    report_label = _node_label(
        "Workflow Report",
        report_description,
        report_id,
        text_width=text_width,
    )

    graphviz_color = _resolve_line_color(line_color)
    edge_label_color = "black"
    dot = f"""digraph NanopubKnowledgeGraph {{
        rankdir=TB;
    graph [bgcolor=\"white\"];
        node [shape=box, style=\"rounded\", color=\"{graphviz_color}\", penwidth=1.6, fontname=\"Helvetica\", fixedsize=false, margin=\"0.12,0.08\"];
        edge [color=\"{graphviz_color}\", fontcolor=\"{edge_label_color}\", penwidth=1.6, fontname=\"Helvetica\"];

  dataset [label={dataset_label}];
  workflow [label={workflow_label}];
    workflow_configuration [label={workflow_configuration_label}];
  report [label={report_label}];

        {{ rank=same; workflow; report; }}
        {{ rank=same; dataset; workflow_configuration; }}

  dataset -> workflow [label=\"used by\"];
    workflow_configuration -> workflow [label="used this configuration"];
  workflow -> report [label=\"produces\"];
    report -> dataset [label=\"based upon\"];
}}
"""
    return dot


def render_graph(dot: str, output_path: Path, graph_format: str) -> None:
    dot_bin = shutil.which("dot")
    if dot_bin is None:
        raise RuntimeError(
            "Graphviz 'dot' executable not found. Please install graphviz."
        )

    output_path.parent.mkdir(parents=True, exist_ok=True)

    with tempfile.NamedTemporaryFile("w", suffix=".dot", delete=False) as tmp_dot:
        tmp_dot.write(dot)
        tmp_dot_path = Path(tmp_dot.name)

    try:
        subprocess.run(
            [
                dot_bin,
                f"-T{graph_format}",
                str(tmp_dot_path),
                "-o",
                str(output_path),
            ],
            check=True,
        )
    finally:
        tmp_dot_path.unlink(missing_ok=True)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Plot a four-node nanopub knowledge graph using Graphviz.",
    )
    parser.add_argument(
        "--dataset-nanopub-id",
        dest="dataset_nanopub_id",
        required=True,
        help="Nanopub ID (URL) of the dataset.",
    )
    parser.add_argument(
        "--workflow-nanopub-id",
        dest="workflow_nanopub_id",
        required=True,
        help="Nanopub ID (URL) of the workflow.",
    )
    parser.add_argument(
        "--workflow-configuration-id",
        dest="workflow_configuration_id",
        required=True,
        help="Nanopub ID (URL) of the workflow configuration.",
    )
    parser.add_argument(
        "--report-nanopub-id",
        dest="report_nanopub_id",
        required=True,
        help="Nanopub ID (URL) of the report.",
    )
    parser.add_argument(
        "-o",
        "--output",
        default="nanopub-knowledge-graph.png",
        help="Output graph file path (default: nanopub-knowledge-graph.png).",
    )
    parser.add_argument(
        "--format",
        default=None,
        help=(
            "Graphviz output format (e.g. svg, png, pdf). Defaults to the output "
            "file extension or png when no extension is present."
        ),
    )
    parser.add_argument(
        "--line-color",
        default="dark brick red",
        help="Color for node borders and arrows (default: dark brick red).",
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Enable debug logging for nanopub description extraction.",
    )
    parser.add_argument(
        "--text-width",
        type=int,
        default=60,
        help=(
            "Approximate wrapping width in characters for description and "
            "nanopub ID lines (default: 60)."
        ),
    )
    return parser.parse_args()


def _setup_logger(verbose: bool) -> logging.Logger:
    level = logging.DEBUG if verbose else logging.WARNING
    logging.basicConfig(level=level, format="%(levelname)s: %(message)s")
    return logging.getLogger(LOGGER_NAME)


def main() -> None:
    args = parse_args()
    if args.text_width < 20:
        print("Error: --text-width must be >= 20", file=sys.stderr)
        sys.exit(2)

    logger = _setup_logger(args.verbose)
    output_path = Path(args.output)
    graph_format = args.format or output_path.suffix.lstrip(".") or "png"

    try:
        dot = build_dot(
            dataset_id=args.dataset_nanopub_id,
            workflow_id=args.workflow_nanopub_id,
            workflow_configuration_id=args.workflow_configuration_id,
            report_id=args.report_nanopub_id,
            line_color=args.line_color,
            text_width=args.text_width,
            logger=logger,
        )
        render_graph(dot=dot, output_path=output_path, graph_format=graph_format)
        logger.debug("Graph rendering completed: %s", output_path)
    except Exception as exc:
        print(f"Error: {exc}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()

"""Standalone CLI to plot a nanopub knowledge graph with Graphviz."""

from __future__ import annotations

import argparse
import logging
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

from snakemake_report_plugin_nanopub_graph import (  # noqa: F401  (re-exported for tests)
    LOGGER_NAME,
    NP_DISPLAY_PREFIXES,
    PREDICATES,
    _artifact_code_from_nanopub_id,
    _clean_whitespace,
    _context_is_assertion,
    _description_from_url,
    _node_label,
    _parse_nanopub_graph,
    _resolve_line_color,
    _shorten,
    _strip_display_prefix,
    _wrap_for_html,
    build_dot,
    deduce_description,
)


def _graphviz_output_format(graph_format: str) -> str:
    # Use the Cairo SVG backend so text is outlined as paths and does not
    # depend on external fonts when typeset in downstream tools.
    if graph_format.lower() == "svg":
        return "svg:cairo"
    return graph_format


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
        graphviz_format = _graphviz_output_format(graph_format)
        subprocess.run(
            [
                dot_bin,
                f"-T{graphviz_format}",
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

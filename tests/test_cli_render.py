from pathlib import Path
from unittest.mock import patch

import snakemake_report_plugin_nanopub_cli as cli_main


def test_graphviz_output_format_uses_cairo_for_svg():
    assert cli_main._graphviz_output_format("svg") == "svg:cairo"
    assert cli_main._graphviz_output_format("SVG") == "svg:cairo"


def test_graphviz_output_format_passes_non_svg_through():
    assert cli_main._graphviz_output_format("png") == "png"
    assert cli_main._graphviz_output_format("pdf") == "pdf"


def test_render_graph_uses_svg_cairo_backend(tmp_path):
    out = tmp_path / "graph.svg"

    with patch("snakemake_report_plugin_nanopub_cli.shutil.which", return_value="dot"):
        with patch("snakemake_report_plugin_nanopub_cli.subprocess.run") as run_mock:
            cli_main.render_graph("digraph G {}", out, "svg")

    cmd = run_mock.call_args.args[0]
    assert "-Tsvg:cairo" in cmd
    assert str(out) in cmd


def test_render_graph_uses_requested_backend_for_non_svg(tmp_path):
    out = tmp_path / "graph.png"

    with patch("snakemake_report_plugin_nanopub_cli.shutil.which", return_value="dot"):
        with patch("snakemake_report_plugin_nanopub_cli.subprocess.run") as run_mock:
            cli_main.render_graph("digraph G {}", out, "png")

    cmd = run_mock.call_args.args[0]
    assert "-Tpng" in cmd
    assert str(out) in cmd

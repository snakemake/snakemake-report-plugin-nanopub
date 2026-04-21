[![Snakemake](https://img.shields.io/badge/snakemake-≥9.1.3-brightgreen.svg)](https://snakemake.github.io)
[![Conventional Commits](https://img.shields.io/badge/Conventional%20Commits-1.0.0-%23FE5196?logo=conventionalcommits&logoColor=white)](https://conventionalcommits.org)

**Please note**: This plugin is work in progress and NOT ready to use.

**Its intention**:

- users will be enabled to automatically create a [nanopub](https://nanopub.net/) using a workflow's metadata
- this nanopub can subsequently be referenced in publications and thereby covering __all__ metadata necessary to scrutinize an analysis (all too often crucial data are missing from publications)

## CLI: plot nanopub knowledge graph

After installation, run:

```bash
plot-nanopub-knowledge-graph \
	--dataset-nanopub-id <dataset_nanopub_url> \
	--workflow-nanopub-id <workflow_nanopub_url> \
	--workflow-configuration-id <workflow_configuration_nanopub_url> \
	--report-nanopub-id <report_nanopub_url> \
	-o graph.png
```

This generates a Graphviz plot with four rounded boxes (`Dataset`, `Workflow`, `Workflow Configuration`, `Workflow Report`) and arrows labeled `used by`, `used this configuration`, `produces`, and `based upon`.

Optional settings:

- `--line-color "dark brick red"` (default) for node border and arrow color
- `--format svg|png|pdf` to override output format
- `--verbose` to print debug logs for nanopub description extraction
- `--text-width 60` to control line wrapping width in box text

Default output format is `png`.

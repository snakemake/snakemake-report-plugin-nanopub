### How this Plugin works

This is a reporter plugin. It enables to publish a [Nanopublication](https://nanopub.net/) containing all metadata necessary to reproduce a given workflow. The resulting nanopublication contains the configuration and all job specifications.

The idea is to allow using linking all metadata of a workflow into a Material & Methods section of scientific paper as a Nanopublication - a worldwide accessible, persistent and unique Wikidata link. Additionally, the plugin allows to create a graphical representation of a knowledge graph consisting of a worklow, its input configuration, a report and input data to illustrate the work done.

### Installation

Installing this plugin into your Snakemake base environment using pip or conda will ensure dependency resolution for `nanopub-py` library as well.

#### Setup

The plugin will check whether a nanopub setup is present. You are advised to follow the introduction [here](https://saranjeetkaur.github.io/nanopub_101) and perform a setup step after the installation as described with the [nanopub-py library documentation](https://nanopublication.github.io/nanopub-py). Basically, perform

```Shell
$ np setup
```

### Contributions

We welcome bug reports, feature requests, and pull requests!
Please report issues specific to this plugin [in the plugin's GitHub repository](https://github.com/snakemake/snakemake-report-plugin-nanopub/issues).

### Usage

#### Preliminaries: Registering your Workflow as a Nanopublication

Before registering metadata for a workflow, the workflow itself ought to be registered manually using (this template](https://w3id.org/np/RAOT7z3RA0XYlHIikne8rfUUYZrtHyrzXBD1HpI_GvcRk). 


### Registering your Workflow Metadata

To register your workflow metadata with this plugin run Snakemake with

```Shell
$ snakemake ... --reporter nanopub --report-nanopub-workflow-id <registered workflow nanopub>
```

This will inform you how much of all metadata are registered:
- the configuration and description will be registered in any case
- to avoid hitting the nanopublication size limit the rule information is most likely removed (it is redundant) and the job information is stripped of execution times and rule information until the size limit is observed.

In the end you will see a line like:

```
Nanopub published successfully: ('https://w3id.org/np/<nanopub ID>', 'https://test.registry.knowledgepixels.com/np/')
Report created.
```

You can navigate to the test registry and check your nanopub. If you want to register with main server put `--report-nanopub-main-server`. This is a security measure to avoid registering too many undesired nanopubs (e.g. accidentally for ill-configured runs).

Optional parameters are:

- `--report-nanopub-dry-run` will print the nanopublication graph information on the terminal before shrinking
- `--report-nanopub-output-path` allows for an optional JSON output

### The Command Line Tool for plotting Knowledge Graphs

The plugin offers a stand-alone command line tool, too: `plot-nanopub-knowledge-graph`. 

When you run it, you get a graphical representation of your workflow its in- and outputs like this:

![Small knowledge graph of a workflow, its dataset, report and configuration.](images/example_knowledgegraph.png)

In order to accomplish this, an uploaded report HTML (generated with Snakemake's `--report` flag) can be registered with [this template](https://w3id.org/np/RAsmNjwvzjYfc8Hson0gyjSL6Oov3nZZEfRy7TOFtO5I8). 

If you want to, register your data as a nanopub, too. I.e. using [this template](https://w3id.org/np/RAE98XsERuzJNczFlZk-uIVRbnCuJMH1ifl1wMLk8_7Pc) -- any other data set template is fine and might offer a more fine-grained description, than this simple one.

Then running the command line tool will yield a knowledge graph as the one you see above:

```Shell
$ plot-nanopub-knowledge-graph \
`--dataset-nanopub-id <dataset nanopub id> \
--workflow-nanopub-id <workflow nanopub id> \
--report-nanopub-id <report nanopub id> \
--workflow-configuration-id <configuration nanopub id> \
-o example_knowledgegraph.png
```

You can change
- the output format with `--format` (e.g. svg, png, pdf). It defaults to the output file extension present.
- the line color with `--line-color (in HTML format).
- the text width with `--text-width` (as a number, it defaults to 60)

The `*-nanopub-id` parameters are mandatory and may be given with their `https://w3id.org/np/` prefix.



#!/usr/bin/env python3
"""
Script to visualize nanopub workflows and related resources.

This script takes nanopub links as input and creates a visualization showing:
- The main nanopubs (workflow, report, dataset) 
- Their descriptions 
- Nanopub links 
- Assertion templates pointing to the respective nanopubs as regular boxes
- Interconnections with rounded arrows
"""

import sys
from typing import Dict, List, Set, Tuple
from urllib.parse import urlparse

try:
    import graphviz
except ImportError:
    print("Please install graphviz: pip install graphviz")
    sys.exit(1)

from nanopub import Nanopub
from rdflib.namespace import DCTERMS, RDFS
from rdflib import URIRef, Literal


# Color scheme
BRICK_RED = "#8B4646"
LIGHT_GREY = "#D3D3D3"
MEDIUM_GREY = "#A9A9A9"
DARK_GREY = "#696969"


class NanopubWorkflowPlotter:
    """
    A plotter for visualizing nanopub workflows and related resources.
    """

    def __init__(self, title: str = "Nanopub Workflow Visualization", output_format: str = "png"):
        """
        Initialize the plotter.
        
        Args:
            title: Title for the graph
            output_format: Output format ('png', 'svg', 'pdf', etc.)
        """
        self.title = title
        self.output_format = output_format
        self.graph = graphviz.Digraph(
            comment=title,
            format=output_format,
            engine='dot',
            graph_attr={
                'rankdir': 'LR',
                'splines': 'curved',
                'overlap': 'false',
                'sep': '+0.5',
            }
        )
        self.graph.attr('node', shape='box', style='rounded,filled', fontname='Arial')
        self.nanopubs_data: Dict = {}
        self.assertion_templates: Dict[str, Set[str]] = {}

    def fetch_nanopub(self, uri: str) -> Tuple[Nanopub, str]:
        """
        Fetch a nanopub from the given URI.
        
        Args:
            uri: The nanopub URI (e.g., https://w3id.org/np/...)
        
        Returns:
            Tuple of (Nanopub object, short identifier)
        """
        try:
            np = Nanopub(source_uri=uri)
            # Extract short ID from URI
            short_id = uri.split('/')[-1]
            return np, short_id
        except Exception as e:
            print(f"Error fetching nanopub {uri}: {e}")
            return None, None

    def extract_description(self, nanopub: Nanopub) -> str:
        """
        Extract the description from a nanopub's assertion graph.
        
        Args:
            nanopub: The Nanopub object
        
        Returns:
            Description string or empty string if not found
        """
        try:
            for obj in nanopub.assertion.objects(None, DCTERMS.description):
                if isinstance(obj, Literal):
                    return str(obj)[:100]  # Truncate to 100 chars
        except Exception as e:
            print(f"Error extracting description: {e}")
        return ""

    def extract_assertion_templates(self, nanopub: Nanopub) -> List[str]:
        """
        Extract assertion templates from a nanopub's assertion graph.
        
        These are identified by triples with rdf:type pointing to ntemplate types.
        
        Args:
            nanopub: The Nanopub object
        
        Returns:
            List of template descriptions
        """
        templates = []
        try:
            # Look for placeholder types from NTEMPLATE namespace
            ntemplate_ns = "https://w3id.org/np/o/ntemplate/"
            
            for subject, obj in nanopub.assertion.subject_objects(RDFS.label):
                if isinstance(obj, Literal):
                    label = str(obj)
                    # Check if this subject has a type
                    for type_obj in nanopub.assertion.objects(subject, 
                                                             URIRef("http://www.w3.org/1999/02/22-rdf-syntax-ns#type")):
                        if ntemplate_ns in str(type_obj):
                            templates.append(label)
                            break
        except Exception as e:
            print(f"Error extracting templates: {e}")
        
        return templates

    def add_nanopub_node(self, short_id: str, label: str, description: str = "", uri: str = ""):
        """
        Add a nanopub node to the graph with rounded corners.
        
        Args:
            short_id: Short identifier for the node
            label: Human-readable label
            description: Optional description text
            uri: The nanopub URI to display in light grey
        """
        # Build HTML-like label for graphviz
        rows = [f"<B>{label}</B>"]
        if description:
            rows.append(f"<FONT POINT-SIZE='9'>{description}</FONT>")
        if description and uri:
            rows.append("")  # Add spacing between description and URI
        if uri:
            short_uri = uri.split('/')[-1] if '/' in uri else uri
            rows.append(f"<FONT COLOR='{LIGHT_GREY}' POINT-SIZE='8'>{short_uri}</FONT>")
        
        html_label = "<" + "<BR/>".join(rows) + ">"
        
        self.graph.node(
            short_id,
            html_label,
            fillcolor='white',
            fontcolor='black',
            fontname='Arial',
            shape='box',
            style='rounded,filled',
            color=BRICK_RED,
            penwidth='1.5',
            margin='0.3,0.2'
        )

    def add_template_node(self, template_id: str, template_label: str):
        """
        Add an assertion template node to the graph (non-rounded box).
        
        Args:
            template_id: Unique identifier for the template
            template_label: Human-readable label
        """
        self.graph.node(
            template_id,
            template_label,
            fillcolor=LIGHT_GREY,
            fontcolor=DARK_GREY,
            fontsize='10',
            shape='box',
            style='filled',
            margin='0.2,0.15'
        )

    def add_link_annotation(self, node_id: str, uri: str):
        """
        Add a link annotation node showing the nanopub URI.
        
        Args:
            node_id: The main node ID
            uri: The nanopub URI
        """
        link_node_id = f"{node_id}_link"
        short_uri = uri.split('/')[-1] if '/' in uri else uri
        
        self.graph.node(
            link_node_id,
            short_uri,
            fillcolor=LIGHT_GREY,
            fontcolor=MEDIUM_GREY,
            fontsize='9',
            shape='box',
            style='filled',
            margin='0.2,0.1'
        )
        
        # Connect with a subtle edge
        self.graph.edge(node_id, link_node_id, color=MEDIUM_GREY, style='dashed', arrowsize='0.5')

    def add_edge_with_arrow(self, from_node: str, to_node: str, label: str = "", 
                           arrowhead: str = 'vee', color: str = BRICK_RED):
        """
        Add an edge with a rounded arrow style.
        
        Args:
            from_node: Source node ID
            to_node: Target node ID
            label: Optional edge label
            arrowhead: Arrow type ('vee', 'dot', 'open')
            color: Edge color
        """
        self.graph.edge(
            from_node,
            to_node,
            label=label,
            color=color,
            arrowsize='1.5',
            arrowhead=arrowhead,
            penwidth='2'
        )

    def plot_workflow(self, workflow_uri: str, report_uri: str, dataset_uri: str,
                     output_file: str = "nanopub_workflow", output_format: str = None):
        """
        Create a visualization of the workflow with report and dataset.
        
        Args:
            workflow_uri: URI of the Snakemake workflow nanopub
            report_uri: URI of the report nanopub
            dataset_uri: URI of the dataset nanopub
            output_file: Output file name (without extension)
            output_format: Output format ('png', 'svg', 'pdf'); uses instance format if None
        """
        if output_format:
            self.output_format = output_format
            self.graph.format = output_format
        
        print(f"Fetching nanopubs...")
        
        # Fetch nanopubs
        workflow_np, workflow_id = self.fetch_nanopub(workflow_uri)
        report_np, report_id = self.fetch_nanopub(report_uri)
        dataset_np, dataset_id = self.fetch_nanopub(dataset_uri)
        
        if not all([workflow_np, report_np, dataset_np]):
            print("Error: Could not fetch all nanopubs")
            return
        
        print("Extracting data from nanopubs...")
        
        # Extract data
        workflow_desc = self.extract_description(workflow_np)
        report_desc = self.extract_description(report_np)
        dataset_desc = self.extract_description(dataset_np)
        
        workflow_templates = self.extract_assertion_templates(workflow_np)
        report_templates = self.extract_assertion_templates(report_np)
        dataset_templates = self.extract_assertion_templates(dataset_np)
        
        # Create clusters for each main resource
        with self.graph.subgraph(name='cluster_workflow') as c:
            c.attr('graph', label='Workflow', style='filled', color=LIGHT_GREY, bgcolor='#f0f0f0')
            
            # Add main node with URI
            self.add_nanopub_node(workflow_id, "Snakemake Workflow", workflow_desc, workflow_uri)
            
            # Add templates
            for i, template in enumerate(workflow_templates):
                template_node_id = f"{workflow_id}_template_{i}"
                self.add_template_node(template_node_id, template)
                self.add_edge_with_arrow(
                    template_node_id, 
                    workflow_id,
                    color=MEDIUM_GREY,
                    arrowhead='open'
                )
        
        with self.graph.subgraph(name='cluster_report') as c:
            c.attr('graph', label='Report', style='filled', color=LIGHT_GREY, bgcolor='#f0f0f0')
            
            # Add main node with URI
            self.add_nanopub_node(report_id, "Workflow Report", report_desc, report_uri)
            
            # Add templates
            for i, template in enumerate(report_templates):
                template_node_id = f"{report_id}_template_{i}"
                self.add_template_node(template_node_id, template)
                self.add_edge_with_arrow(
                    template_node_id,
                    report_id,
                    color=MEDIUM_GREY,
                    arrowhead='open'
                )
        
        with self.graph.subgraph(name='cluster_dataset') as c:
            c.attr('graph', label='Dataset', style='filled', color=LIGHT_GREY, bgcolor='#f0f0f0')
            
            # Add main node with URI
            self.add_nanopub_node(dataset_id, "Dataset", dataset_desc, dataset_uri)
            
            # Add templates
            for i, template in enumerate(dataset_templates):
                template_node_id = f"{dataset_id}_template_{i}"
                self.add_template_node(template_node_id, template)
                self.add_edge_with_arrow(
                    template_node_id,
                    dataset_id,
                    color=MEDIUM_GREY,
                    arrowhead='open'
                )
        
        # Add connections between main resources
        self.add_edge_with_arrow(workflow_id, report_id, label="produces", arrowhead='vee')
        self.add_edge_with_arrow(dataset_id, workflow_id, label="used by", arrowhead='vee')
        self.add_edge_with_arrow(dataset_id, report_id, label="input to", arrowhead='vee')
        
        # Render the graph
        print(f"Rendering graph to {output_file}.{self.output_format}...")
        self.graph.render(output_file, cleanup=True)
        print(f"Success! Output saved to {output_file}.{self.output_format}")


def main():
    """Main entry point."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Visualize nanopub workflows")
    parser.add_argument(
        "--format",
        "-f",
        default="png",
        choices=["png", "svg", "pdf", "jpg"],
        help="Output format (default: png)"
    )
    parser.add_argument(
        "workflow_uri",
        nargs="?",
        default="https://w3id.org/np/RAjHDlPDghZzc9ZvQ3uJQNJ9Jd_KAYzZt7dk5PXKgjRyE",
        help="URI of the Snakemake workflow nanopub"
    )
    parser.add_argument(
        "report_uri",
        nargs="?",
        default="https://w3id.org/np/RApK8IUY9KJJkFoasvMJhPQQtT8VvN0IQ__hAxKOeeIuk",
        help="URI of the report nanopub"
    )
    parser.add_argument(
        "dataset_uri",
        nargs="?",
        default="https://w3id.org/np/RAADj5Q7GRdIUraoI2xTbMhe_fF97e4nr6olQlFI8Sfnk",
        help="URI of the dataset nanopub"
    )
    
    args = parser.parse_args()
    
    # Create and run plotter with specified format
    plotter = NanopubWorkflowPlotter(output_format=args.format)
    plotter.plot_workflow(args.workflow_uri, args.report_uri, args.dataset_uri, "nanopub_workflow")


if __name__ == "__main__":
    main()

from dataclasses import dataclass, field
from typing import Optional

from snakemake_interface_report_plugins.reporter import ReporterBase
from snakemake_interface_report_plugins.settings import ReportSettingsBase


# Raise errors that will not be handled within this plugin but thrown upwards to
# Snakemake and the user as WorkflowError.
from snakemake_interface_common.exceptions import WorkflowError  # noqa: F401

from nanopub import Nanopub, NanopubConf, load_profile
from rdflib import Graph
import rdflib


# Optional:
# Define additional settings for your reporter.
# They will occur in the Snakemake CLI as --report-<reporter-name>-<param-name>
# Omit this class if you don't need any.
# Make sure that all defined fields are Optional (or bool) and specify a default value
# of None (or False) or anything else that makes sense in your case.
@dataclass
class ReportSettings(ReportSettingsBase):
    myparam: Optional[int] = field(
        default=None,
        metadata={
            "help": "Some help text",
            # Optionally request that setting is also available for specification
            # via an environment variable. The variable will be named automatically as
            # SNAKEMAKE_REPORT_<reporter-name>_<param-name>, all upper case.
            # This mechanism should ONLY be used for passwords and usernames.
            # For other items, we rather recommend to let people use a profile
            # for setting defaults
            # (https://snakemake.readthedocs.io/en/stable/executing/cli.html#profiles).
            "env_var": False,
            # Optionally specify a function that parses the value given by the user.
            # This is useful to create complex types from the user input.
            "parse_func": ...,
            # If a parse_func is specified, you also have to specify an unparse_func
            # that converts the parsed value back to a string.
            "unparse_func": ...,
            # Optionally specify that setting is required when the reporter is in use.
            "required": True,
            # Optionally specify multiple args with "nargs": "+"
        },
    )


# Required:
# Implementation of your reporter
class Reporter(ReporterBase):
    def __post_init__(self):
        # initialize additional attributes
        # Do not overwrite the __init__ method as this is kept in control of the base
        # class in order to simplify the update process.
        # See https://github.com/snakemake/snakemake-interface-report-plugins/snakemake_interface_report_plugins/reporter.py # noqa: E501
        # for attributes of the base class.
        # In particular, the settings of above ReportSettings class are accessible via
        # self.settings.
        self.metadata = {field.name: field.metadata for field in ReportSettings.__dataclass_fields__.values()}
        

    def render(self):
        """
        The render method is called by Snakemake to generate the report,
        which in this case, is a nanopub and not a graphical display.
        """
        np_conf = NanopubConf(
            use_test_server=True, # will be configurable in the future
            profile=load_profile(),
            add_prov_generated_time=True,
            attribute_publication_to_profile=True,
        )

        my_assertion = Graph()
        
        my_assertion.add((
                rdflib.URIRef("http://example.org/"), # replace with actual subject
                rdflib.RDF.type,
                rdflib.FOAF.assertion,
            ))
        
        np = Nanopub(
            assertion=my_assertion,
            nanopub_conf=np_conf,
        )

        # Add metadata to the nanopub
        for name, metadata_object in self.metadata.items():
            np.add_metadata(
                name=name,
                value=self.settings[name],
                metadata_object=metadata_object,
            )

        # Publish the nanopub
        np.publish()
        # return a value from the render method
        self.logger.info(f"Nanopub published successfully: {np.nanopub_uri}")
        
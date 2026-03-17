from dataclasses import dataclass, field
import datetime
import json
import logging
from pathlib import Path
from typing import Any, Optional
import uuid
import sys
from urllib.parse import quote

from nanopub import Nanopub, NanopubConf, load_profile
from rdflib import Literal, Namespace, RDF, URIRef
from rdflib.namespace import DCTERMS, RDFS
from rdflib.namespace import XSD

from snakemake.report.rulegraph_spec import rulegraph_spec
from snakemake.report.html_reporter import data as html_data
from snakemake_interface_common.exceptions import WorkflowError
from snakemake_interface_report_plugins.reporter import ReporterBase
from snakemake_interface_report_plugins.settings import ReportSettingsBase
from .validation import bind_nanopub_prefixes
from .extraction import (
    extract_jobs,
    extract_rules_full,
    extract_workflow_inputs,
    extract_everything
)


NANOPUB_SNK = Namespace("https://w3id.org/np/snakemake/")
SCHEMA = Namespace("https://schema.org/")
NPX = Namespace("http://purl.org/nanopub/x/")


class _SnakemakeStyleFormatter(logging.Formatter):
    _RESET = "\033[0m"
    _COLORS = {
        logging.INFO: "\033[32m",
        logging.WARNING: "\033[33m",
        logging.DEBUG: "\033[34m",
    }

    def format(self, record: logging.LogRecord) -> str:
        message = super().format(record)
        color = self._COLORS.get(record.levelno)
        if color is None:
            return message
        return f"{color}{message}{self._RESET}"


def _configure_logger() -> logging.Logger:
    logger = logging.getLogger("snakemake.report.nanopub")
    if logger.handlers:
        return logger

    handler = logging.StreamHandler()
    handler.setFormatter(_SnakemakeStyleFormatter("[nanopub] %(levelname)s: %(message)s"))
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)
    logger.propagate = False
    return logger



@dataclass
class ReportSettings(ReportSettingsBase):
    workflow_id: str = field(
        default=None,
        metadata={
            "help": "NanoPub ID of a workflow for which this report"
                    "this metadata NanoPub should be published.",
            "env_var": False,
            "required": True,
        },
    )
    output_path: Optional[Path] = field(
        default=None,
        metadata={
            "help": "Optional JSON output path for extracted workflow metadata.",
            "env_var": False,
            "required": False,
        },
    )
    main_server: bool = field(
        default=False,
        metadata={
            "help": "Publish to nanopub main server (defaults to test server).",
            "env_var": False,
            "required": False,
        },
    )
    dry_run: bool = field(
        default=False,
        metadata={
            "help": "Perform a dry run (do not publish the nanopub, just generate"
                    "and print the nanopub content).",
            "env_var": False,
            "required": False,
        },
    )


class Reporter(ReporterBase):
    _MAX_PUBLISH_QUADS = 300

    def __post_init__(self):
        self.generated_at = datetime.datetime.now(datetime.UTC).isoformat()
        self.logger = _configure_logger()
        self.dry_run = self.settings.dry_run

    def _jsonable(self, value: Any):
        if isinstance(value, dict):
            return {str(k): self._jsonable(v) for k, v in value.items()}
        if isinstance(value, (list, tuple, set)):
            return [self._jsonable(v) for v in value]
        if isinstance(value, Path):
            return str(value)
        if isinstance(value, (str, int, float, bool)) or value is None:
            return value
        return str(value)

    def make_term(self, value: Any):
        if value is None:
            return None
        if isinstance(value, bool):
            return Literal(value, datatype=XSD.boolean)
        if isinstance(value, int):
            return Literal(value, datatype=XSD.integer)
        if isinstance(value, float):
            return Literal(value, datatype=XSD.double)
        if isinstance(value, str):
            if value.startswith(("http://", "https://", "urn:")):
                return URIRef(value)
            return Literal(value)
        return Literal(json.dumps(self._jsonable(value), ensure_ascii=False), datatype=XSD.string)

    def safe_fragment(self, value: Any, prefix: str = "item") -> str:
        raw = str(value) if value is not None else ""
        raw = raw.strip()
        if not raw:
            return f"{prefix}-{uuid.uuid4()}"
        return quote(raw, safe="")

    def build_nanopub(self, payload: dict):
        profile = load_profile()
        np_conf = NanopubConf(
            use_test_server=not self.settings.main_server,
            profile=profile,
            add_pubinfo_generated_time=True,
            add_prov_generated_time=True,
            attribute_assertion_to_profile=True,
            attribute_publication_to_profile=True,
        )

        # Create the Nanopub first so we can use its sub-namespace for all
        # internal URIs.  This mirrors workflow_report_template.py: nodes
        # created under np._metadata.namespace live in the temp sub-namespace
        # and are automatically rewritten to the trusty-URI sub-namespace when
        # np.sign() is called.  Bare http://purl.org/nanopub/temp/ URIs that
        # are NOT derived from that namespace are NOT rewritten by sign() and
        # will therefore appear in the final nanopub as invalid temp URIs,
        # causing the main registry to reject the publication.
        np = Nanopub(conf=np_conf)
        sub = np._metadata.namespace
        np.pubinfo.add((np._metadata.np_uri, NPX.hasNanopubType, SCHEMA.Dataset))
        np.pubinfo.add((np._metadata.np_uri, DCTERMS.created, Literal(self.generated_at, datatype=XSD.dateTime)))

        profile_orcid = None
        for attr in ("orcid_id", "orcid", "orcidid"):
            value = getattr(profile, attr, None)
            if value:
                profile_orcid = value
                break
        if profile_orcid:
            if not str(profile_orcid).startswith(("http://", "https://")):
                profile_orcid = f"https://orcid.org/{profile_orcid}"
            profile_orcid_ref = URIRef(str(profile_orcid))
            np.pubinfo.add((np._metadata.np_uri, DCTERMS.creator, profile_orcid_ref))

        workflow_id_value = self.settings.workflow_id or "workflow"
        np.pubinfo.add((np._metadata.np_uri, RDFS.label, Literal(f"Snakemake workflow metadata: {workflow_id_value}")))

        subj = sub["dataset"]
        workflow_node = sub["workflowrun"]

        np.assertion.add((subj, RDF.type, SCHEMA.Dataset))
        np.assertion.add((workflow_node, RDF.type, NANOPUB_SNK.WorkflowRun))
        np.assertion.add((subj, NANOPUB_SNK.hasWorkflowRun, workflow_node))
        np.assertion.add(
            (
                subj,
                NANOPUB_SNK.generatedAt,
                Literal(self.generated_at, datatype=XSD.dateTime),
            )
        )

        workflow_id_term = self.make_term(self.settings.workflow_id)
        if workflow_id_term is not None:
            np.assertion.add((subj, NANOPUB_SNK.describesWorkflow, workflow_id_term))

        workflow = payload.get("workflow", {})
        for pred, key in (
            (NANOPUB_SNK.mainSnakefile, "main_snakefile"),
            (NANOPUB_SNK.description, "description"),
        ):
            term = self.make_term(workflow.get(key))
            if term is not None:
                np.assertion.add((workflow_node, pred, term))

        for item in workflow.get("included_snakefiles", []):
            term = self.make_term(item)
            if term is not None:
                np.assertion.add((workflow_node, NANOPUB_SNK.includedSnakefile, term))

        for item in workflow.get("configfiles", []):
            term = self.make_term(item)
            if term is not None:
                np.assertion.add((workflow_node, NANOPUB_SNK.configfile, term))

        for item in workflow.get("dag_sources", []):
            term = self.make_term(item)
            if term is not None:
                np.assertion.add((workflow_node, NANOPUB_SNK.dagSource, term))

        config_term = self.make_term(workflow.get("config"))
        if config_term is not None:
            np.assertion.add((workflow_node, NANOPUB_SNK.configJSON, config_term))

        metadata_term = self.make_term(workflow.get("metadata"))
        if metadata_term is not None:
            np.assertion.add((workflow_node, NANOPUB_SNK.workflowMetadataJSON, metadata_term))

        summary = payload.get("summary", {})
        summary_node = sub["workflowsummary"]
        np.assertion.add((summary_node, RDF.type, NANOPUB_SNK.WorkflowSummary))
        np.assertion.add((subj, NANOPUB_SNK.hasSummary, summary_node))
        for pred, key in (
            (NANOPUB_SNK.numberOfRules, "n_rules"),
            (NANOPUB_SNK.numberOfJobs, "n_jobs"),
            (NANOPUB_SNK.numberOfResults, "n_results"),
        ):
            term = self.make_term(summary.get(key))
            if term is not None:
                np.assertion.add((summary_node, pred, term))

        rule_outputs = {}
        for job in payload.get("jobs_full", []):
            rule_name = job.get("rule")
            if not rule_name:
                continue
            rule_outputs.setdefault(rule_name, set())
            for out in job.get("output", []):
                if out:
                    rule_outputs[rule_name].add(str(out))

        for rule in payload.get("rules_full", []):
            rule_name = rule.get("name", "rule")
            rule_node = sub[f"rule-{self.safe_fragment(rule_name, 'rule')}"]
            np.assertion.add((rule_node, RDF.type, NANOPUB_SNK.WorkflowRule))
            np.assertion.add((workflow_node, NANOPUB_SNK.hasRule, rule_node))

            name_term = self.make_term(rule_name)
            if name_term is not None:
                np.assertion.add((rule_node, NANOPUB_SNK.ruleName, name_term))

            software_labels = set()
            for key in ("wrapper", "script", "notebook", "conda_env", "container_img"):
                value = rule.get(key)
                if value:
                    software_labels.add(str(value))
            if rule.get("is_shell") and rule.get("shellcmd"):
                software_labels.add("shell")
            if not software_labels:
                software_labels.add(str(rule_name))

            for software in sorted(software_labels):
                np.assertion.add((rule_node, NANOPUB_SNK.hasSoftwarePackage, Literal(software)))

            aggregated_outputs = set(str(o) for o in rule.get("output", []) if o)
            aggregated_outputs.update(rule_outputs.get(rule_name, set()))
            for out in sorted(aggregated_outputs):
                np.assertion.add((rule_node, NANOPUB_SNK.hasOutput, Literal(out)))

            for idx, param in enumerate(rule.get("params", []), start=1):
                param_node = sub[f"param-{self.safe_fragment(rule_name, 'rule')}-{idx}"]
                np.assertion.add((param_node, RDF.type, NANOPUB_SNK.Parameterization))
                np.assertion.add((rule_node, NANOPUB_SNK.hasParameterization, param_node))
                np.assertion.add((param_node, NANOPUB_SNK.parameterIndex, Literal(idx, datatype=XSD.integer)))
                term = self.make_term(param)
                if term is not None:
                    np.assertion.add((param_node, NANOPUB_SNK.parameterValue, term))

            param_values = [self._jsonable(p) for p in rule.get("params", [])]
            if param_values:
                np.assertion.add(
                    (
                        rule_node,
                        NANOPUB_SNK.parametersJSON,
                        Literal(json.dumps(param_values, ensure_ascii=False), datatype=XSD.string),
                    )
                )

        return np

    def render(self):
        try:
            payload = extract_everything(self.jobs, self.rules, self.results, 
                                         self.metadata, self.dag, self.workflow_description, self.generated_at, self._jsonable, self.logger)

            if self.settings.output_path is not None:
                self.settings.output_path.parent.mkdir(parents=True, exist_ok=True)
                with open(self.settings.output_path, "w", encoding="utf-8") as out:
                    json.dump(payload, out, indent=2, ensure_ascii=False)

            np = self.build_nanopub(payload)
            self.logger.info("Nanopub quad count before publish: %d", len(np.rdf))
            try:
                _ = np.is_valid
                self.logger.info("Nanopub validation passed before publish.")
            except Exception as validation_error:
                raise WorkflowError("Generated nanopub is invalid before publish.", validation_error)

            # Registry endpoints can reject very large nanopubs with generic HTTP 400
            # and no structured response body. If the graph is large, retry with a
            # compact assertion model that keeps only summary-level information.
            if len(np.rdf) > self._MAX_PUBLISH_QUADS:
                self.logger.warning(
                    "Nanopub has %d quads (threshold %d). Building compact nanopub for publish retry.",
                    len(np.rdf),
                    self._MAX_PUBLISH_QUADS,
                )
                compact_payload = dict(payload)
                compact_payload["rules_full"] = []
                compact_payload["jobs_full"] = []
                compact_html = dict(compact_payload.get("html_reporter_derived", {}))
                compact_html["packages"] = {}
                compact_payload["html_reporter_derived"] = compact_html
                np = self.build_nanopub(compact_payload)
                self.logger.info("Compact nanopub quad count before publish: %d", len(np.rdf))
                try:
                    _ = np.is_valid
                    self.logger.info("Compact nanopub validation passed before publish.")
                except Exception as validation_error:
                    raise WorkflowError(
                        "Compact generated nanopub is invalid before publish.", validation_error
                    )

            # Main registry requires a signed trusty nanopub.
            np = bind_nanopub_prefixes(np)
            try:
                np.sign()
                np = bind_nanopub_prefixes(np)
                _ = np.is_valid
                self.logger.info("Signed nanopub validation passed before publish.")
            except Exception as sign_error:
                raise WorkflowError("Failed to sign or validate nanopub before publish.", sign_error)

            self.logger.debug("Generated nanopub object: %s", np)
            if self.dry_run:
                self.logger.info("Dry run: full nanopub content:\n%s", np.rdf.serialize(format="trig"))
                sys.exit(0)

            try:
                id = np.publish()
                self.logger.info(
                    f"Nanopub published successfully: {id}"
                )
            except Exception as e:
                self.logger.warning(
                    "Nanopub created (not published). Set --report-nanopub-init-publish to publish."
                    f"The error during publication was: {e}"
                )
                self.logger.warning("Publication exception type: %s", type(e).__name__)
                self.logger.warning("Publication exception args: %s", getattr(e, "args", ()))
                # Show the server’s JSON error payload (if any)
                if hasattr(e, "response") and e.response is not None:
                    self.logger.warning("Server response status: %s", e.response.status_code)
                    self.logger.warning("Server response body: %s", e.response.text)
                if getattr(e, "__cause__", None) is not None:
                    self.logger.warning("Publication exception cause: %r", e.__cause__)
                if getattr(e, "__context__", None) is not None:
                    self.logger.warning("Publication exception context: %r", e.__context__)

        except Exception as e:
            raise WorkflowError("Failed to generate nanopub metadata report.", e)
           

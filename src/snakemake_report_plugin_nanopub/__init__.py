from dataclasses import dataclass, field
import datetime
import html
import json
from pathlib import Path
import re
from typing import Any, Optional
import uuid
import sys
from urllib.parse import quote, urlparse

from nanopub import Nanopub, NanopubConf, load_profile
from rdflib import Literal, Namespace, RDF, URIRef
from rdflib.namespace import DCTERMS, RDFS
from rdflib.namespace import XSD

from snakemake.logging import logger as snakemake_logger
from snakemake_interface_common.exceptions import WorkflowError
from snakemake_interface_report_plugins.reporter import ReporterBase
from snakemake_interface_report_plugins.settings import ReportSettingsBase
from .validation import bind_nanopub_prefixes
from .extraction import extract_everything

NANOPUB_SNK = Namespace("https://w3id.org/np/snakemake/")
SCHEMA = Namespace("https://schema.org/")
NPX = Namespace("http://purl.org/nanopub/x/")


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
    # We set a publishing threshold to avoid attempting to publish nanopubs
    # that are too large for the server to handle.
    # Here, 'quat' means RDF quads, which are the internal representation used by the
    # nanopub library. The final published nanopub will be serialized to RDF triples,
    # but the library may use quads (subject, predicate, object, assertion_graph)
    _MAX_PUBLISH_QUADS = 300

    def __post_init__(self):
        self.generated_at = datetime.datetime.now(datetime.UTC).isoformat()
        self.dry_run = self.settings.dry_run
        self.logger = snakemake_logger

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
        return Literal(
            json.dumps(self._jsonable(value), ensure_ascii=False), datatype=XSD.string
        )

    def safe_fragment(self, value: Any, prefix: str = "item") -> str:
        raw = str(value) if value is not None else ""
        raw = raw.strip()
        if not raw:
            return f"{prefix}-{uuid.uuid4()}"
        return quote(raw, safe="")

    def plain_text(
        self,
        value: Any,
        drop_links: bool = False,
        strip_comment_lines: bool = False,
    ) -> Optional[str]:
        if value is None:
            return None

        text = str(value).strip()
        if (text.startswith('"""') and text.endswith('"""')) or (
            text.startswith("'''") and text.endswith("'''")
        ):
            text = text[3:-3]

        # Handle serialized/escaped multiline payloads (e.g. "\\n" from JSON-like sources)
        text = text.replace("\\r\\n", "\n").replace("\\n", "\n").replace("\\r", "\n")
        text = text.replace('\\"', '"').replace("\\'", "'")

        text = text.replace("\r\n", "\n").replace("\r", "\n")
        text = re.sub(r"(?is)<br\\s*/?>", "\n", text)
        text = re.sub(
            r"(?is)</?(?:div|p|blockquote|li|ul|ol|section)\\b[^>]*>", "\n", text
        )
        text = re.sub(r"(?is)<a\\b[^>]*>(.*?)</a>", r"\\1", text)
        text = re.sub(r"(?is)<[^>]+>", "", text)
        text = html.unescape(text)

        if strip_comment_lines:
            text = "\n".join(
                line for line in text.splitlines() if not line.lstrip().startswith("#")
            )

        text = "\n".join(line.rstrip() for line in text.splitlines())
        text = re.sub(r"\n{3,}", "\n\n", text)
        text = text.strip()
        if not text:
            return None

        if drop_links:
            parsed = urlparse(text)
            if parsed.scheme in {"http", "https", "urn"}:
                if parsed.fragment:
                    text = parsed.fragment
                else:
                    path_name = Path(parsed.path).name if parsed.path else ""
                    text = path_name or parsed.netloc or text

            text = re.sub(r"(?i)\\b(?:https?://|urn:)\\S+", "", text).strip()
            if not text:
                return None

        return text

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
        np.pubinfo.add(
            (
                np._metadata.np_uri,
                DCTERMS.created,
                Literal(self.generated_at, datatype=XSD.dateTime),
            )
        )

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
            np.pubinfo.add((np._metadata.np_uri, NPX.signedBy, profile_orcid_ref))

        workflow_id_value = (
            self.plain_text(self.settings.workflow_id, drop_links=True) or "workflow"
        )
        np.pubinfo.add(
            (
                np._metadata.np_uri,
                RDFS.label,
                Literal(f"Snakemake workflow metadata: {workflow_id_value}"),
            )
        )

        # Use a single dataset node — no separate workflowrun indirection.
        subj = sub["dataset"]
        workflow_node = subj

        # Put the most identifying triples first so they appear at the top of
        # the serialized assertion block.
        workflow_id_term = self.make_term(workflow_id_value)
        if workflow_id_term is not None:
            np.assertion.add((subj, NANOPUB_SNK.describesWorkflow, workflow_id_term))

        np.assertion.add(
            (
                subj,
                NANOPUB_SNK.generatedAt,
                Literal(self.generated_at, datatype=XSD.dateTime),
            )
        )
        np.assertion.add((subj, RDF.type, SCHEMA.Dataset))

        workflow = payload.get("workflow", {})
        description_term = self.make_term(workflow.get("description"))
        if description_term is not None:
            np.assertion.add((subj, NANOPUB_SNK.description, description_term))

        config_section_node = sub["workflow-configuration"]
        np.assertion.add(
            (workflow_node, NANOPUB_SNK.hasConfigurationSection, config_section_node)
        )
        np.assertion.add(
            (config_section_node, RDFS.label, Literal("from workflow configuration"))
        )

        config_file_contents = workflow.get("config_file_contents", [])
        for idx, config_entry in enumerate(config_file_contents, start=1):
            config_node = sub[f"config-{idx}"]
            np.assertion.add(
                (config_section_node, NANOPUB_SNK.hasConfigurationFile, config_node)
            )

            config_path = config_entry.get("path")
            config_identifier = None
            if config_path is not None:
                config_identifier = Path(str(config_path)).name or str(config_path)

            path_term = self.make_term(config_identifier)
            if path_term is not None:
                np.assertion.add((config_node, DCTERMS.identifier, path_term))

            cleaned_content = self.plain_text(
                config_entry.get("content"), strip_comment_lines=True
            )
            content_term = self.make_term(cleaned_content)
            if content_term is not None:
                np.assertion.add((config_node, SCHEMA.text, content_term))

        if not config_file_contents:
            cleaned_config = self.plain_text(
                workflow.get("config"), strip_comment_lines=True
            )
            config_term = self.make_term(cleaned_config)
            if config_term is not None:
                np.assertion.add((config_section_node, SCHEMA.text, config_term))

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
                np.assertion.add(
                    (rule_node, NANOPUB_SNK.hasSoftwarePackage, Literal(software))
                )

            if rule_name == "all":
                aggregated_inputs = set(str(i) for i in rule.get("input", []) if i)
                for rule_input in sorted(aggregated_inputs):
                    np.assertion.add(
                        (rule_node, NANOPUB_SNK.hasInput, Literal(rule_input))
                    )
            else:
                aggregated_outputs = set(str(o) for o in rule.get("output", []) if o)
                aggregated_outputs.update(rule_outputs.get(rule_name, set()))
                for out in sorted(aggregated_outputs):
                    np.assertion.add((rule_node, NANOPUB_SNK.hasOutput, Literal(out)))

            for idx, param in enumerate(rule.get("params", []), start=1):
                param_node = sub[f"param-{self.safe_fragment(rule_name, 'rule')}-{idx}"]
                np.assertion.add((param_node, RDF.type, NANOPUB_SNK.Parameterization))
                np.assertion.add(
                    (rule_node, NANOPUB_SNK.hasParameterization, param_node)
                )
                np.assertion.add(
                    (
                        param_node,
                        NANOPUB_SNK.parameterIndex,
                        Literal(idx, datatype=XSD.integer),
                    )
                )
                term = self.make_term(param)
                if term is not None:
                    np.assertion.add((param_node, NANOPUB_SNK.parameterValue, term))

            param_values = [self._jsonable(p) for p in rule.get("params", [])]
            if param_values:
                np.assertion.add(
                    (
                        rule_node,
                        NANOPUB_SNK.parametersJSON,
                        Literal(
                            json.dumps(param_values, ensure_ascii=False),
                            datatype=XSD.string,
                        ),
                    )
                )

        return np

    def render(self):
        try:
            payload = extract_everything(
                self.jobs,
                self.rules,
                self.results,
                self.metadata,
                self.dag,
                self.workflow_description,
                self.generated_at,
                self._jsonable,
                self.logger,
            )

            if self.settings.output_path is not None:
                self.settings.output_path.parent.mkdir(parents=True, exist_ok=True)
                with open(self.settings.output_path, "w", encoding="utf-8") as out:
                    json.dump(payload, out, indent=2, ensure_ascii=False)

            np = self.build_nanopub(payload)
            self.logger.info(
                f"Nanopub RDF quadruple count before publish: {len(np.rdf)}"
            )
            try:
                _ = np.is_valid
                self.logger.info("Nanopub validation passed before publish.")
            except Exception as validation_error:
                raise WorkflowError(
                    "Generated nanopub is invalid before publish.", validation_error
                )

            # Registry endpoints can reject very large nanopubs with generic HTTP 400
            # and no structured response body. If the graph is large, retry with a
            # compact assertion model that keeps only summary-level information.
            if len(np.rdf) > self._MAX_PUBLISH_QUADS:
                self.logger.warning(
                    f"Nanopub has {len(np.rdf)} RDF quadruples (threshold {self._MAX_PUBLISH_QUADS}). Building compact nanopub for publish retry."
                )
                compact_payload = dict(payload)
                compact_payload["rules_full"] = []
                compact_payload["jobs_full"] = []
                compact_html = dict(compact_payload.get("html_reporter_derived", {}))
                compact_html["packages"] = {}
                compact_payload["html_reporter_derived"] = compact_html
                np = self.build_nanopub(compact_payload)
                self.logger.info(
                    f"Compact nanopub RDF quadruple count before publish: {len(np.rdf)}"
                )
                try:
                    _ = np.is_valid
                    self.logger.info(
                        "Compact nanopub validation passed before publish."
                    )
                except Exception as validation_error:
                    raise WorkflowError(
                        "Compact generated nanopub is invalid before publish.",
                        validation_error,
                    )

            # Main registry requires a signed trusty nanopub.
            np = bind_nanopub_prefixes(np)
            try:
                np.sign()
                np = bind_nanopub_prefixes(np)
                _ = np.is_valid
                self.logger.info("Signed nanopub validation passed before publish.")
            except Exception as sign_error:
                raise WorkflowError(
                    "Failed to sign or validate nanopub before publish.", sign_error
                )

            self.logger.debug(f"Generated nanopub object: {np}")
            if self.dry_run:
                self.logger.info(
                    f"Dry run: full nanopub content:\n{np.rdf.serialize(format='trig')}"
                )
                sys.exit(0)

            try:
                id = np.publish()
                self.logger.info(f"Nanopub published successfully: {id}")
            except Exception as e:
                self.logger.warning(
                    "Nanopub created (not published)."
                    "Set --report-nanopub-main-server to publish."
                    f"The error during publication was: {e}"
                )
                self.logger.warning(f"Publication exception type: {type(e).__name__}")
                self.logger.warning(
                    f"Publication exception args: {getattr(e, 'args', ())}"
                )
                # Show the server’s JSON error payload (if any)
                if hasattr(e, "response") and e.response is not None:
                    self.logger.warning(
                        f"Server response status: {e.response.status_code}"
                    )
                    self.logger.warning(f"Server response body: {e.response.text}")
                if getattr(e, "__cause__", None) is not None:
                    self.logger.warning(f"Publication exception cause: {e.__cause__!r}")
                if getattr(e, "__context__", None) is not None:
                    self.logger.warning(
                        f"Publication exception context: {e.__context__!r}"
                    )

        except Exception as e:
            raise WorkflowError("Failed to generate nanopub metadata report.", e)

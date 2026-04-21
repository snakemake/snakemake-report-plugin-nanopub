import json
from types import SimpleNamespace

import pytest

from snakemake_report_plugin_nanopub import extraction


class DummyLogger:
    def __init__(self):
        self.warnings = []
        self.debugs = []

    def warning(self, message):
        self.warnings.append(str(message))

    def debug(self, message):
        self.debugs.append(str(message))


class DummyJob:
    def __init__(self, rule, starttime=None, endtime=None, output=None):
        self.rule = rule
        self.starttime = starttime
        self.endtime = endtime
        self.output = output or []
        self.conda_env_file = "env.yml"
        self.container_img_url = "docker://example/image:1.0"


class DummyRule:
    def __init__(self):
        self.name = "align"
        self.docstring = "Alignment rule"
        self.input = ["reads.fastq", lambda wildcards: "dynamic"]
        self.output = ["aligned.bam"]
        self.params = ["--very-sensitive"]
        self.log = ["align.log"]
        self.benchmark = "bench.txt"
        self.resources = {"_cores": 8, "mem_mb": 16000}
        self.conda_env = "envs/align.yaml"
        self.container_img = "docker://img"
        self.env_modules = ["bwa/0.7"]
        self.wrapper = "0.99.0/bio/bwa/mem"
        self.script = None
        self.notebook = None
        self.shellcmd = "bwa mem ..."
        self.is_run = False
        self.is_shell = True
        self.is_script = False
        self.is_wrapper = True
        self.is_notebook = False


@pytest.fixture
def jsonable():
    return lambda value: value


def test_read_workflow_config_files_reads_and_reports_missing(tmp_path):
    logger = DummyLogger()
    existing = tmp_path / "config.yaml"
    existing.write_text("answer: 42\n", encoding="utf-8")
    missing = tmp_path / "missing.yaml"

    entries = extraction.read_workflow_config_files([existing, missing], logger)

    assert entries[0]["path"] == str(existing)
    assert entries[0]["content"] == "answer: 42\n"
    assert entries[1]["path"] == str(missing)
    assert entries[1]["content"] is None
    assert any(
        "Could not read workflow config file" in warning for warning in logger.warnings
    )


def test_extract_jobs_computes_runtime_and_serializes(jsonable):
    jobs = [
        DummyJob("rule_a", starttime=1.5, endtime=4.0, output=["a.txt"]),
        DummyJob("rule_b", starttime=None, endtime=2.0, output=["b.txt"]),
    ]

    result = extraction.extract_jobs(jobs, jsonable)

    assert result[0]["rule"] == "rule_a"
    assert result[0]["runtime"] == pytest.approx(2.5)
    assert result[0]["output"] == ["a.txt"]
    assert result[1]["rule"] == "rule_b"
    assert result[1]["runtime"] is None


def test_extract_rules_full_extracts_wrapper_version_and_threads(jsonable):
    rules = [DummyRule()]

    result = extraction.extract_rules_full(rules, jsonable)

    assert len(result) == 1
    rule = result[0]
    assert rule["name"] == "align"
    assert rule["wrapper"] == "0.99.0/bio/bwa/mem"
    assert rule["wrapper_version"] == "0.99.0"
    assert rule["threads"] == 8
    assert rule["is_wrapper"] is True


def test_extract_workflow_inputs_collects_declared_and_dag_inputs():
    dag = SimpleNamespace(
        jobs=[SimpleNamespace(input=["sample1.fastq", "sample2.fastq"])],
        workflow=SimpleNamespace(
            rules=[
                SimpleNamespace(input=["sample1.fastq", lambda wildcards: "dynamic"]),
                SimpleNamespace(input=["sample2.fastq"]),
            ]
        ),
    )

    result = extraction.extract_workflow_inputs(dag)

    assert result["declared_rule_inputs"] == ["sample1.fastq", "sample2.fastq"]
    assert result["dag_job_inputs"] == ["sample1.fastq", "sample2.fastq"]


def test_extract_everything_builds_full_payload(monkeypatch, tmp_path, jsonable):
    logger = DummyLogger()
    cfg = tmp_path / "workflow.yaml"
    cfg.write_text("threads: 4\n", encoding="utf-8")

    jobs = [DummyJob("align", starttime=1.0, endtime=3.0, output=["aligned.bam"])]
    rules = [DummyRule()]

    dag = SimpleNamespace(
        jobs=[SimpleNamespace(input=["reads.fastq"])],
        workflow=SimpleNamespace(
            configfiles=[cfg],
            config={"threads": 4},
            rules=rules,
        ),
    )

    monkeypatch.setattr(
        extraction,
        "rulegraph_spec",
        lambda dag_arg: (
            {"nodes": ["n1"], "links": ["l1"], "links_direct": []},
            None,
            None,
        ),
    )

    fake_html = SimpleNamespace(
        render_categories=lambda results: json.dumps([{"name": "cat"}]),
        render_results=lambda results, mode_embedded=True: json.dumps([{"id": "res"}]),
        render_rules=lambda rules_arg: json.dumps([{"name": "align"}]),
        get_packages=lambda: SimpleNamespace(
            get_json=lambda: json.dumps({"pkg": "1.0"})
        ),
        render_metadata=lambda metadata: json.dumps({"meta": "ok"}),
    )
    monkeypatch.setattr(extraction, "html_data", fake_html)

    payload = extraction.extract_everything(
        jobs=jobs,
        rules=rules,
        results=[{"id": "res"}],
        metadata={"meta": "ok"},
        dag=dag,
        workflow_description="A workflow",
        generated_at="2026-04-16T00:00:00",
        jsonable=jsonable,
        logger=logger,
    )

    assert payload["generated_at"] == "2026-04-16T00:00:00"
    assert payload["workflow"]["description"] == "A workflow"
    assert payload["workflow"]["configfiles"] == [str(cfg)]
    assert payload["workflow"]["config_file_contents"][0]["content"] == "threads: 4\n"
    assert payload["rules_full"][0]["name"] == "align"
    assert payload["jobs_full"][0]["runtime"] == pytest.approx(2.0)
    assert payload["inputs"]["dag_job_inputs"] == ["reads.fastq"]
    assert payload["html_reporter_derived"]["rulegraph"]["nodes"] == ["n1"]
    assert payload["html_reporter_derived"]["packages"] == {"pkg": "1.0"}


def test_extract_everything_handles_optional_html_derived_failure(
    monkeypatch, tmp_path, jsonable
):
    logger = DummyLogger()
    cfg = tmp_path / "workflow.yaml"
    cfg.write_text("threads: 2\n", encoding="utf-8")

    rules = [DummyRule()]
    jobs = [DummyJob("align", starttime=1.0, endtime=2.0, output=["aligned.bam"])]

    dag = SimpleNamespace(
        jobs=[SimpleNamespace(input=["reads.fastq"])],
        workflow=SimpleNamespace(configfiles=[cfg], config={"threads": 2}, rules=rules),
    )

    monkeypatch.setattr(
        extraction,
        "rulegraph_spec",
        lambda dag_arg: (_ for _ in ()).throw(RuntimeError("boom")),
    )

    payload = extraction.extract_everything(
        jobs=jobs,
        rules=rules,
        results=[],
        metadata={},
        dag=dag,
        workflow_description="desc",
        generated_at="2026-04-16T00:00:00",
        jsonable=jsonable,
        logger=logger,
    )

    assert payload["html_reporter_derived"] == {}
    assert any(
        "Skipping optional html_reporter_derived extraction" in warning
        for warning in logger.warnings
    )
    assert any("traceback" in debug for debug in logger.debugs)


def _make_minimal_extract_everything_kwargs(monkeypatch, tmp_path, jsonable):
    """Return minimal kwargs for extract_everything that won't error on imports."""
    logger = DummyLogger()
    rules = []
    dag = SimpleNamespace(
        jobs=[],
        workflow=SimpleNamespace(
            configfiles=[],
            config={},
            rules=rules,
        ),
    )

    monkeypatch.setattr(
        extraction,
        "rulegraph_spec",
        lambda dag_arg: ({"nodes": [], "links": [], "links_direct": []}, None, None),
    )

    fake_html = SimpleNamespace(
        render_categories=lambda results: "[]",
        render_results=lambda results, mode_embedded=True: "[]",
        render_rules=lambda rules_arg: "[]",
        get_packages=lambda: SimpleNamespace(get_json=lambda: "{}"),
        render_metadata=lambda metadata: "{}",
    )
    monkeypatch.setattr(extraction, "html_data", fake_html)

    return {
        "rules": rules,
        "results": [],
        "metadata": {},
        "dag": dag,
        "workflow_description": "desc",
        "generated_at": "2026-01-01T00:00:00",
        "jsonable": jsonable,
        "logger": logger,
    }


def test_ts_iso_none_starttime(monkeypatch, tmp_path, jsonable):
    """ts_iso(None) should return None, covering the early-return branch."""
    kwargs = _make_minimal_extract_everything_kwargs(monkeypatch, tmp_path, jsonable)
    # A job with starttime=None triggers ts_iso(None) → return None
    job_with_none_start = DummyJob("rule_x", starttime=None, endtime=2.0)
    payload = extraction.extract_everything(jobs=[job_with_none_start], **kwargs)

    timeline = payload["html_reporter_derived"].get("timeline", [])
    assert any(entry["starttime"] is None for entry in timeline)


def test_ts_iso_os_error_branch(monkeypatch, tmp_path, jsonable):
    """When datetime.fromtimestamp raises OSError, ts_iso should return None."""
    from unittest.mock import patch

    kwargs = _make_minimal_extract_everything_kwargs(monkeypatch, tmp_path, jsonable)
    job = DummyJob("rule_y", starttime=1.0, endtime=2.0)

    with patch("snakemake_report_plugin_nanopub.extraction.datetime") as mock_dt:
        mock_dt.datetime.fromtimestamp.side_effect = OSError("bad timestamp")
        payload = extraction.extract_everything(jobs=[job], **kwargs)

    timeline = payload["html_reporter_derived"].get("timeline", [])
    # All timestamps should be None because fromtimestamp always raised OSError.
    assert all(entry["starttime"] is None for entry in timeline)
    assert all(entry["endtime"] is None for entry in timeline)

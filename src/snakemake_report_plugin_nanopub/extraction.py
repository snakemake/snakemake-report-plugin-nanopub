import datetime
import json


from snakemake.report.rulegraph_spec import rulegraph_spec as rulegraph_spec  # noqa: PLC0415
from snakemake.report.html_reporter import data as html_data  # noqa: PLC0415


def extract_jobs(jobs, jsonable):
    joblist = []
    for rec in jobs:
        start = getattr(rec, "starttime", None)
        end = getattr(rec, "endtime", None)
        runtime = None
        if isinstance(start, (int, float)) and isinstance(end, (int, float)):
            runtime = end - start

        joblist.append(
            {
                "rule": getattr(rec, "rule", None),
                "starttime": start,
                "endtime": end,
                "runtime": runtime,
                "output": jsonable(getattr(rec, "output", [])),
                "conda_env_file": jsonable(getattr(rec, "conda_env_file", None)),
                "container_img_url": jsonable(getattr(rec, "container_img_url", None)),
            }
        )
    return joblist


def extract_rules_full(rules, jsonable):
    workflow_rules = []
    for rule in rules:
        wrapper = getattr(rule, "wrapper", None)
        wrapper_version = None
        if wrapper and isinstance(wrapper, str) and "/" in wrapper:
            wrapper_version = wrapper.split("/", 1)[0]

        workflow_rules.append(
            {
                "name": rule.name,
                "docstring": rule.docstring,
                "input": jsonable(list(rule.input)),
                "output": jsonable(list(rule.output)),
                "params": jsonable(list(rule.params)),
                "log": jsonable(list(rule.log)),
                "benchmark": jsonable(rule.benchmark),
                "threads": jsonable(
                    rule.resources.get("_cores") if rule.resources else None
                ),
                "resources": jsonable(rule.resources),
                "conda_env": jsonable(rule.conda_env),
                "container_img": jsonable(rule.container_img),
                "env_modules": jsonable(rule.env_modules),
                "wrapper": jsonable(wrapper),
                "wrapper_version": wrapper_version,
                "script": jsonable(rule.script),
                "notebook": jsonable(rule.notebook),
                "shellcmd": jsonable(rule.shellcmd),
                "is_run": rule.is_run,
                "is_shell": rule.is_shell,
                "is_script": rule.is_script,
                "is_wrapper": rule.is_wrapper,
                "is_notebook": rule.is_notebook,
            }
        )
    return workflow_rules


def extract_workflow_inputs(dag):
    concrete_inputs = set()
    for job in dag.jobs:
        for f in job.input:
            concrete_inputs.add(str(f))

    declared_inputs = sorted(
        {str(f) for rule in dag.workflow.rules for f in rule.input if not callable(f)}
    )

    return {
        "declared_rule_inputs": declared_inputs,
        "dag_job_inputs": sorted(concrete_inputs),
    }


def extract_everything(
    jobs,
    rules,
    results,
    metadata,
    dag,
    workflow_description,
    generated_at,
    jsonable,
    logger,
):
    runtimes_raw = [
        {"rule": rec.rule, "runtime": rec.endtime - rec.starttime}
        for rec in jobs
        if getattr(rec, "endtime", None) is not None
        and getattr(rec, "starttime", None) is not None
    ]

    def ts_iso(ts):
        if ts is None:
            return None
        try:
            return datetime.datetime.fromtimestamp(ts).isoformat()
        except OSError:
            return None

    timeline_raw = [
        {
            "rule": rec.rule,
            "starttime": ts_iso(getattr(rec, "starttime", None)),
            "endtime": ts_iso(getattr(rec, "endtime", None)),
        }
        for rec in jobs
    ]

    html_reporter_derived = {}
    try:
        rulegraph, _, _ = rulegraph_spec(dag)
        html_reporter_derived = {
            "categories": json.loads(html_data.render_categories(results)),
            "results": json.loads(
                html_data.render_results(results, mode_embedded=True)
            ),
            "rulegraph": {
                "nodes": rulegraph["nodes"],
                "links": rulegraph["links"],
                "links_direct": rulegraph["links_direct"],
            },
            "rules": json.loads(html_data.render_rules(rules)),
            "runtimes": runtimes_raw,
            "timeline": timeline_raw,
            "packages": json.loads(html_data.get_packages().get_json()),
            "metadata": json.loads(html_data.render_metadata(metadata)),
        }
    except Exception as e:
        logger.warning(
            "Skipping optional html_reporter_derived extraction due to error: %s", e
        )
        logger.debug("html_reporter_derived extraction traceback", exc_info=True)

    report_payload = {
        "generated_at": generated_at,
        "workflow": {
            "main_snakefile": str(dag.workflow.main_snakefile),
            "included_snakefiles": sorted(
                [f.get_path_or_uri() for f in dag.workflow.included]
            ),
            "configfiles": [str(f) for f in dag.workflow.configfiles],
            "dag_sources": sorted(dag.get_sources()),
            "description": workflow_description,
            "metadata": jsonable(metadata),
            "config": jsonable(dag.workflow.config),
        },
        "summary": {
            "n_rules": len(list(dag.workflow.rules)),
            "n_jobs": len(list(dag.jobs)),
            "n_results": sum(
                len(catresults)
                for subcats in results.values()
                for catresults in subcats.values()
            ),
        },
        "html_reporter_derived": html_reporter_derived,
        "rules_full": extract_rules_full(dag.workflow.rules, jsonable),
        "jobs_full": extract_jobs(jobs, jsonable),
        "inputs": extract_workflow_inputs(dag),
    }

    return report_payload

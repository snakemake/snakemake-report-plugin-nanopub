import json
from pathlib import Path
import yaml


from snakemake.report.rulegraph_spec import (
    rulegraph_spec as rulegraph_spec,
)  # noqa: PLC0415
from snakemake.report.html_reporter import data as html_data  # noqa: PLC0415


def _unique_paths(paths):
    seen = set()
    result = []
    for path in paths:
        normalized = Path(path)
        key = str(normalized)
        if key in seen:
            continue
        seen.add(key)
        result.append(normalized)
    return result


def _coerce_path(value):
    if value is None or callable(value):
        return None
    if isinstance(value, Path):
        return value
    if isinstance(value, str):
        value = value.strip()
        if not value:
            return None
        return Path(value)
    return None


def _conda_env_search_roots(configfiles):
    roots = [
        Path.cwd(),
        Path.cwd() / "workflow",
        Path.cwd() / "rules",
        Path.cwd() / "workflow" / "rules",
    ]

    for configfile in configfiles or []:
        parent = Path(str(configfile)).parent
        roots.extend(
            [
                parent,
                parent / "workflow",
                parent / "rules",
                parent / "workflow" / "rules",
            ]
        )

    return _unique_paths(roots)


def _rule_local_search_roots(rule):
    roots = []

    for attr in ("basedir", "base_dir", "rulebasedir"):
        value = getattr(rule, attr, None)
        path = _coerce_path(value)
        if path is not None:
            roots.extend([path, path / "rules", path / "workflow" / "rules"])

    for attr in ("snakefile", "rulefile", "sourcefile"):
        value = getattr(rule, attr, None)
        path = _coerce_path(value)
        if path is not None:
            parent = path.parent
            roots.extend([parent, parent / "rules", parent / "workflow" / "rules"])

    workflow_obj = getattr(rule, "workflow", None)
    if workflow_obj is not None:
        for attr in ("basedir", "workdir"):
            value = getattr(workflow_obj, attr, None)
            path = _coerce_path(value)
            if path is not None:
                roots.extend([path, path / "rules", path / "workflow" / "rules"])

    return _unique_paths(roots)


def _resolve_conda_env_path(conda_env, search_roots):
    if not conda_env:
        return None

    conda_env_path = _coerce_path(conda_env)
    if conda_env_path is None:
        return None
    candidates = []
    if conda_env_path.is_absolute():
        candidates.append(conda_env_path)
    else:
        for root in search_roots or [Path.cwd()]:
            root_path = _coerce_path(root)
            if root_path is not None:
                candidates.append(root_path / conda_env_path)

    for candidate in _unique_paths(candidates):
        try:
            if candidate.exists() and candidate.is_file():
                return candidate
        except OSError:
            continue

    return None


def _parse_conda_dependencies(conda_env_path):
    if conda_env_path is None:
        return []

    parsed = yaml.safe_load(Path(conda_env_path).read_text(encoding="utf-8"))
    if not isinstance(parsed, dict):
        return []

    dependencies = parsed.get("dependencies", [])
    if not isinstance(dependencies, list):
        return []

    # Keep only scalar dependency specifiers. Nested sections like
    # "- pip:" are intentionally ignored for now.
    return [str(dep) for dep in dependencies if isinstance(dep, (str, int, float))]


def read_workflow_config_files(configfiles, logger):
    config_entries = []
    for configfile in configfiles:
        path = Path(str(configfile))
        entry = {"path": str(path)}
        try:
            entry["content"] = path.read_text(encoding="utf-8")
        except (OSError, UnicodeError, yaml.YAMLError) as e:
            logger.warning(f"Could not read workflow config file {path}: {e}")
            entry["content"] = None
        config_entries.append(entry)
    return config_entries


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


def extract_rules_full(rules, jsonable, conda_env_search_roots=None, logger=None):
    workflow_rules = []
    for rule in rules:
        wrapper = getattr(rule, "wrapper", None)
        is_wrapper = bool(getattr(rule, "is_wrapper", False) or wrapper)
        wrapper_version = None
        if wrapper and isinstance(wrapper, str) and "/" in wrapper:
            wrapper_version = wrapper.split("/", 1)[0]

        conda_env = jsonable(rule.conda_env)
        conda_dependencies = []
        if not is_wrapper:
            per_rule_roots = _unique_paths(
                list(conda_env_search_roots or []) + _rule_local_search_roots(rule)
            )
            conda_env_path = _resolve_conda_env_path(conda_env, per_rule_roots)
            if conda_env_path is not None:
                try:
                    conda_dependencies = _parse_conda_dependencies(conda_env_path)
                except OSError as e:
                    if logger is not None:
                        logger.warning(
                            f"Could not read conda environment file {conda_env_path}: {e}"
                        )
            elif conda_env and logger is not None:
                logger.warning(
                    f"Could not resolve conda environment path '{conda_env}' for rule '{rule.name}'."
                )

        workflow_rules.append(
            {
                # Legacy rule metadata kept as reference only.
                # Uncomment selectively if broader rule metadata is needed again.
                # "docstring": rule.docstring,
                # "params": jsonable(list(rule.params)),
                # "threads": jsonable(
                #     rule.resources.get("_cores") if rule.resources else None
                # ),
                # "resources": jsonable(rule.resources),
                # "container_img": jsonable(rule.container_img),
                # "env_modules": jsonable(rule.env_modules),
                # "script": jsonable(rule.script),
                # "notebook": jsonable(rule.notebook),
                # "shellcmd": jsonable(rule.shellcmd),
                # "is_run": rule.is_run,
                # "is_shell": rule.is_shell,
                # "is_script": rule.is_script,
                # "is_wrapper": rule.is_wrapper,
                # "is_notebook": rule.is_notebook,
                "name": rule.name,
                "input": jsonable([item for item in rule.input if not callable(item)]),
                "output": jsonable(
                    [item for item in rule.output if not callable(item)]
                ),
                "wrapper": jsonable(wrapper),
                "conda_env": conda_env,
                "conda_dependencies": conda_dependencies,
                "wrapper_version": wrapper_version,
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

    # def ts_iso(ts):
    #     if ts is None:
    #         return None
    #     try:
    #         return datetime.datetime.fromtimestamp(ts).isoformat()
    #     except OSError:
    #         return None
    #
    # timeline_raw = [
    #     {
    #         "rule": rec.rule,
    #         "starttime": ts_iso(getattr(rec, "starttime", None)),
    #         "endtime": ts_iso(getattr(rec, "endtime", None)),
    #     }
    #     for rec in jobs
    # ]

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
            # "timeline": timeline_raw,
            "packages": json.loads(html_data.get_packages().get_json()),
            "metadata": json.loads(html_data.render_metadata(metadata)),
        }
    except Exception as e:
        logger.warning(
            f"Skipping optional html_reporter_derived extraction due to error: {e}"
        )
        logger.debug(f"html_reporter_derived extraction traceback: {e!r}")

    report_payload = {
        "generated_at": generated_at,
        "workflow": {
            "configfiles": [str(f) for f in dag.workflow.configfiles],
            "config_file_contents": read_workflow_config_files(
                dag.workflow.configfiles, logger
            ),
            "description": workflow_description,
            "config": jsonable(dag.workflow.config),
        },
        "html_reporter_derived": html_reporter_derived,
        "rules_full": extract_rules_full(
            dag.workflow.rules,
            jsonable,
            conda_env_search_roots=_conda_env_search_roots(dag.workflow.configfiles),
            logger=logger,
        ),
        "jobs_full": extract_jobs(jobs, jsonable),
        "inputs": extract_workflow_inputs(dag),
    }

    return report_payload

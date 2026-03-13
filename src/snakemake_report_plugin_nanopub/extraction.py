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
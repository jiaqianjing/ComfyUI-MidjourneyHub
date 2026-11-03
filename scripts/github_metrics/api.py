"""GitHub read adapter.

CALLING SPEC: collect(repo, now) -> JSON-compatible snapshot.
Side effects: read GitHub through authenticated gh CLI; raises on API failure.
Never reads, prints, or stores credentials; requires traffic read permission.
"""

import json
import os
import subprocess


def get(path, star_dates=False):
    result = subprocess.run(
        (["gh", "api", path, "--paginate", "--slurp", "-H",
          "Accept: application/vnd.github.star+json"] if star_dates else ["gh", "api", path]), capture_output=True, text=True, timeout=90
    )
    if result.returncode:
        raise RuntimeError("GitHub API failed for " + path + ": " + result.stderr)
    return json.loads(result.stdout)


def collect(repo, now):
    base = "repos/" + repo
    metadata = get(base)
    return {
        "schema_version": 1,
        "repository": repo,
        "collected_at": now.isoformat(),
        "star_dates": [item["starred_at"] for page in get(
            base + "/stargazers?per_page=100", star_dates=True) for item in page],
        "counts": {
            "stars": metadata["stargazers_count"],
            "forks": metadata["forks_count"],
            "subscribers": metadata["subscribers_count"],
        },
        "traffic": ({name: get(base + "/traffic/" + name) for name in
                    ("views", "clones", "popular/referrers", "popular/paths")}
                    if os.environ.get("METRICS_TRAFFIC", "true") == "true" else {}),
    }

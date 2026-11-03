"""Snapshot file I/O.

CALLING SPEC: save_json(path, data) -> None; read_snapshots(root) -> list[dict].
Side effects: atomic local JSON writes / reads. No network access.
"""

import json
import os
import tempfile
from pathlib import Path


def save_json(path, data):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = None
    try:
        with tempfile.NamedTemporaryFile(mode="w", encoding="utf-8",
                                         dir=path.parent, delete=False) as stream:
            temporary = stream.name
            json.dump(data, stream, ensure_ascii=False, indent=2)
            stream.write("\n")
        os.replace(temporary, path)
    finally:
        if temporary and os.path.exists(temporary):
            os.unlink(temporary)


def read_snapshots(root):
    return [json.loads(path.read_text(encoding="utf-8"))
            for path in sorted(Path(root).glob("snapshots/*.json"))]

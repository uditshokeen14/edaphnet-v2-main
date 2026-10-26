"""Run records (charter §7): every run writes config, provenance, metrics, predictions."""
import datetime as dt
import hashlib
import json
import platform
import subprocess
import sys
from pathlib import Path


def _git(args, cwd):
    try:
        return subprocess.run(["git", *args], cwd=cwd, capture_output=True, text=True,
                              check=True).stdout.strip()
    except Exception:
        return None


def provenance(repo_root):
    sha = _git(["rev-parse", "HEAD"], repo_root)
    dirty = _git(["status", "--porcelain", "--", "src", "scripts", "configs"], repo_root)
    import numpy, scipy, sklearn, pandas, lightgbm  # noqa: E401
    return {
        "git_commit": sha or "no-commit",
        "git_dirty": bool(dirty) if dirty is not None else True,
        "status": "exploratory" if (sha is None or dirty) else "clean",
        "python": sys.version.split()[0],
        "platform": platform.platform(),
        "packages": {m.__name__: m.__version__ for m in (numpy, scipy, sklearn, pandas, lightgbm)},
        "started": dt.datetime.now().isoformat(timespec="seconds"),
    }


def new_run_dir(root, name, repo_root):
    sha = (_git(["rev-parse", "--short", "HEAD"], repo_root) or "nocommit")
    stamp = dt.datetime.now().strftime("%Y%m%d-%H%M%S")
    d = Path(root) / f"{stamp}_{name}_{sha}"
    d.mkdir(parents=True, exist_ok=False)
    return d


def write_json(path, obj):
    Path(path).write_text(json.dumps(obj, indent=2, default=_default))


def config_hash(cfg):
    return hashlib.sha256(json.dumps(cfg, sort_keys=True, default=str).encode()).hexdigest()[:12]


def _default(o):
    try:
        import numpy as np
        if isinstance(o, np.generic):
            return o.item()
        if isinstance(o, np.ndarray):
            return o.tolist()
    except ImportError:
        pass
    return str(o)

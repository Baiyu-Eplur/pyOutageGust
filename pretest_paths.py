"""Explicit paths for legacy analyses. Execution settings live in main.py."""
from __future__ import annotations

import json
import os
from pathlib import Path
from functools import lru_cache

PROJECT_ROOT = Path(__file__).resolve().parent
PRETEST_ROOT = PROJECT_ROOT / "results" / "pretest"
OLD_ROOT = Path("D:/Pyprogramme/STST2603")


def project_path(relative=""):
    return PROJECT_ROOT / relative


def result_path(relative=""):
    """Writable result location, allocated by the dispatcher for this step."""
    root = os.environ.get("PRETEST_OUTPUT_ROOT")
    if not root:
        raise RuntimeError("请在 main.py 设置开关并运行 python main.py；旧脚本需要运行上下文。")
    path = (Path(root) / relative).resolve()
    if not path.is_relative_to(Path(root).resolve()):
        raise ValueError(f"Result path escapes this run: {relative}")
    # Several legacy scripts wrote directly to a filename and assumed its
    # historical parent existed. A new timestamp directory starts empty.
    path.parent.mkdir(parents=True, exist_ok=True)
    return path


def data_path(relative=""):
    """V2 derived data are outputs; read_input finds existing source snapshots."""
    path = result_path("pipeline_v2_data") / relative
    (path.parent if path.suffix else path).mkdir(parents=True, exist_ok=True)
    return path


def external_path(relative=""):
    """Prefer migrated local inputs, with explicit read-only legacy fallback."""
    rel = str(relative).replace("\\", "/").strip("/")
    if not rel:
        # A root is only a prefix; resolve the full filename at its read site.
        return OLD_ROOT
    aliases = {
        "rebuild_v3_full_stage/outputs/ukpn_full_stage_dataset_v3.csv": "ukpn_full_stage_dataset_v3.csv",
        "data/Local_Authority_Districts_December_2021_UK_BGC_2022": "gis/LAD_DEC_2021_UK_BGC",
        "data/dno_license_areas_20200506": "gis/DNO_License_Areas_20200506",
    }
    candidates = []
    for old, local in aliases.items():
        if rel == old or rel.startswith(old + "/"):
            candidates.append(PROJECT_ROOT / "data/external" / (local + rel[len(old):]))
    candidates.append(PROJECT_ROOT / "data/external" / rel.removeprefix("data/new/").removeprefix("data/"))
    candidates.append(PROJECT_ROOT / "data/external" / rel)
    # Existing residual dependencies only: do not search unrelated locations.
    candidates.append(OLD_ROOT / rel)
    for candidate in candidates:
        if candidate.exists():
            return candidate
    return candidates[0]


@lru_cache(maxsize=1)
def _index():
    path = PRETEST_ROOT / "latest.json"
    return json.loads(path.read_text(encoding="utf-8")) if path.exists() else {}


def input_files(directory, pattern):
    """Union of cached files from this step, successful runs and raw snapshots."""
    directory = Path(directory)
    files = {p.name: p for p in Path(read_input(directory)).glob(pattern)}
    output = os.environ.get("PRETEST_OUTPUT_ROOT")
    if output and directory.is_relative_to(Path(output)):
        prefix = directory.relative_to(output).as_posix() + "/"
        for key, item in _index().items():
            if key.startswith(prefix) and "/" not in key[len(prefix):] and Path(key).match(pattern):
                files[Path(key).name] = PRETEST_ROOT / item["path"]
    files.update({p.name: p for p in directory.glob(pattern)})
    return list(files.values())


def _record_input(path):
    log = os.environ.get("PRETEST_INPUT_LOG")
    if log and path.is_file():
        stat = path.stat()
        record = {"path": str(path.resolve()), "bytes": stat.st_size,
                  "mtime_ns": stat.st_mtime_ns,
                  "legacy_external": path.resolve().is_relative_to(OLD_ROOT.resolve())}
        with open(log, "a", encoding="utf-8") as stream:
            stream.write(json.dumps(record, ensure_ascii=False) + "\n")
    return path


def read_input(value):
    """Current step -> successful indexed outputs -> archived baseline -> raw input.

    Only explicit read call sites use this function. Write paths never fall back
    to an earlier run, to data/external, or to the old project.
    """
    if not isinstance(value, (str, os.PathLike)):
        return value  # pandas also accepts already-open streams / ExcelFile.
    if isinstance(value, str) and "://" in value:
        return value
    path = Path(value)
    # Resolve legacy roots embedded in old JSON manifests without editing those
    # frozen manifests. Resolve a complete input filename before selecting a copy.
    if path.is_absolute() and path.is_relative_to(OLD_ROOT):
        rel = path.relative_to(OLD_ROOT).as_posix()
        path = PROJECT_ROOT / rel.removeprefix("claude_branch/") if rel.startswith("claude_branch/") else external_path(rel)
    output = os.environ.get("PRETEST_OUTPUT_ROOT")
    key = None
    if output and path.is_absolute() and path.is_relative_to(Path(output)):
        key = path.relative_to(output).as_posix()
    elif path.is_absolute() and path.is_relative_to(PROJECT_ROOT / "results") and not path.is_relative_to(PRETEST_ROOT):
        key = path.relative_to(PROJECT_ROOT / "results").as_posix()
    if path.is_file():
        return _record_input(path)
    if key:
        indexed = _index().get(key)
        if indexed:
            candidate = PRETEST_ROOT / indexed["path"]
            if candidate.is_file():
                return _record_input(candidate)
        if key.startswith("pipeline_v2_data/"):
            return _record_input(external_path("data/" + key.removeprefix("pipeline_v2_data/")))
        if key.startswith("review_package/data/"):
            candidate = PROJECT_ROOT / key
            if candidate.is_file():
                return _record_input(candidate)
        raise FileNotFoundError(f"缺少前置结果 {key}。请在 main.py 开启对应生成步骤，或检查 results/pretest/latest.json。")
    if path.is_dir():
        return path
    return _record_input(path)

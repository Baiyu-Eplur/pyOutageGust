"""One-time archive of pre-entry-point results, with per-file byte checks."""
from datetime import datetime
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from pretestmain import sha256, write_json
from pretest_paths import PRETEST_ROOT


def archive():
    report = ROOT / "docs/migration_history/pretest_archive_20260909.json"
    if report.exists():
        raise RuntimeError("Archive already completed; do not rerun")
    stamp = datetime.now().astimezone().strftime("%Y%m%d%H%M%S")
    destination = PRETEST_ROOT / "archive" / stamp
    destination.mkdir(parents=True, exist_ok=False)
    sources = [(p, Path("results") / p.name, p.name)
               for p in sorted((ROOT / "results").iterdir()) if p.name != "pretest"]
    for folder, target, key in [("review_package/results", "review_package/results", "review_package/regression"),
                                ("data/generated", "data/generated", "generated_data")]:
        parent = ROOT / folder
        if parent.exists():
            sources.extend((p, Path(target) / p.name, f"{key}/{p.name}") for p in sorted(parent.iterdir()))
    index_path = PRETEST_ROOT / "latest.json"
    index = json.loads(index_path.read_text(encoding="utf-8")) if index_path.exists() else {}
    manifest = {"archived_at": datetime.now().astimezone().isoformat(),
                "purpose": "统一入口改造：归档现有旧研究结果；不重新计算或修改内容", "files": [], "moves": []}
    for source, relative, key in sources:
        source = source.resolve()
        target = (destination / relative).resolve()
        # Verify each resolved move remains in the explicitly authorized project.
        if not source.is_relative_to(ROOT.resolve()) or not target.is_relative_to(destination.resolve()):
            raise ValueError(f"Unsafe move: {source} -> {target}")
        files = sorted(source.rglob("*")) if source.is_dir() else [source]
        records = []
        for file in files:
            if file.is_file():
                suffix = file.relative_to(source) if source.is_dir() else Path()
                future = target / suffix if source.is_dir() else target
                logical = (Path(key) / suffix).as_posix()
                records.append({"old_path": file.relative_to(ROOT).as_posix(),
                                "path": future.relative_to(PRETEST_ROOT).as_posix(),
                                "key": logical, "sha256": sha256(file), "bytes": file.stat().st_size})
        target.parent.mkdir(parents=True, exist_ok=True)
        if target.exists():
            raise FileExistsError(target)
        source.rename(target)
        for record in records:
            if sha256(PRETEST_ROOT / record["path"]) != record["sha256"]:
                raise RuntimeError(f"Archive checksum mismatch: {record}")
            index[record["key"]] = {**record, "run_id": stamp, "status": "archived",
                                    "purpose": manifest["purpose"]}
        manifest["files"].extend(records)
        manifest["moves"].append({"from": str(source), "to": str(target), "files": len(records), "verified": True})
        # Incremental journal/index makes completed moves recoverable after an interruption.
        write_json(destination / "archive_manifest.json", manifest)
        write_json(index_path, index)
    write_json(report, manifest)
    print(f"Archived {len(manifest['files'])} files; SHA256 verified; destination: {destination}")


if __name__ == "__main__":
    archive()

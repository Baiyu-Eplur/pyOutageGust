"""Legacy task dispatcher. User switches and parameters live in main.py only."""
from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import runpy
import subprocess
import sys
import time
import traceback
from datetime import datetime, timedelta

from pretest_paths import PRETEST_ROOT, PROJECT_ROOT

# These modules supply functions to the registered analyses; they have no
# independent command-line operation. r02_input_pipeline has an explicit adapter.
SUPPORT_MODULES = {
    "appendix_h_20260906/appendix_h_common.py",
    "dev_sample_decontamination/clean_sample_builder.py",
    "event_input_repair/r02_events.py",
    "final_combined_analysis/figure_style.py",
}


def available_tasks():
    paths = {p.relative_to(PROJECT_ROOT / "scripts").with_suffix("").as_posix(): p
             for p in (PROJECT_ROOT / "scripts").rglob("*.py")
             if p.relative_to(PROJECT_ROOT / "scripts").as_posix() not in SUPPORT_MODULES}
    paths["review_package/run_main_regression"] = PROJECT_ROOT / "review_package/code/run_main_regression.py"
    return paths


def category(key):
    group, name = key.split("/", 1)
    if name.startswith("figure") or name.startswith("make_"):
        return "figures"
    if group in {"pipeline_v2", "model_review_package_20260907"} or name.startswith("build_"):
        return "data"
    if "audit" in group or group == "event_input_repair" or name.startswith("diag_"):
        return "checks"
    if "fit" in name or group == "review_package":
        return "models"
    return "analysis"


def write_json(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_suffix(path.suffix + ".tmp")
    temp.write_text(json.dumps(value, ensure_ascii=False, indent=2), encoding="utf-8")
    temp.replace(path)


def sha256(path):
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def _reserve_run():
    now = datetime.now().astimezone()
    for n in range(86400):
        run_id = (now + timedelta(seconds=n)).strftime("%Y%m%d%H%M%S")
        directory = PRETEST_ROOT / "runs" / run_id
        try:
            directory.mkdir(parents=True, exist_ok=False)
            return run_id, directory
        except FileExistsError:
            continue
    raise RuntimeError("Could not allocate an unused run directory")


def run_pretests(switches, *, purpose, dry_run=0, continue_on_error=0, python_executable=None):
    tasks = available_tasks()
    if set(switches) != set(tasks):
        raise ValueError(f"main.py 开关清单与脚本不一致。缺少: {sorted(set(tasks)-set(switches))}; 多余: {sorted(set(switches)-set(tasks))}")
    if any(type(v) is not int or v not in (0, 1) for v in switches.values()):
        raise ValueError("所有步骤开关必须为整数 0 或 1")
    if any(type(v) is not int or v not in (0, 1) for v in [dry_run, continue_on_error]):
        raise ValueError("DRY_RUN / CONTINUE_ON_ERROR 必须为 0 或 1")
    if not isinstance(purpose, str) or not purpose.strip():
        raise ValueError("请在 main.py 的 RUN_PURPOSE 写明本次运行目的")
    enabled = [k for k, v in switches.items() if v == 1]
    interpreter = str(python_executable or sys.executable)
    PRETEST_ROOT.mkdir(parents=True, exist_ok=True)
    # A single writer protects the reusable-output index from lost updates.
    lock = PRETEST_ROOT / ".run.lock"
    try:
        handle = lock.open("x", encoding="utf-8")
    except FileExistsError:
        raise RuntimeError(f"已有运行锁 {lock}。若上次进程被强制结束，请确认无运行进程后移除该锁。") from None
    with handle:
        handle.write(str(os.getpid()))
    run_dir = None
    try:
        run_id, run_dir = _reserve_run()
        manifest = {"run_id": run_id, "purpose": purpose.strip(),
                    "started_at": datetime.now().astimezone().isoformat(),
                    "python": interpreter, "dry_run": bool(dry_run), "status": "running",
                    "switches": switches, "steps": [], "outputs": [],
                    "entry_sha256": sha256(PROJECT_ROOT / "main.py")}
        manifest["code_sha256"] = {
            p.relative_to(PROJECT_ROOT).as_posix(): sha256(p)
            for p in [*sorted((PROJECT_ROOT / "scripts").rglob("*.py")),
                      *sorted((PROJECT_ROOT / "review_package/code").glob("*.py")),
                      PROJECT_ROOT / "main.py", Path(__file__).resolve(), PROJECT_ROOT / "pretest_paths.py"]}
        write_json(run_dir / "run.json", manifest)
        print(f"运行 {run_id}: {purpose}\n启用 {len(enabled)} 步；记录: {run_dir}", flush=True)
        if dry_run:
            for key in enabled:
                print(f"  [{category(key)}] {key}", flush=True)
            manifest["status"] = "planned"
        elif not enabled:
            manifest["status"] = "no_steps"
            print("所有步骤均为 0；未执行分析。请修改 main.py 顶部开关。", flush=True)
        else:
            for number, key in enumerate(enabled, 1):
                path = tasks[key]
                # Per-step isolation keeps partial failures and different legacy
                # versions from overwriting each other's products in one run.
                output_root = PRETEST_ROOT / category(key) / run_id / f"{number:03d}"
                output_root.mkdir(parents=True)
                step_dir = run_dir / f"{number:03d}"
                step_dir.mkdir()
                step = {"task": key, "script": str(path.relative_to(PROJECT_ROOT)),
                        "source_sha256": sha256(path), "status": "running",
                        "started_at": datetime.now().astimezone().isoformat(),
                        "output_root": str(output_root.relative_to(PRETEST_ROOT))}
                manifest["steps"].append(step)
                write_json(run_dir / "run.json", manifest)
                env = os.environ.copy()
                env.update(PRETEST_OUTPUT_ROOT=str(output_root), PRETEST_INPUT_LOG=str(step_dir / "inputs.jsonl"),
                           PRETEST_STEP_DIR=str(step_dir), PYTHONUTF8="1", PYTHONIOENCODING="utf-8",
                           PYTHONUNBUFFERED="1",
                           PYTHONDONTWRITEBYTECODE="1", MPLBACKEND="Agg", MPLCONFIGDIR=str(step_dir / "mpl"),
                           TEMP=str(step_dir / "tmp"), TMP=str(step_dir / "tmp"))
                (step_dir / "tmp").mkdir()
                print(f"[{number}/{len(enabled)}] {key}", flush=True)
                start = time.monotonic()
                try:
                    with (step_dir / "console.log").open("w", encoding="utf-8") as log:
                        process = subprocess.Popen([interpreter, "-B", str(Path(__file__).resolve()), "--worker", key],
                                                   cwd=PROJECT_ROOT, env=env, stdout=subprocess.PIPE,
                                                   stderr=subprocess.STDOUT, text=True, encoding="utf-8", errors="replace")
                        try:
                            for line in process.stdout:
                                log.write(line)
                                log.flush()
                                print(line, end="", flush=True)
                            step["returncode"] = process.wait()
                        except BaseException:
                            process.terminate()
                            process.wait()
                            raise
                    step["status"] = "completed" if step["returncode"] == 0 else "failed"
                except Exception as exc:
                    step.update(status="failed", error=repr(exc))
                step["seconds"] = round(time.monotonic() - start, 3)
                step["finished_at"] = datetime.now().astimezone().isoformat()
                artifacts = []
                for file in sorted(output_root.rglob("*")):
                    if file.is_file():
                        artifacts.append({"key": file.relative_to(output_root).as_posix(),
                                          "path": file.relative_to(PRETEST_ROOT).as_posix(),
                                          "bytes": file.stat().st_size, "sha256": sha256(file),
                                          "task": key, "status": step["status"]})
                manifest["outputs"].extend(artifacts)
                # Failure outputs remain visible for diagnosis but never become inputs.
                if step["status"] == "completed":
                    index_path = PRETEST_ROOT / "latest.json"
                    index = json.loads(index_path.read_text(encoding="utf-8")) if index_path.exists() else {}
                    for artifact in artifacts:
                        index[artifact["key"]] = {**artifact, "run_id": run_id, "purpose": purpose}
                    write_json(index_path, index)
                write_json(run_dir / "run.json", manifest)
                if step["status"] == "failed" and not continue_on_error:
                    break
            manifest["status"] = "failed" if any(s["status"] == "failed" for s in manifest["steps"]) else "completed"
        manifest["finished_at"] = datetime.now().astimezone().isoformat()
        write_json(run_dir / "run.json", manifest)
        lines = [f"# pretest {run_id}", "", f"目的：{purpose}", f"状态：{manifest['status']}", "",
                 "| 步骤 | 状态 | 结果目录 |", "|---|---|---|"]
        lines.extend(f"| {s['task']} | {s['status']} | {s['output_root']} |" for s in manifest["steps"])
        (run_dir / "README.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
        print(f"运行结束: {manifest['status']}；详见 {run_dir / 'run.json'}", flush=True)
        return manifest
    except BaseException as exc:
        if run_dir is not None:
            manifest["status"] = "interrupted" if isinstance(exc, KeyboardInterrupt) else "failed"
            manifest["error"] = repr(exc)
            manifest["finished_at"] = datetime.now().astimezone().isoformat()
            if manifest["steps"] and manifest["steps"][-1]["status"] == "running":
                manifest["steps"][-1]["status"] = manifest["status"]
            write_json(run_dir / "run.json", manifest)
        raise
    finally:
        lock.unlink()


def _write_guard(output_root, step_dir):
    """Reject unintended Python file writes outside this step's output/log dirs."""
    allowed = [output_root.resolve(), step_dir.resolve()]
    def check(value, mkdir=False):
        if not isinstance(value, (str, bytes, os.PathLike)):
            return
        path = Path(os.fsdecode(value)).resolve()
        if os.fsdecode(value).lower() in {"nul", os.devnull.lower()}:
            return
        if mkdir and path.is_dir():
            return
        if not any(path.is_relative_to(root) for root in allowed):
            raise PermissionError(f"pretest 拒绝向本步结果/日志目录之外写入: {path}")
    def hook(event, args):
        if event == "open":
            mode, flags = args[1], args[2]
            if (isinstance(mode, str) and any(c in mode for c in "wax+")) or (isinstance(flags, int) and flags & (os.O_WRONLY | os.O_RDWR | os.O_CREAT | os.O_TRUNC)):
                check(args[0])
        elif event in {"os.mkdir", "os.remove", "os.rmdir"}:
            check(args[0], mkdir=event == "os.mkdir")
        elif event in {"os.rename", "os.link", "os.symlink"}:
            check(args[0]); check(args[1])
    sys.addaudithook(hook)


def _worker(key):
    sys.dont_write_bytecode = True
    output_root = Path(os.environ["PRETEST_OUTPUT_ROOT"])
    step_dir = Path(os.environ["PRETEST_STEP_DIR"])
    _write_guard(output_root, step_dir)
    path = available_tasks()[key]
    sys.path.insert(0, str(path.parent))
    sys.argv = [str(path)]
    if key == "event_input_repair/r02_input_pipeline":
        namespace = runpy.run_path(str(path))
        frame, summary = namespace["step0_build_sample"]()
        frame, coverage = namespace["step1_lad_gapfill"](frame)
        write_json(output_root / "event_input_repair/input_summary.json", {**summary, "coverage": coverage})
    else:
        runpy.run_path(str(path), run_name="__main__")


if __name__ == "__main__":
    if len(sys.argv) == 3 and sys.argv[1] == "--worker":
        try:
            _worker(sys.argv[2])
        except Exception:
            traceback.print_exc()
            raise SystemExit(1)
    else:
        # No second copy of switches: direct invocation uses main.py as well.
        from main import main
        raise SystemExit(main())

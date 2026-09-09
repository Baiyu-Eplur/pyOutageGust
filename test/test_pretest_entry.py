"""Regression tests for orchestration, result reuse, and failure isolation."""
import ast
import io
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
import main
import pretestmain as runner
import pretest_paths as paths


class PretestEntryTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.pre = self.root / "results/pretest"
        self.pre.mkdir(parents=True)
        for module in [runner, paths]:
            p = patch.object(module, "PRETEST_ROOT", self.pre)
            p.start(); self.addCleanup(p.stop)
        paths._index.cache_clear()
        self.addCleanup(paths._index.cache_clear)
        self.output = self.pre / "figures/20260909000000/001"
        self.output.mkdir(parents=True)
        p = patch.dict(os.environ, {"PRETEST_OUTPUT_ROOT": str(self.output), "PRETEST_INPUT_LOG": ""})
        p.start(); self.addCleanup(p.stop)
        self.switches = dict.fromkeys(runner.available_tasks(), 0)

    def test_registry_covers_all_scripts_and_support_modules(self):
        actual = {p.relative_to(ROOT / "scripts").as_posix() for p in (ROOT / "scripts").rglob("*.py")}
        registered = {k + ".py" for k in runner.available_tasks() if not k.startswith("review_package/")}
        self.assertEqual(actual, registered | runner.SUPPORT_MODULES)
        self.assertEqual(set(main.PRETEST_STEPS), set(runner.available_tasks()))

    def test_all_disabled_does_not_import_or_spawn_analyses(self):
        with patch.object(runner.subprocess, "Popen", side_effect=AssertionError("must not spawn")):
            run = runner.run_pretests(self.switches, purpose="all disabled")
        self.assertEqual(run["status"], "no_steps")
        self.assertFalse(run["outputs"])
        self.assertEqual(run["purpose"], "all disabled")

    def test_dry_run_does_not_execute_enabled_step(self):
        self.switches["pipeline_v2/main1_v2"] = 1
        with patch.object(runner.subprocess, "Popen", side_effect=AssertionError("must not spawn")):
            run = runner.run_pretests(self.switches, purpose="plan only", dry_run=1)
        self.assertEqual(run["status"], "planned")
        self.assertEqual(len(run["run_id"]), 14)

    def test_invalid_switch_or_missing_purpose_rejected(self):
        for value in [2, "1", True]:
            self.switches[next(iter(self.switches))] = value
            with self.assertRaises(ValueError):
                runner.run_pretests(self.switches, purpose="invalid")
        self.switches[next(iter(self.switches))] = 0
        with self.assertRaises(ValueError):
            runner.run_pretests(self.switches, purpose=" ")

    def test_read_reuses_archive_without_redirecting_writes(self):
        old = self.pre / "archive/20260909000000/example/raw/a.csv"
        old.parent.mkdir(parents=True); old.write_text("old", encoding="utf-8")
        runner.write_json(self.pre / "latest.json", {"example/raw/a.csv": {"path": old.relative_to(self.pre).as_posix()}})
        writable = paths.result_path("example/raw/a.csv")
        self.assertEqual(paths.read_input(writable), old)
        self.assertNotEqual(writable, old)
        writable.parent.mkdir(parents=True, exist_ok=True); writable.write_text("new", encoding="utf-8")
        self.assertEqual(paths.read_input(writable), writable)
        self.assertEqual(old.read_text(encoding="utf-8"), "old")

    def test_missing_prerequisite_has_actionable_error(self):
        with self.assertRaisesRegex(FileNotFoundError, "main.py"):
            paths.read_input(paths.result_path("missing/file.csv"))

    def test_result_path_requires_context_and_rejects_escape(self):
        with self.assertRaises(ValueError):
            paths.result_path("../../../../escape.csv")
        with patch.dict(os.environ, {}, clear=True), self.assertRaises(RuntimeError):
            paths.result_path("file.csv")

    def test_same_second_run_names_do_not_collide(self):
        first = runner._reserve_run()[0]
        second = runner._reserve_run()[0]
        self.assertNotEqual(first, second)
        self.assertEqual(len(first), 14)
        self.assertEqual(len(second), 14)

    def test_failure_artifacts_are_logged_but_not_published(self):
        key = "final_combined_analysis/figure4_dose_response"
        self.switches[key] = 1
        runner.write_json(self.pre / "latest.json", {"keep": {"path": "prior.csv"}})
        class Failure:
            stdout = io.StringIO("test failure\n")
            def __init__(self, *args, **kwargs):
                out = Path(kwargs["env"]["PRETEST_OUTPUT_ROOT"])
                (out / "partial.csv").write_text("partial", encoding="utf-8")
            def wait(self):
                return 1
        with patch.object(runner.subprocess, "Popen", Failure):
            run = runner.run_pretests(self.switches, purpose="failure contract")
        self.assertEqual(run["status"], "failed")
        self.assertEqual(run["outputs"][0]["status"], "failed")
        self.assertEqual(json.loads((self.pre / "latest.json").read_text()), {"keep": {"path": "prior.csv"}})
        self.assertFalse((self.pre / ".run.lock").exists())

    def test_write_guard_rejects_source_and_external_writes(self):
        code = """import sys
from pathlib import Path
from pretestmain import _write_guard
out=Path(sys.argv[1]); other=Path(sys.argv[2])
_write_guard(out,out)
(out/'allowed.txt').write_text('ok')
try:
    (other/'blocked.txt').write_text('bad')
except PermissionError:
    pass
else:
    raise AssertionError('unexpected write')
"""
        result = subprocess.run([sys.executable, "-B", "-c", code, str(self.output), str(self.root)], cwd=ROOT,
                                capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertFalse((self.root / "blocked.txt").exists())

    def test_all_active_sources_parse(self):
        sources = list((ROOT / "scripts").rglob("*.py")) + list((ROOT / "review_package/code").glob("*.py"))
        sources += [ROOT / n for n in ["main.py", "pretestmain.py", "pretest_paths.py"]]
        for path in sources:
            with self.subTest(path=path):
                ast.parse(path.read_text(encoding="utf-8-sig"), filename=str(path))


if __name__ == "__main__":
    unittest.main(verbosity=2)

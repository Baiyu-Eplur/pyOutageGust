"""One-time, source-preserving path migration (2026-09-09). Do not rerun."""
import ast
import hashlib
import io
import json
from pathlib import Path
import re
import tokenize

ROOT = Path(__file__).resolve().parents[2]


def offsets(text):
    lines = text.splitlines(keepends=True)
    starts = [0]
    for line in lines:
        starts.append(starts[-1] + len(line))
    def pos(line, byte):
        return starts[line - 1] + len(lines[line - 1].encode()[:byte].decode())
    return pos


def migrate(path):
    original = path.read_text(encoding="utf-8-sig")
    text = original
    edits = []
    lines = text.splitlines(keepends=True)
    starts = [0]
    for line in lines:
        starts.append(starts[-1] + len(line))
    v2 = path.parent.name == "pipeline_v2"
    for token in tokenize.generate_tokens(io.StringIO(text).readline):
        if token.type != tokenize.STRING:
            continue
        try:
            value = ast.literal_eval(token.string)
        except (SyntaxError, ValueError):
            continue
        if not isinstance(value, str) or "\n" in value:
            continue
        norm = value.replace("\\", "/")
        expression = None
        old = "D:/Pyprogramme/STST2603"
        new = "D:/Pyprogramme/pyOutageGust"
        for prefix in [old + "/claude_branch", new]:
            if norm == prefix or norm.startswith(prefix + "/"):
                rel = norm[len(prefix):].lstrip("/")
                if rel.startswith("results/"):
                    expression = f"str(result_path({rel[8:]!r}))"
                elif rel == "review_package/data" or rel.startswith("review_package/results"):
                    expression = f"str(result_path({rel.replace('review_package/results', 'review_package/regression')!r}))"
                else:
                    expression = f"str(project_path({rel!r}))"
                break
        tmp = re.match(r"/tmp/branch_work\d*/results/(.*)", norm)
        if tmp:
            expression = f"str(result_path({tmp[1]!r}))"
        if expression is None:
            for prefix in [old, "/mnt/user-data/uploads/STST2603"]:
                if norm == prefix or norm.startswith(prefix + "/"):
                    rel = norm[len(prefix):].lstrip("/")
                    if v2 and rel.startswith("data/"):
                        expression = f"str(data_path({rel[5:]!r}))"
                    else:
                        expression = f"str(external_path({rel!r}))"
                    break
        if v2 and norm.startswith("data/"):
            expression = f"str(data_path({norm[5:]!r}))"
        if expression:
            edits.append((starts[token.start[0]-1]+token.start[1], starts[token.end[0]-1]+token.end[1], expression))
    for start, end, value in reversed(edits):
        text = text[:start] + value + text[end:]

    if v2:
        text = re.sub(r'(DATA_DIR|DATA) = (BASE_DIR|BASE) / "data"', r'\1 = data_path()', text)
        text = text.replace('REQUESTS_CACHE_PATH = BASE_DIR / ".weather_cache_master"', 'REQUESTS_CACHE_PATH = data_path(".weather_cache_master")')
    if path.name == "audit_pipeline.py":
        text = text.replace("PROJECT = ROOT.parent", "PROJECT = external_path()")
        text = text.replace("sys.path.insert(0, str(PROJECT / '.venv/Lib/site-packages'))", "# Use the interpreter selected by main.py.")
        text = text.replace("OUT = ROOT / 'results/code_audit_20260905'", "OUT = result_path('code_audit_20260905')")
        text = text.replace("SRC = PROJECT / 'rebuild_v3_full_stage/outputs/ukpn_full_stage_dataset_v3.csv'", "SRC = external_path('rebuild_v3_full_stage/outputs/ukpn_full_stage_dataset_v3.csv')")
    if path.name == "test_r02_events.py":
        text = text.replace("sys.dont_write_bytecode=True;sys.path.insert(0,str(ROOT.parent/'.venv/Lib/site-packages'))", "sys.dont_write_bytecode=True")
    if path.name == "run_main_regression.py":
        text = text.replace('Path(__file__).resolve().parent.parent / "data"', 'result_path("review_package/data")')
        text = text.replace('Path(__file__).resolve().parent.parent / "results"', 'result_path("review_package/regression")')

    # Wrap read arguments only. Keep the computation, comments and formatting.
    tree = ast.parse(text)
    pos = offsets(text)
    wrappers = set()
    read_functions = {"read_csv", "read_parquet", "read_pickle", "read_excel", "read_file", "ExcelFile", "loadtxt", "listdir"}
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        func = node.func
        target = None
        if isinstance(func, ast.Attribute) and func.attr in read_functions and node.args:
            target = node.args[0]
        elif isinstance(func, ast.Attribute) and func.attr in {"read_text", "read_bytes"}:
            target = func.value
        elif isinstance(func, ast.Attribute) and func.attr == "open":
            mode = node.args[0] if node.args else next((k.value for k in node.keywords if k.arg == "mode"), ast.Constant("r"))
            if isinstance(mode, ast.Constant) and isinstance(mode.value, str) and not any(c in mode.value for c in "wax+"):
                target = func.value
        elif isinstance(func, ast.Name) and func.id == "open" and node.args:
            mode = node.args[1] if len(node.args) > 1 else next((k.value for k in node.keywords if k.arg == "mode"), ast.Constant("r"))
            if isinstance(mode, ast.Constant) and isinstance(mode.value, str) and not any(c in mode.value for c in "wax+"):
                target = node.args[0]
        if target is not None:
            wrappers.add((pos(target.lineno, target.col_offset), pos(target.end_lineno, target.end_col_offset)))
    inserts = []
    for start, end in wrappers:
        inserts.extend([(start, "read_input("), (end, ")")])
    for position, value in sorted(inserts, reverse=True):
        text = text[:position] + value + text[position:]
    if text != original:
        tree = ast.parse(text)
        end_line = 0
        for i, node in enumerate(tree.body):
            if (i == 0 and isinstance(node, ast.Expr) and isinstance(node.value, ast.Constant) and isinstance(node.value.value, str)) or (isinstance(node, ast.ImportFrom) and node.module == "__future__"):
                end_line = node.end_lineno
            else:
                break
        parts = text.splitlines(keepends=True)
        bootstrap = ('\n# Shared pretest paths; all execution is dispatched from main.py.\n'
                     'import sys as _pretest_sys\nfrom pathlib import Path as _PretestPath\n'
                     '_pretest_sys.path.insert(0, str(_PretestPath(__file__).resolve().parents[2]))\n'
                     'from pretest_paths import project_path, result_path, external_path, data_path, read_input\n\n')
        parts.insert(end_line, bootstrap)
        text = ''.join(parts)
        ast.parse(text)
        path.write_text(text, encoding="utf-8")
    return {"file": path.relative_to(ROOT).as_posix(), "changed": text != original,
            "before_sha256": hashlib.sha256(original.encode()).hexdigest(),
            "after_sha256": hashlib.sha256(text.encode()).hexdigest(),
            "path_literals": len(edits), "read_sites": len(wrappers)}


if __name__ == "__main__":
    report = ROOT / "docs/migration_history/pretest_source_changes_20260909.json"
    if report.exists():
        raise SystemExit("Already migrated; this one-time tool must not be rerun.")
    files = sorted((ROOT / "scripts").rglob("*.py")) + list((ROOT / "review_package/code").glob("*.py"))
    changes = [migrate(p) for p in files]
    report.write_text(json.dumps(changes, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Inventoried {len(changes)} files; changed {sum(c['changed'] for c in changes)}")

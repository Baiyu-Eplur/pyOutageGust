"""Create the X01 return package without uploading or altering source inputs."""
from pathlib import Path
import hashlib
import json
import zipfile

ROOT = Path(__file__).resolve().parents[1]
ZIP = ROOT / "RETURN_PACKAGE_X01.zip"
MANIFEST = ROOT / "RETURN_PACKAGE_MANIFEST.json"
EXCLUDED = {
    "RETURN_PACKAGE_X01.zip": "the package cannot contain itself",
    "frozen_sources/input/R02_event_master.parquet": "large local frozen database; retained locally with SHA-256 in DATA_MANIFEST.json",
}


def sha(path):
    h=hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda:f.read(1<<20),b""):
            h.update(chunk)
    return h.hexdigest()


def main():
    files=[]
    for p in ROOT.rglob("*"):
        if not p.is_file():
            continue
        rel=p.relative_to(ROOT).as_posix()
        if rel in EXCLUDED or rel=="RETURN_PACKAGE_MANIFEST.json":
            continue
        files.append(p)
    files.sort(key=lambda p:p.relative_to(ROOT).as_posix())
    payload={"package":"RETURN_PACKAGE_X01.zip","run_id":ROOT.name,"included_file_count":len(files)+1,"excluded":EXCLUDED,
             "included_files":[{"path":p.relative_to(ROOT).as_posix(),"bytes":p.stat().st_size,"sha256":sha(p)} for p in files],
             "note":"RETURN_PACKAGE_MANIFEST.json is included in the ZIP but omitted from its own digest list."}
    MANIFEST.write_text(json.dumps(payload,ensure_ascii=False,indent=2),encoding="utf-8")
    with zipfile.ZipFile(ZIP,"w",compression=zipfile.ZIP_DEFLATED,compresslevel=6) as z:
        for p in files+[MANIFEST]:
            z.write(p,p.relative_to(ROOT).as_posix())
    with zipfile.ZipFile(ZIP,"r") as z:
        bad=z.testzip()
        names=z.namelist()
    if bad is not None or "RETURN_TO_CHATGPT_X01.md" not in names or "tables/model_leaderboard.csv" not in names:
        raise SystemExit(f"package validation failed: {bad}")
    print(json.dumps({"zip":str(ZIP),"bytes":ZIP.stat().st_size,"members":len(names),"testzip":bad},ensure_ascii=False))


if __name__=="__main__":
    main()

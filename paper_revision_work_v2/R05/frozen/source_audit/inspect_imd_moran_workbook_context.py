from __future__ import annotations

from pathlib import Path

import pandas as pd


IMD_FILE = Path(r"D:\Pyprogramme\STST2603\data\localincomedeprivationdata.xlsx")


def main() -> None:
    xl = pd.ExcelFile(IMD_FILE)
    print("Sheets:")
    for s in xl.sheet_names:
        print("-", s)

    print("\nTop rows from sheets containing ranking/data context:")
    for sheet in xl.sheet_names:
        if "rank" in sheet.lower() or "indicator" in sheet.lower() or "read" in sheet.lower() or "note" in sheet.lower():
            print(f"\n--- {sheet} ---")
            df = pd.read_excel(IMD_FILE, sheet_name=sheet, header=None, nrows=12)
            with pd.option_context("display.max_columns", 12, "display.width", 220):
                print(df)

    print("\nCells mentioning Moran/profile/spatial context:")
    needles = "Moran|moran|profile|Profile|deprivation gap|spatial|cluster"
    for sheet in xl.sheet_names:
        df = pd.read_excel(IMD_FILE, sheet_name=sheet, header=None, dtype=str)
        mask = df.apply(lambda col: col.str.contains(needles, case=False, na=False))
        coords = []
        for c in mask.columns:
            for r in mask.index[mask[c]].tolist():
                coords.append((r, c, df.iat[r, c]))
        if coords:
            print(f"\n--- {sheet} ---")
            for r, c, val in coords[:60]:
                print(f"row={r} col={c}: {val}")

    print("\nExpanded Notes rows 29-33:")
    notes = pd.read_excel(IMD_FILE, sheet_name="Notes", header=None, dtype=str)
    for r in range(29, 34):
        vals = [str(x) for x in notes.iloc[r].dropna().tolist()]
        print(f"{r}: {' '.join(vals)}")


if __name__ == "__main__":
    main()

"""Left-preserving LAD and socioeconomic enrichment for the v3 stage dataset."""

from __future__ import annotations

import json
from pathlib import Path

import geopandas as gpd
import numpy as np
import pandas as pd


PROJECT_ROOT = Path(r"D:\Pyprogramme\STST2603")
RUN_ROOT = PROJECT_ROOT / "rebuild_v3_full_stage"
INPUT = RUN_ROOT / "outputs" / "02_ukpn_stage_weather_v3.csv"
OUTPUT = RUN_ROOT / "outputs" / "ukpn_full_stage_dataset_v3.csv"
QA_JSON = RUN_ROOT / "logs" / "03_final_dataset_qa.json"

LAD_SHP = (
    PROJECT_ROOT
    / "data"
    / "Local_Authority_Districts_December_2021_UK_BGC_2022"
    / "LAD_DEC_2021_UK_BGC.shp"
)
LAD_FEATURES = (
    PROJECT_ROOT
    / "data"
    / "Local_Authority_Districts_December_2021_UK_BGC_2022"
    / "LAD_full_dataset_with_dno.csv"
)
POPULATION = PROJECT_ROOT / "data" / "population_lad_long.csv"
VALIDATED_IMD = PROJECT_ROOT / "data" / "new" / "ukpn_master_with_income_deprivation_crosswalk.csv"
VALIDATED_GVA = PROJECT_ROOT / "data" / "new" / "ukpn_master_final.csv"

EXPECTED_SOURCE_ROWS = 237_901


def unique_lookup_from_validated(path, key, columns):
    lookup = pd.read_csv(path, usecols=[key] + columns, low_memory=False)
    lookup[key] = lookup[key].astype("string").str.strip()
    conflicting = lookup.groupby(key, dropna=False)[columns].nunique(dropna=False).max(axis=1)
    if (conflicting > 1).any():
        bad = conflicting[conflicting > 1].index.tolist()[:10]
        raise ValueError(f"Validated lookup has conflicting values for {key}: {bad}")
    return lookup.drop_duplicates(subset=[key], keep="first")


def main():
    df = pd.read_csv(INPUT, low_memory=False)
    if len(df) != EXPECTED_SOURCE_ROWS:
        raise ValueError(f"Weather input row count is {len(df):,}, expected {EXPECTED_SOURCE_ROWS:,}")
    if not df["source_row_number"].is_unique:
        raise ValueError("source_row_number is not unique before downstream enrichment")

    source_columns = set(df.columns)

    # Spatial matching runs only on valid coordinates; all source rows are restored by left merge.
    valid = df["lat"].between(49, 61) & df["lon"].between(-9, 3)
    points = gpd.GeoDataFrame(
        df.loc[valid, ["source_row_number", "lat", "lon"]].copy(),
        geometry=gpd.points_from_xy(df.loc[valid, "lon"], df.loc[valid, "lat"]),
        crs="EPSG:4326",
    )
    lad = gpd.read_file(LAD_SHP).to_crs("EPSG:4326")
    lad_join = gpd.sjoin(points, lad, how="left", predicate="within")
    if lad_join["source_row_number"].duplicated().any():
        lad_join = lad_join.drop_duplicates("source_row_number", keep="first")
    lad_columns = [c for c in lad.columns if c != "geometry"]
    spatial_lookup = pd.DataFrame(lad_join[["source_row_number"] + lad_columns])
    df = df.merge(spatial_lookup, on="source_row_number", how="left", validate="one_to_one")

    # Population is year-specific and uses the same direct LAD21->LAD23 code match as v1.
    df["year"] = pd.to_datetime(df["clean_start"], errors="coerce", utc=True).dt.year
    pop = pd.read_csv(POPULATION, low_memory=False).rename(columns={"LAD23CD": "LAD21CD"})
    pop["LAD21CD"] = pop["LAD21CD"].astype("string").str.strip()
    pop["year"] = pd.to_numeric(pop["year"], errors="coerce").astype("Int64")
    if pop.duplicated(["LAD21CD", "year"]).any():
        raise ValueError("Population lookup is not unique by LAD21CD and year")
    df["LAD21CD"] = df["LAD21CD"].astype("string").str.strip()
    df = df.merge(pop, on=["LAD21CD", "year"], how="left", suffixes=("", "_pop"), validate="many_to_one")

    # Reuse the already validated static Buckinghamshire crosswalk outputs as lookup tables.
    df["LADCD"] = df["LAD21CD"]
    imd_columns = [
        "LADNM",
        "profile",
        "rural_urban_classification",
        "deprivation_gap_pct",
        "deprivation_gap_rank",
        "morans_i",
        "morans_i_rank",
        "income_deprivation_rate",
        "income_deprivation_rate_rank",
        "income_deprivation_rate_quintile",
    ]
    imd = unique_lookup_from_validated(VALIDATED_IMD, "LADCD", imd_columns)
    df = df.merge(imd, on="LADCD", how="left", validate="many_to_one")

    gva_columns = [
        "population_2016",
        "gva_total",
        "gva_pc",
        "gva_prod",
        "gva_manufacturing",
        "gva_construction",
        "gva_distribution",
        "gva_information",
        "gva_finance",
        "gva_realestate",
        "gva_professional",
        "gva_public",
        "gva_other",
        "gva_prod_share",
        "gva_manufacturing_share",
        "gva_construction_share",
        "gva_distribution_share",
        "gva_information_share",
        "gva_finance_share",
        "gva_realestate_share",
        "gva_professional_share",
        "gva_public_share",
        "gva_other_share",
    ]
    gva = unique_lookup_from_validated(VALIDATED_GVA, "LADCD", gva_columns)
    df = df.merge(gva, on="LADCD", how="left", validate="many_to_one")
    df["log_gva_pc"] = np.where(df["gva_pc"] > 0, np.log(df["gva_pc"]), np.nan)

    lad_features = pd.read_csv(LAD_FEATURES, low_memory=False)
    lad_features["LADCD"] = lad_features["LADCD"].astype("string").str.strip()
    lad_features = lad_features.drop_duplicates("LADCD", keep="first")
    df = df.merge(lad_features, on="LADCD", how="left", suffixes=("", "_lad"), validate="many_to_one")

    start = pd.to_datetime(df["Start Date and Time"], errors="coerce", utc=True)
    df["Daytime Indicator"] = ((start.dt.hour >= 6) & (start.dt.hour < 18)).astype("Int64")
    df["Hour"] = start.dt.hour
    df["Month"] = start.dt.month
    df["Weekday"] = start.dt.weekday

    if len(df) != EXPECTED_SOURCE_ROWS or not df["source_row_number"].is_unique:
        raise ValueError("A downstream merge changed the source row cardinality")
    df = df.sort_values("source_row_number", kind="stable").reset_index(drop=True)

    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(OUTPUT, index=False)

    qa = {
        "rows": int(len(df)),
        "columns": int(df.shape[1]),
        "source_rows_preserved": bool(len(df) == EXPECTED_SOURCE_ROWS),
        "source_row_number_unique": bool(df["source_row_number"].is_unique),
        "source_row_number_complete_sequence": bool(
            df["source_row_number"].tolist() == list(range(1, EXPECTED_SOURCE_ROWS + 1))
        ),
        "weather_status_counts": {
            str(k): int(v) for k, v in df["weather_status_v3"].value_counts(dropna=False).items()
        },
        "lad_match_rate": float(df["LAD21CD"].notna().mean()),
        "population_match_rate": float(df["population"].notna().mean()),
        "imd_match_rate": float(df["income_deprivation_rate"].notna().mean()),
        "gva_match_rate": float(df["gva_pc"].notna().mean()),
        "new_columns_after_weather": sorted(set(df.columns).difference(source_columns)),
    }
    QA_JSON.write_text(json.dumps(qa, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({k: v for k, v in qa.items() if k != "new_columns_after_weather"}, ensure_ascii=False, indent=2))
    print(f"Saved: {OUTPUT}")


if __name__ == "__main__":
    main()

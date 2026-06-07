from __future__ import annotations

import pandas as pd


JAPAN_POPULATION_ANCHORS = (
    (1980, 117_060_396, "Census"),
    (1985, 121_048_923, "Census"),
    (1990, 123_611_167, "Census"),
    (1995, 125_570_246, "Census"),
    (2000, 126_925_843, "Census"),
    (2005, 127_767_994, "Census"),
    (2010, 128_057_352, "Census"),
    (2015, 127_094_745, "Census"),
    (2020, 126_146_099, "Census"),
    (2070, 87_000_000, "IPSS 2023 projection"),
)


def japan_reference_frame() -> pd.DataFrame:
    anchors = pd.DataFrame(JAPAN_POPULATION_ANCHORS, columns=["calendar_year", "population", "source"])
    years = pd.DataFrame({"calendar_year": range(1980, 2071)})
    merged = years.merge(anchors[["calendar_year", "population"]], on="calendar_year", how="left")
    merged["population"] = merged["population"].interpolate(method="linear")
    baseline = float(anchors.loc[anchors["calendar_year"] == 1980, "population"].iloc[0])
    merged["population_index"] = merged["population"] / baseline
    return merged


def rmse_for_years(simulation: pd.Series, reference: pd.Series, years: tuple[int, ...]) -> float:
    errors = [(float(simulation.loc[year]) - float(reference.loc[year])) ** 2 for year in years]
    return float(sum(errors) / len(errors)) ** 0.5


def dataframe_to_markdown(frame: pd.DataFrame) -> str:
    columns = list(frame.columns)
    rows = [
        "| " + " | ".join(str(column) for column in columns) + " |",
        "| " + " | ".join("---" for _ in columns) + " |",
    ]
    for _, row in frame.iterrows():
        rows.append("| " + " | ".join(str(row[column]) for column in columns) + " |")
    return "\n".join(rows)

"""Read the region's land-use sentences and their polygons with DuckDB."""

import duckdb

from georeset_viz import config

SENTENCES_SQL = """
CREATE OR REPLACE TEMP TABLE sentences AS
WITH kept AS (
    SELECT id, text, source, url, polygon_ids[1] AS polygon
    FROM read_parquet($glob)
    WHERE region = $region AND language = $language AND landuse
      AND length(text) BETWEEN $min_chars AND $max_chars
), unique_text AS (
    SELECT text, min(id) AS id, arg_min(source, id) AS source,
           arg_min(url, id) AS url, arg_min(polygon, id) AS polygon
    FROM kept GROUP BY text
), ranked AS (
    SELECT *, row_number() OVER (PARTITION BY polygon ORDER BY id) AS rank FROM unique_text
)
SELECT text, source, url, polygon FROM ranked WHERE rank <= $cap ORDER BY polygon, id
"""

POLYGONS_SQL = """
SELECT polygon_id, name, osm_tag, lat, lon, area_m2, geometry::BLOB
FROM read_parquet($glob)
WHERE region = $region AND polygon_id IN (SELECT polygon FROM sentences)
ORDER BY polygon_id
"""


def extract(
    con: duckdb.DuckDBPyConnection, sentences_glob: str, polygons_glob: str
) -> tuple[dict[str, list], list[tuple]]:
    con.execute(
        SENTENCES_SQL,
        {
            "glob": sentences_glob,
            "region": config.REGION,
            "language": config.LANGUAGE,
            "min_chars": config.MIN_CHARS,
            "max_chars": config.MAX_CHARS,
            "cap": config.MAX_SENTENCES_PER_POLYGON,
        },
    )
    columns = ["text", "source", "url", "polygon"]
    rows = con.execute(f"SELECT {', '.join(columns)} FROM sentences").fetchall()
    sentences = {name: [row[i] for row in rows] for i, name in enumerate(columns)}
    polygons = con.execute(
        POLYGONS_SQL, {"glob": polygons_glob, "region": config.REGION}
    ).fetchall()
    return sentences, polygons

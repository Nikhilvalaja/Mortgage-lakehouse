from pyspark import pipelines as dp
from pyspark.sql import functions as F
from pyspark.sql.types import StringType, StructField, StructType

from vendor_drop.layout import ORIG_FIELDS, PERF_FIELDS

catalog = spark.conf.get("vd.catalog")  # set per target in resources/vendor_drop/pipeline.yml
inbound = f"/Volumes/{catalog}/landing/inbound"


def string_schema(fields: list[str]) -> StructType:
    """Every field as nullable STRING: Bronze keeps the vendor's bytes, Silver types them."""
    return StructType([StructField(name, StringType(), True) for name in fields])


def read_raw(kind: str, fields: list[str]):
    """Auto Loader stream over inbound/<servicer>/<period>/<kind>_*.txt."""
    return (
        spark.readStream.format("cloudFiles")
        .option("cloudFiles.format", "csv")
        .option("sep", "|")
        .option("header", "false")
        .option("cloudFiles.schemaEvolutionMode", "rescue")
        .option("rescuedDataColumn", "_rescued_data")
        .option("pathGlobFilter", f"{kind}_*.txt")
        .schema(string_schema(fields))
        .load(inbound)
        .withColumn("_source_file", F.col("_metadata.file_path"))
        .withColumn("servicer_id", F.regexp_extract("_source_file", r"inbound/([^/]+)/", 1))
        .withColumn("period", F.regexp_extract("_source_file", r"inbound/[^/]+/(\d{6})/", 1))
        .withColumn("_ingest_ts", F.current_timestamp())
    )


@dp.table(name="bronze.perf_raw", comment="Monthly performance rows exactly as delivered")
def perf_raw():
    return read_raw("perf", PERF_FIELDS)


@dp.table(name="bronze.orig_raw", comment="Loan origination rows exactly as delivered")
def orig_raw():
    return read_raw("orig", ORIG_FIELDS)

from pyspark import pipelines as dp
from pyspark.sql import functions as F

catalog = spark.conf.get("vd.catalog")
inbound = f"/Volumes/{catalog}/landing/inbound"


@dp.table(
    name="bronze.perf_raw",
    comment="Monthly performance lines as received",
)
def perf_raw():
    return (
        spark.readStream.format("cloudFiles")
        .option("cloudFiles.format", "csv")
        .option("sep", "|")
        .option("header", "false")
        .option("cloudFiles.inferColumnTypes", "false")
        .option("pathGlobFilter", "perf_*.txt")
        .option("rescuedDataColumn", "_rescued_data")
        .load(inbound)
        .withColumn("_source_file", F.col("_metadata.file_path"))
        .withColumn("_ingest_ts", F.current_timestamp())
    )

# glue_jobs/src/raw_to_bronze.py
import sys
from awsglue.utils import getResolvedOptions
from awsglue.context import GlueContext
from awsglue.job import Job
from pyspark.context import SparkContext
from pyspark.sql import functions as F
from pyspark.sql import types as T

args = getResolvedOptions(sys.argv, ["JOB_NAME", "raw_bucket", "processed_bucket"])
RAW_BUCKET = args["raw_bucket"]
PROC_BUCKET = args["processed_bucket"]

sc = SparkContext()
glue_ctx = GlueContext(sc)
spark = glue_ctx.spark_session
job = Job(glue_ctx)
job.init(args["JOB_NAME"], args)

spark.conf.set("spark.sql.sources.partitionOverwriteMode", "dynamic")

# Helpers
def to_float(expr):
    # remove commas and non-numeric chars
    return F.regexp_replace(
        F.regexp_replace(expr, ",", ""),
        r"[^0-9.]", ""
    ).cast(T.DoubleType())

def to_bool(expr):
    return (F.lower(F.col(expr)).isin("true", "1", "yes", "y")).cast("boolean")

# Read RAW CSVs (encoding tolerant)
df_raw = (
    spark.read
    .option("header", "true")
    .option("multiLine", "true")
    .option("escape", "\"")
    .option("quote", "\"")
    .option("encoding", "ISO-8859-1")
    .csv(f"s3://{RAW_BUCKET}/")
)

# Basic normalization
df = df_raw.select([F.col(c).alias(c.strip().lower()) for c in df_raw.columns])

# Parse / cast
df = (
    df
    .withColumn("actual_price_num", to_float(F.col("actual_price")))
    .withColumn("selling_price_num", to_float(F.col("selling_price")))
    .withColumn("average_rating_num", F.regexp_replace(F.col("average_rating"), r"[^0-9.]", "").cast("double"))
    .withColumn("out_of_stock_bool", to_bool("out_of_stock"))
    .withColumn("crawled_ts", F.to_timestamp(F.col("crawled_at"), "dd/MM/yyyy, HH:mm:ss"))
    .withColumn("ingestion_date", F.current_date())
    .dropDuplicates(["pid"])  # keep most recent record per pid if pid exists
)

# Prune to a clean bronze schema
bronze_cols = [
    "_id", "pid", "title", "brand", "category", "sub_category",
    "actual_price", "selling_price", "description", "discount",
    "average_rating", "average_rating_num", "out_of_stock", "out_of_stock_bool",
    "seller", "product_details", "crawled_at", "crawled_ts",
    "url", "images",
    "actual_price_num", "selling_price_num", "ingestion_date"
]
df_bronze = df.select([c for c in bronze_cols if c in df.columns])

# Write Bronze as Parquet (partition by ingestion_date for manageability)
out_path = f"s3://{PROC_BUCKET}/bronze/flipkart_fashion/"
(
    df_bronze
    .repartition(1)  # adjust for data size; remove for large volumes
    .write.mode("overwrite")
    .partitionBy("ingestion_date")
    .parquet(out_path)
)

job.commit()

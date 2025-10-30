import sys
from awsglue.utils import getResolvedOptions
from awsglue.context import GlueContext
from awsglue.job import Job
from pyspark.context import SparkContext
from pyspark.sql import functions as F, types as T

## --------------------------
##  Glue job initialization
## --------------------------
args = getResolvedOptions(sys.argv, [
    'JOB_NAME',
    'processed_bucket'
])

sc = SparkContext()
glueContext = GlueContext(sc)
spark = glueContext.spark_session
job = Job(glueContext)
job.init(args['JOB_NAME'], args)

processed_bucket = args['processed_bucket']

print("=== Starting Bronze → Silver transformation ===")

## --------------------------
## 1️⃣ Read Bronze data
## --------------------------
bronze_path = f"s3://{processed_bucket}/bronze/flipkart_fashion/"
df_bronze = spark.read.parquet(bronze_path)
print("Bronze data schema:")
df_bronze.printSchema()

## --------------------------
## 2️⃣ Normalize brand/category names
## --------------------------
df_silver = (
    df_bronze
    .withColumn("brand_norm", F.lower(F.trim(F.col("brand"))))
    .withColumn("category_norm", F.lower(F.trim(F.col("category"))))
)

## --------------------------
## 3️⃣ Parse product_details JSON safely
## --------------------------
map_schema = T.MapType(T.StringType(), T.StringType())

def parse_details(col):
    """Safely parse product_details JSON that may be array<map> or map."""
    array_col = F.from_json(col, T.ArrayType(map_schema))
    map_col = F.from_json(col, map_schema)
    return F.when(
        F.size(array_col) > 0, F.element_at(array_col, 1)
    ).otherwise(map_col)

df_silver = df_silver.withColumn(
    "details_map",
    F.when(
        (F.col("product_details").isNull()) |
        (F.length(F.trim(F.col("product_details"))) == 0),
        F.lit(None)
    ).otherwise(parse_details(F.col("product_details")))
)

## --------------------------
## 4️⃣ Compute derived fields
## --------------------------
df_silver = (
    df_silver
    .withColumn("discount_ratio",
                (F.col("actual_price_num") - F.col("selling_price_num")) /
                F.col("actual_price_num"))
    .withColumn("is_discounted",
                (F.col("discount_ratio") > 0).cast("boolean"))
    .withColumn("etl_updated_ts", F.current_timestamp())
)

## --------------------------
## 5️⃣ Write Silver data to S3
## --------------------------
silver_path = f"s3://{processed_bucket}/silver/flipkart_fashion/"
(
    df_silver
    .coalesce(1)
    .write
    .mode("overwrite")
    .parquet(silver_path)
)

print(f"✅ Silver data written to {silver_path}")

job.commit()

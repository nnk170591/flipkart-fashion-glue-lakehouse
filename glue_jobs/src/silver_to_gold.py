import sys
from awsglue.utils import getResolvedOptions
from awsglue.context import GlueContext
from awsglue.job import Job
from pyspark.context import SparkContext
from pyspark.sql import functions as F

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

print("=== Starting Silver → Gold aggregation ===")

## --------------------------
## 1️⃣ Read Silver data
## --------------------------
silver_path = f"s3://{processed_bucket}/silver/flipkart_fashion/"
df_silver = spark.read.parquet(silver_path)
print("Silver data schema:")
df_silver.printSchema()

## --------------------------
## 2️⃣ Brand-level KPIs
## --------------------------
brand_agg = (
    df_silver.groupBy("brand_norm")
    .agg(
        F.count("*").alias("total_products"),
        F.avg("selling_price_num").alias("avg_selling_price"),
        F.avg("actual_price_num").alias("avg_actual_price"),
        F.avg("average_rating_num").alias("avg_rating"),
        F.avg("discount_ratio").alias("avg_discount_ratio"),
        F.sum(F.when(F.col("is_discounted") == True, 1).otherwise(0)).alias("num_discounted_products")
    )
    .withColumn("etl_updated_ts", F.current_timestamp())
)

## --------------------------
## 3️⃣ Category-level KPIs
## --------------------------
category_agg = (
    df_silver.groupBy("category_norm")
    .agg(
        F.count("*").alias("total_products"),
        F.avg("selling_price_num").alias("avg_selling_price"),
        F.avg("average_rating_num").alias("avg_rating"),
        F.avg("discount_ratio").alias("avg_discount_ratio")
    )
    .withColumn("etl_updated_ts", F.current_timestamp())
)

## --------------------------
## 4️⃣ Optional: Brand x Category matrix
## --------------------------
brand_cat_agg = (
    df_silver.groupBy("brand_norm", "category_norm")
    .agg(
        F.count("*").alias("total_products"),
        F.avg("selling_price_num").alias("avg_selling_price"),
        F.avg("average_rating_num").alias("avg_rating"),
        F.avg("discount_ratio").alias("avg_discount_ratio")
    )
    .withColumn("etl_updated_ts", F.current_timestamp())
)

## --------------------------
## 5️⃣ Write Gold datasets to S3
## --------------------------
gold_base = f"s3://{processed_bucket}/gold/flipkart_fashion/"

(
    brand_agg.coalesce(1)
    .write.mode("overwrite")
    .parquet(gold_base + "brand_summary/")
)

(
    category_agg.coalesce(1)
    .write.mode("overwrite")
    .parquet(gold_base + "category_summary/")
)

(
    brand_cat_agg.coalesce(1)
    .write.mode("overwrite")
    .parquet(gold_base + "brand_category_summary/")
)

print(f"✅ Gold datasets written to {gold_base}")
job.commit()

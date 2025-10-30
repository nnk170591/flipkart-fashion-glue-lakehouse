import sys, boto3
from awsglue.utils import getResolvedOptions
from awsglue.context import GlueContext
from awsglue.job import Job
from pyspark.context import SparkContext
from pyspark.sql import functions as F

# ---- params ----
args = getResolvedOptions(sys.argv, ["JOB_NAME", "processed_bucket", "dq_results_bucket"])
PROC = args["processed_bucket"]
DQ_BUCKET = args["dq_results_bucket"]

# ---- glue init ----
sc = SparkContext()
glue = GlueContext(sc)
spark = glue.spark_session
job = Job(glue)
job.init(args["JOB_NAME"], args)

# ---- read bronze ----
bronze_path = f"s3://{PROC}/bronze/flipkart_fashion/"
df = spark.read.parquet(bronze_path)

# ---- checks (simple but effective) ----
checks = {
    "row_count_min_100": df.count() >= 100,  # adjust if you expect more
    "no_null_pid": df.filter("pid IS NULL").count() == 0,
    "positive_prices": df.filter("selling_price_num <= 0 OR actual_price_num <= 0").count() == 0,
    "rating_range_0_5": df.filter("(average_rating_num < 0) OR (average_rating_num > 5)").count() == 0
}

status = "PASS" if all(checks.values()) else "FAIL"

# ---- write a simple HTML summary to S3 for portfolio ----
html = f"""
<h2>Bronze DQ Report</h2>
<p>Status: <b style='color:{"green" if status=="PASS" else "red"}'>{status}</b></p>
<table border="1" cellpadding="6">
  <tr><th>Check</th><th>Result</th></tr>
  {''.join(f"<tr><td>{k}</td><td>{v}</td></tr>" for k,v in checks.items())}
</table>
"""
# easiest: write as a single-row text (you can download and rename to .html)
spark.createDataFrame([(html,)], "html string").coalesce(1)\
    .write.mode("overwrite").text(f"s3://{DQ_BUCKET}/dq/bronze_html_tmp/")
print(f"Bronze DQ HTML written under s3://{DQ_BUCKET}/dq/bronze_html_tmp/")

# ---- push a CloudWatch metric ----
cw = boto3.client("cloudwatch")
cw.put_metric_data(
    Namespace="Flipkart/GlueDQ",
    MetricData=[{
        "MetricName": "BronzeDQPass",
        "Unit": "Count",
        "Value": 1.0 if status == "PASS" else 0.0
    }]
)

# ---- fail job on critical checks ----
if status != "PASS":
    raise Exception("DQ FAILED: Bronze checks did not pass")

job.commit()

🛍️ Flipkart Fashion Data Lakehouse (AWS Glue + Athena)

A fully automated data lakehouse pipeline built on AWS using Glue, S3, and Athena, with IaC powered by AWS CDK and continuous deployment via GitHub Actions.

🚀 Architecture Overview

Layers (Medallion Architecture)

Layer	Storage	Description
🪶 Raw	S3 Bucket	Raw CSVs (uploaded from Kaggle dataset)
🥉 Bronze	S3 Parquet	Cleaned & normalized raw data
🥈 Silver	S3 Parquet	Enriched, standardized product data
🥇 Gold	S3 Parquet	Aggregated brand/category-level insights

AWS Components:

AWS Glue Jobs for ETL (Raw → Bronze → Silver → Gold)

AWS Glue Crawlers for schema discovery

AWS Glue Catalog for table registry

AWS Athena for ad-hoc SQL analysis

AWS CDK for infrastructure as code

GitHub Actions for CI/CD deployment

⚙️ How to Deploy in Your Own AWS Account
1️⃣ Prerequisites

AWS Account (with Admin or PowerUser permissions)

AWS CLI

AWS CDK v2

Python 3.9+ and pip installed

2️⃣ Clone the Repository
git clone https://github.com/nnk170591/flipkart-fashion-glue-lakehouse.git
cd flipkart-fashion-glue-lakehouse

3️⃣ Setup Environment
python -m venv .venv
source .venv/bin/activate  # (Linux/Mac)
.venv\Scripts\activate     # (Windows)
pip install -r requirements.txt

4️⃣ Bootstrap CDK (first time only)
cdk bootstrap

5️⃣ Deploy the Stack
cdk deploy


This will create:

3 S3 buckets (raw, processed, analytics)

3 Glue ETL jobs (Raw→Bronze→Silver→Gold)

3 Crawlers (Bronze, Silver, Gold)

Glue Database: flipkart_fashion_db

IAM role for Glue jobs

📊 Load Data & Run the Pipeline
1️⃣ Upload Dataset

Download from Kaggle:
👉 Flipkart Fashion Products Dataset

Then upload to your raw bucket:

aws s3 cp flipkart_fashion_data.csv s3://flipkart-fashion-raw-data/

2️⃣ Start Glue Workflow

Run the Glue workflow named:

flipkart_fashion_etl_workflow


This will execute all ETL jobs sequentially.

🔍 Query Data in Athena

In Athena, run:

USE flipkart_fashion_db;

SELECT brand, AVG(selling_price_num) AS avg_price
FROM flipkart_fashion_silver
GROUP BY brand
ORDER BY avg_price DESC
LIMIT 10;


Or:

SELECT category, COUNT(*) AS total_products
FROM flipkart_gold_brand_summary
GROUP BY category;

🧩 Project Highlights

✅ End-to-end AWS Glue pipeline (Raw → Bronze → Silver → Gold)
✅ Automated infrastructure via AWS CDK
✅ CI/CD using GitHub Actions + OIDC
✅ Athena SQL queries for analytics
✅ Modular design — can integrate with QuickSight or Redshift
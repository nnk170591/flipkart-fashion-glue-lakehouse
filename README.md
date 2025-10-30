# Flipkart Fashion Data Lakehouse  
_A Modern AWS Glue + Athena Pipeline (with CDK & GitHub Actions)_


---

##  Overview

This project builds an **end-to-end AWS data lakehouse** for Flipkart Fashion data using a **Medallion Architecture (Raw → Bronze → Silver → Gold)**.

It demonstrates modern **data engineering principles**, including:
- Serverless ETL pipelines with **AWS Glue**
- Schema discovery with **Glue Crawlers**
- Querying via **Amazon Athena**
- Infrastructure-as-Code with **AWS CDK (Python)**
- CI/CD automation using **GitHub Actions with OIDC**

---

##  Architecture Summary

| Layer | Storage | Format | Description |
|--------|----------|---------|--------------|
|  Raw | S3 | CSV | Original Kaggle dataset uploaded manually |
|  Bronze | S3 | Parquet | Cleaned & normalized raw data |
|  Silver | S3 | Parquet | Enriched, structured fashion product data |
|  Gold | S3 | Parquet | Aggregated metrics (brand/category-level summaries) |

**AWS Components**
- **S3** → Data lake zones  
- **Glue Jobs** → ETL for each layer  
- **Glue Catalog & Crawlers** → Table registration  
- **Athena** → Interactive querying  
- **CloudWatch** → Logs & metrics  
- **CDK** → Automated infrastructure provisioning  
- **GitHub Actions** → CI/CD pipeline with OIDC role assumption  

---

##  Getting Started (Your Own AWS Account)

### 1️⃣ Prerequisites
- AWS account with Admin or PowerUser permissions  
- [AWS CLI](https://docs.aws.amazon.com/cli/latest/userguide/getting-started-install.html) installed  
- [AWS CDK v2](https://docs.aws.amazon.com/cdk/v2/guide/cli.html) installed  
- Python 3.9+ and `pip`  

---

### 2️⃣ Clone the Repository
```bash
git clone https://github.com/nnk170591/flipkart-fashion-glue-lakehouse.git
cd flipkart-fashion-glue-lakehouse
```

---

### 3️⃣ Setup Environment
```bash
python -m venv .venv
source .venv/bin/activate  # Linux/Mac
.venv\Scripts\activate     # Windows
pip install -r requirements.txt
```

---

### 4️⃣ Bootstrap & Deploy CDK
```bash
cdk bootstrap
cdk deploy
```

This will create:
-  S3 buckets (`raw`, `processed`, `analytics`)
-  Glue ETL Jobs:  
  `flipkart_raw_to_bronze_job`, `flipkart_bronze_to_silver_job`, `flipkart_silver_to_gold_job`
-  Crawlers:  
  `flipkart_raw_crawler`, `flipkart_bronze_crawler`, `flipkart_silver_crawler`, `flipkart_gold_crawler`
-  Glue Database: `flipkart_fashion_db`
-  Workflow: `flipkart_fashion_etl_workflow`

---

##  Load Data & Run Pipeline

### 1️⃣ Upload Dataset
Download from Kaggle:  
 [Flipkart Fashion Products Dataset](https://www.kaggle.com/datasets/aaditshukla/flipkart-fasion-products-dataset)

Then upload it to the raw bucket:
```bash
aws s3 cp flipkart_fashion_data.csv s3://flipkart-fashion-raw-data/
```

---

### 2️⃣ Run the Glue Workflow
In AWS Console → **Glue → Workflows → `flipkart_fashion_etl_workflow`**  
Click **Run workflow**.  

This executes:
```
Raw → Bronze → Silver → Gold
```
Sequentially, via Glue Triggers and Jobs.

---

## 🔍 Query with Athena

### Connect Athena to the Glue Catalog:
1. Go to **Athena Console**  
2. Choose the database:
   ```sql
   USE flipkart_fashion_db;
   ```

### Example Queries
```sql
-- Top 10 brands by average price
SELECT brand, AVG(selling_price_num) AS avg_price
FROM flipkart_fashion_silver
GROUP BY brand
ORDER BY avg_price DESC
LIMIT 10;
```

```sql
-- Product distribution by category
SELECT category, COUNT(*) AS total_products
FROM flipkart_gold_brand_summary
GROUP BY category
ORDER BY total_products DESC;
```


##  Tech Stack

| Category | Tool | Purpose |
|-----------|------|----------|
| Infrastructure | AWS CDK (Python) | IaC for AWS components |
| Storage | Amazon S3 | Data lake zones |
| ETL | AWS Glue | Serverless transformations |
| Metadata | AWS Glue Catalog | Schema registry |
| Query | Amazon Athena | SQL-based analytics |
| Monitoring | CloudWatch | Logs and metrics |
| CI/CD | GitHub Actions | OIDC-based auto deployment |

---

##  Outputs

| Resource | Name |
|-----------|------|
| Glue Database | `flipkart_fashion_db` |
| Workflow | `flipkart_fashion_etl_workflow` |
| Bronze Table | `flipkart_fashion_bronze` |
| Silver Table | `flipkart_fashion_silver` |
| Gold Table | `flipkart_gold_brand_summary` |

---

##  Security & Cost Optimizations
- S3 Buckets encrypted with SSE-S3  
- Glue roles scoped with least privilege  
- Parquet + partitioning reduces Athena query cost  
- Lifecycle policies for temp data (optional)  

---

##  Future Enhancements
- Add Great Expectations data quality suite  
- Integrate with QuickSight for visualization  
- Add CI/CD smoke tests and environment promotion  
- Implement Lake Formation fine-grained permissions  

---

##  Portfolio Value

This project showcases:
- **End-to-end AWS Glue pipeline design**
- **Infrastructure-as-Code & automation**
- **Modern data engineering best practices**
- **Production-grade CI/CD setup**


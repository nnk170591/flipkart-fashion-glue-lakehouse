-- =====================================
-- Athena DDL: Flipkart Fashion Lakehouse
-- =====================================

-- Database
CREATE DATABASE IF NOT EXISTS flipkart_fashion_db;

-- RAW LAYER
CREATE EXTERNAL TABLE IF NOT EXISTS flipkart_fashion_db.flipkart_fashion_raw_data (
  pid STRING,
  title STRING,
  brand STRING,
  category STRING,
  sub_category STRING,
  actual_price STRING,
  selling_price STRING,
  description STRING,
  discount STRING,
  average_rating STRING,
  out_of_stock STRING,
  seller STRING,
  product_details STRING,
  crawled_at STRING,
  url STRING,
  images STRING
)
ROW FORMAT SERDE 'org.apache.hadoop.hive.serde2.lazy.LazySimpleSerDe'
STORED AS TEXTFILE
LOCATION 's3://flipkart-fashion-raw-data/'
TBLPROPERTIES ('skip.header.line.count'='1');

-- BRONZE LAYER
CREATE EXTERNAL TABLE IF NOT EXISTS flipkart_fashion_db.flipkart_fashion_bronze (
  pid STRING,
  title STRING,
  brand STRING,
  category STRING,
  sub_category STRING,
  actual_price_num DOUBLE,
  selling_price_num DOUBLE,
  average_rating_num DOUBLE,
  out_of_stock_bool BOOLEAN,
  ingestion_date STRING
)
STORED AS PARQUET
LOCATION 's3://flipkart-fashion-processed-data/bronze/flipkart_fashion/';

-- SILVER LAYER
CREATE EXTERNAL TABLE IF NOT EXISTS flipkart_fashion_db.flipkart_fashion_silver (
  pid STRING,
  title STRING,
  brand STRING,
  category STRING,
  sub_category STRING,
  actual_price_num DOUBLE,
  selling_price_num DOUBLE,
  discount DOUBLE,
  average_rating_num DOUBLE,
  out_of_stock_bool BOOLEAN,
  seller STRING,
  ingestion_date STRING
)
STORED AS PARQUET
LOCATION 's3://flipkart-fashion-processed-data/silver/flipkart_fashion/';

-- GOLD LAYER (Aggregated)
CREATE EXTERNAL TABLE IF NOT EXISTS flipkart_fashion_db.flipkart_gold_brand_summary (
  brand STRING,
  total_products INT,
  avg_discount DOUBLE,
  avg_rating DOUBLE,
  avg_price DOUBLE,
  last_ingestion STRING
)
STORED AS PARQUET
LOCATION 's3://flipkart-fashion-analytics-data/gold/brand_summary/';

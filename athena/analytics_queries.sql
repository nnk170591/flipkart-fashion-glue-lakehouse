-- =====================================
-- Athena Analytics: Flipkart Fashion
-- =====================================

-- 1️⃣ Top 10 brands by number of products
SELECT brand, COUNT(*) AS total_products
FROM flipkart_fashion_silver
WHERE brand IS NOT NULL
GROUP BY brand
ORDER BY total_products DESC
LIMIT 10;

-- 2️⃣ Average discount by category
SELECT category,
       ROUND(AVG(discount), 2) AS avg_discount,
       ROUND(AVG(selling_price_num), 2) AS avg_selling_price
FROM flipkart_fashion_silver
GROUP BY category
ORDER BY avg_discount DESC;

-- 3️⃣ Price vs Discount correlation (for QuickSight scatter plot)
SELECT category, brand,
       AVG(actual_price_num) AS avg_actual,
       AVG(selling_price_num) AS avg_selling,
       ROUND(AVG(discount), 2) AS avg_discount
FROM flipkart_fashion_silver
GROUP BY category, brand;

-- 4️⃣ Brand performance summary (from Gold table)
SELECT brand, total_products, avg_discount, avg_rating, avg_price
FROM flipkart_gold_brand_summary
ORDER BY avg_rating DESC
LIMIT 15;

-- 5️⃣ Out-of-stock rate per category
SELECT category,
       SUM(CASE WHEN out_of_stock_bool THEN 1 ELSE 0 END) * 100.0 / COUNT(*) AS out_of_stock_rate
FROM flipkart_fashion_silver
GROUP BY category
ORDER BY out_of_stock_rate DESC;

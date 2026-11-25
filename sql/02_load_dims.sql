-- 1. Populate dim_date from order timestamps in stg_orders
INSERT INTO dim_date (
    date_key,
    full_date,
    year,
    quarter,
    month,
    month_name,
    day_of_month,
    day_of_week,
    day_name,
    is_weekend
)
SELECT DISTINCT
    TO_CHAR(d::date, 'YYYYMMDD')::INT AS date_key,
    d::date AS full_date,
    EXTRACT(YEAR FROM d)::INT AS year,
    EXTRACT(QUARTER FROM d)::INT AS quarter,
    EXTRACT(MONTH FROM d)::INT AS month,
    TRIM(TO_CHAR(d, 'Month')) AS month_name,
    EXTRACT(DAY FROM d)::INT AS day_of_month,
    EXTRACT(ISODOW FROM d)::INT AS day_of_week,
    TRIM(TO_CHAR(d, 'Day')) AS day_name,
    EXTRACT(ISODOW FROM d)::INT IN (6, 7) AS is_weekend
FROM (
    SELECT order_purchase_timestamp::timestamp AS d
    FROM stg_orders
    WHERE order_purchase_timestamp IS NOT NULL
) dates
ON CONFLICT (date_key) DO NOTHING;

-- 2. Populate dim_customer
INSERT INTO dim_customer (
    customer_id,
    customer_unique_id,
    customer_zip_code_prefix,
    customer_city,
    customer_state
)
SELECT DISTINCT ON (customer_id)
    customer_id,
    customer_unique_id,
    customer_zip_code_prefix::VARCHAR(16),
    customer_city::VARCHAR(100),
    customer_state::VARCHAR(10)
FROM stg_customers
WHERE customer_id IS NOT NULL
ORDER BY customer_id
ON CONFLICT (customer_id) DO UPDATE SET
    customer_unique_id = EXCLUDED.customer_unique_id,
    customer_zip_code_prefix = EXCLUDED.customer_zip_code_prefix,
    customer_city = EXCLUDED.customer_city,
    customer_state = EXCLUDED.customer_state;

-- 3. Populate dim_product (with English category translation)
INSERT INTO dim_product (
    product_id,
    product_category_name,
    product_category_name_english,
    product_weight_g,
    product_length_cm,
    product_height_cm,
    product_width_cm
)
SELECT DISTINCT ON (p.product_id)
    p.product_id,
    p.product_category_name::VARCHAR(100),
    COALESCE(t.product_category_name_english, p.product_category_name)::VARCHAR(100) AS product_category_name_english,
    p.product_weight_g::NUMERIC(12, 2),
    p.product_length_cm::NUMERIC(12, 2),
    p.product_height_cm::NUMERIC(12, 2),
    p.product_width_cm::NUMERIC(12, 2)
FROM stg_products p
LEFT JOIN stg_product_category_translation t
    ON p.product_category_name = t.product_category_name
WHERE p.product_id IS NOT NULL
ORDER BY p.product_id
ON CONFLICT (product_id) DO UPDATE SET
    product_category_name = EXCLUDED.product_category_name,
    product_category_name_english = EXCLUDED.product_category_name_english,
    product_weight_g = EXCLUDED.product_weight_g,
    product_length_cm = EXCLUDED.product_length_cm,
    product_height_cm = EXCLUDED.product_height_cm,
    product_width_cm = EXCLUDED.product_width_cm;

-- 4. Populate dim_seller
INSERT INTO dim_seller (
    seller_id,
    seller_zip_code_prefix,
    seller_city,
    seller_state
)
SELECT DISTINCT ON (seller_id)
    seller_id,
    seller_zip_code_prefix::VARCHAR(16),
    seller_city::VARCHAR(100),
    seller_state::VARCHAR(10)
FROM stg_sellers
WHERE seller_id IS NOT NULL
ORDER BY seller_id
ON CONFLICT (seller_id) DO UPDATE SET
    seller_zip_code_prefix = EXCLUDED.seller_zip_code_prefix,
    seller_city = EXCLUDED.seller_city,
    seller_state = EXCLUDED.seller_state;

INSERT INTO fact_order_items (
    order_id,
    order_item_id,
    customer_key,
    product_key,
    seller_key,
    order_date_key,
    order_status,
    price,
    freight_value,
    order_purchase_timestamp,
    order_delivered_customer_date,
    order_estimated_delivery_date
)
SELECT
    oi.order_id,
    oi.order_item_id::INT,
    dc.customer_key,
    dp.product_key,
    ds.seller_key,
    TO_CHAR(o.order_purchase_timestamp::timestamp, 'YYYYMMDD')::INT AS order_date_key,
    o.order_status::VARCHAR(32),
    oi.price::NUMERIC(12, 2),
    oi.freight_value::NUMERIC(12, 2),
    o.order_purchase_timestamp::timestamp,
    o.order_delivered_customer_date::timestamp,
    o.order_estimated_delivery_date::timestamp
FROM stg_order_items oi
JOIN stg_orders o
    ON oi.order_id = o.order_id
JOIN dim_customer dc
    ON o.customer_id = dc.customer_id
JOIN dim_product dp
    ON oi.product_id = dp.product_id
JOIN dim_seller ds
    ON oi.seller_id = ds.seller_id
WHERE o.order_purchase_timestamp IS NOT NULL
ON CONFLICT (order_id, order_item_id) DO UPDATE SET
    customer_key = EXCLUDED.customer_key,
    product_key = EXCLUDED.product_key,
    seller_key = EXCLUDED.seller_key,
    order_date_key = EXCLUDED.order_date_key,
    order_status = EXCLUDED.order_status,
    price = EXCLUDED.price,
    freight_value = EXCLUDED.freight_value,
    order_purchase_timestamp = EXCLUDED.order_purchase_timestamp,
    order_delivered_customer_date = EXCLUDED.order_delivered_customer_date,
    order_estimated_delivery_date = EXCLUDED.order_estimated_delivery_date;

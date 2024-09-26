authDataBaseValidations = [
    {
        "source_table": "spree_users",
        "source_query": "select count(*) from (SELECT u.id AS user_id, u.encrypted_password AS password, u.password_salt, u.email, u.created_at, u.updated_at, CAST(CASE WHEN u.deleted_at IS NOT NULL THEN TRUE ELSE FALSE END AS BOOLEAN) AS is_deleted, CURRENT_TIMESTAMP AS password_updated_at, false AS is_email_verified, u.is_phone_verified AS mobile_verified, CASE WHEN sua.provider = 'google_oauth2' THEN 'google' ELSE sua.provider END AS login_type, sua.uid AS social_id, COALESCE(u.spree_api_key, '') AS spree_api_key, CASE WHEN u.blacklisted_at IS NOT NULL THEN TRUE ELSE false END AS blacklisted FROM spree_users u LEFT JOIN spree_user_authentications sua ON u.id = sua.user_id)tb",
        "dest_table": "user",
        "dest_query": "select count(*) from public.user"
    },
    {
        "source_table": "spree_user_clients",
        "source_query": """
                        SELECT COUNT(*) FROM (WITH cte AS (SELECT DISTINCT user_id, uuid AS device_id, platform AS device_type, created_at, updated_at, push_notification_token AS token, 'customer' AS user_type, row_number() OVER (PARTITION BY user_id ORDER BY user_id) AS rn FROM spree_user_clients ORDER BY user_id, uuid) SELECT user_id, device_id, device_type, created_at, updated_at, token, user_type FROM cte WHERE rn = 1) tb;
                        """,
        "dest_table": "device_token",
        "dest_query": "select count(*) from device_token"
    },
    {
        "source_table": "spree_users",
        "source_query": "select count(*) from (SELECT DISTINCT u.id AS id, u.id AS user, u.encrypted_password AS password, u.password_salt, u.email, u.created_at, u.updated_at, CAST(CASE WHEN u.deleted_at IS NOT NULL THEN TRUE ELSE FALSE END AS BOOLEAN) AS is_deleted, CURRENT_TIMESTAMP AS password_updated_at FROM spree_users u INNER JOIN spree_roles_users sru ON sru.user_id = u.id INNER JOIN spree_roles sr ON sr.id = sru.role_id AND sr.id <> 2 AND sr.name <> 'user')sb;",
        "dest_table": "employee",
        "dest_query": "select count(*) from employee"
    }
]

orderDataBaseValidations = [
    {
        "source_table": "spree_fulfilments",
        "source_query": "SELECT count(*) FROM (WITH RankedResults AS (SELECT cancel_reason, created_at, updated_at, ROW_NUMBER() OVER (PARTITION BY cancel_reason ORDER BY created_at DESC) AS rn FROM spree_fulfilments WHERE cancel_reason IS NOT NULL) SELECT ROW_NUMBER() OVER () AS id, cancel_reason AS reason_en, '' AS reason_ar, true AS visible, created_at, updated_at FROM RankedResults WHERE rn = 1 ORDER BY id ASC) tb;",
        "dest_table": "order_cancellation_reason",
        "dest_query": "SELECT COUNT(*) FROM order_cancellation_reason"
    },
    {
        "source_table": "spree_orders",
        "source_query": "select count(*) from spree_orders where state != 'cart'",
        "dest_table": "order",
        "dest_query": "SELECT COUNT(*) FROM public.order;"
    },
    {
        "source_table": "spree_line_items",
        "source_query": "SELECT count(*) FROM (SELECT sli.id, sli.variant_id AS product_variant_id, coalesce(CASE WHEN sv.weight_increment > 0 AND sv.default_weight_count > 0 AND sv.max_weight_per_order > 0 THEN CASE WHEN sli.requested_quantity < sv.weight_increment AND sli.requested_quantity > 0 THEN sv.weight_increment / sli.requested_quantity ELSE sli.requested_quantity / sv.weight_increment END ELSE sli.requested_quantity END, 0) AS quantity, CASE WHEN sv.weight_increment > 0 AND sv.default_weight_count > 0 AND sv.max_weight_per_order > 0 THEN sli.quantity ELSE NULL END AS picked_weight, COALESCE(CASE WHEN sv.weight_increment > 0 AND sv.default_weight_count > 0 AND sv.max_weight_per_order > 0 THEN 1 ELSE sli.quantity END, 0) AS picked_quantity, sli.price, sli.created_at, sli.replaced, so.state, COALESCE(sli.updated_at, CURRENT_TIMESTAMP) AS updated_at, CASE WHEN sli.on_sale = false THEN sli.price ELSE '0.0' END AS action_price, CASE WHEN sli.on_sale = true THEN sli.price ELSE '0' END AS sale_price, 0 AS picker_id, sv.product_id, sli.order_id AS order_shipment_id, CASE WHEN so.replace_product::varchar = 'true' THEN 'replace-with-similar-product' WHEN so.replace_product::varchar = 'false' THEN 'cancel' ELSE NULL END AS replacement_pref, 1 AS category_id, '' AS status FROM spree_line_items sli LEFT JOIN spree_variants sv ON sv.id = sli.variant_id LEFT JOIN spree_orders so ON so.id = sli.order_id WHERE so.state != 'cart' ORDER BY sli.id DESC) tb;",
        "dest_table": "order_product",
        "dest_query": "SELECT COUNT(*) FROM order_product;"
    },
    {
        "source_table": "spree_payment_methods",
        "source_query": "SELECT count(*) FROM (SELECT ROW_NUMBER() OVER () AS id, sp.order_id, sp.response_code AS transaction_id, sp.amount, COALESCE(so.currency, '') AS currency, sp.state AS status, sp.payment_method_id AS payment_option_id, sp.source_id, ss.id AS shipment_id, SUBSTRING(sp.source_type, 8) AS source_type FROM spree_payments sp LEFT JOIN spree_orders so ON so.id = sp.order_id LEFT JOIN spree_shipments ss ON ss.order_id = so.id) tb;",
        "dest_table": "order_payment",
        "dest_query": "SELECT COUNT(*) FROM order_payment;"
    },
    {
        "source_table": "spree_shipments",
        "source_query": "SELECT count(*) FROM (WITH cte AS (SELECT so.id AS id, so.id AS order_id, CASE WHEN so.state = 'delivery' THEN 'delivered' WHEN so.state = 'picking_and_staging_in_progress' THEN 'pending' WHEN so.state = 'payment' THEN 'pending' WHEN so.state = 'complete' THEN 'completed' WHEN so.state = 'confirm' THEN 'pending' WHEN so.state = 'canceled' THEN 'customer_cancelled' END AS order_status, so.created_at, so.updated_at, CAST((so.total * (so.vat_percentage / 100)) AS DOUBLE PRECISION) AS tax_total, so.total, CAST(dsto.start_time AS text) AS start_time, CAST(dsto.end_time AS text) AS end_time, CASE WHEN dtss.day_of_week = 0 THEN 'sunday' WHEN dtss.day_of_week = 1 THEN 'monday' WHEN dtss.day_of_week = 2 THEN 'tuesday' WHEN dtss.day_of_week = 3 THEN 'wednesday' WHEN dtss.day_of_week = 4 THEN 'thursday' WHEN dtss.day_of_week = 5 THEN 'friday' WHEN dtss.day_of_week = 6 THEN 'saturday' ELSE 'sunday' END AS day_of_week, dtss.spree_shipping_method_id AS delivery_option_id, so.order_type, so.supermarket_id, sla.delivery_date, sa.amount AS delivery_charges, FALSE AS is_delivery_on_hold, so.created_at AS processing_start_at, ROW_NUMBER() OVER (PARTITION BY so.id ORDER BY so.id) AS row_num FROM spree_orders so LEFT JOIN danube_slot_to_orders dsto ON dsto.order_id = so.id LEFT JOIN danube_time_slots_schedules dtss ON dtss.id = dsto.time_slots_schedule_id LEFT JOIN spree_lift_assignments sla ON sla.order_id = so.id LEFT JOIN spree_adjustments sa ON sa.order_id = so.id AND sa.label = 'Express Fee' WHERE so.state != 'cart') SELECT * FROM cte WHERE row_num = 1) tb;",
        "dest_table": "order_shipment",
        "dest_query": "SELECT COUNT(*) FROM order_shipment;"
    },
    {
        "source_table": "spree_orders/spree_addresses",
        "source_query": "SELECT count(*) FROM (SELECT so.id AS order_id, so.bill_address_id AS address_id, 'true' AS is_bill_address, COALESCE(sa.city, '') AS city, COALESCE(con.name, '') AS country, sdtrans.name AS district, 'other' AS type, CONCAT(sa.address1, ' ', sa.address2) AS formatted_address, COALESCE(sa.latitude, '0.0') AS latitude, COALESCE(sa.longitude, '0.0') AS longitude, CASE WHEN sa.zipcode ~ '^[0-9]+$' THEN CAST(sa.zipcode AS INT) ELSE NULL END AS postal_code, so.special_instructions AS delivery_instruction, so.created_at, so.updated_at FROM spree_orders so LEFT JOIN spree_addresses sa ON sa.id = so.bill_address_id LEFT JOIN spree_countries con ON con.id = sa.country_id LEFT JOIN spree_districts dist ON dist.id = sa.district_id LEFT JOIN spree_district_translations sdtrans ON sdtrans.spree_district_id = dist.id AND sdtrans.locale = 'en' WHERE so.state != 'cart' UNION ALL SELECT so.id AS order_id, so.ship_address_id AS address_id, 'false' AS is_bill_address, COALESCE(sa.city, '') AS city, COALESCE(con.name, '') AS country, sdtrans.name AS district, 'other' AS type, CONCAT(sa.address1, ' ', sa.address2) AS formatted_address, COALESCE(sa.latitude, '0.0') AS latitude, COALESCE(sa.longitude, '0.0') AS longitude, CASE WHEN sa.zipcode ~ '^[0-9]+$' THEN CAST(sa.zipcode AS INT) ELSE NULL END AS postal_code, so.special_instructions AS delivery_instruction, so.created_at, so.updated_at FROM spree_orders so LEFT JOIN spree_addresses sa ON sa.id = so.ship_address_id LEFT JOIN spree_countries con ON con.id = sa.country_id LEFT JOIN spree_districts dist ON dist.id = sa.district_id LEFT JOIN spree_district_translations sdtrans ON sdtrans.spree_district_id = dist.id AND sdtrans.locale = 'en' WHERE so.state != 'cart') tb;",
        "dest_table": "order_address",
        "dest_query": "SELECT COUNT(*) FROM order_address;"
    },
    {
        "source_table": "spree_cashbacks",
        "source_query": "select count(*) from spree_cashbacks;",
        "dest_table": "cashbacks",
        "dest_query": "SELECT COUNT(*) FROM cashback;"
    },
    {
        "source_table": "spree_adjustments",
        "source_query": "select count(*) from spree_adjustments",
        "dest_table": "order_adjustment",
        "dest_query": "SELECT COUNT(*) FROM order_adjustment;"
    },
    {
        "source_table": "spree_invoice_logs",
        "source_query": "select count(*) from spree_invoice_logs",
        "dest_table": "order_invoice_logs",
        "dest_query": "SELECT COUNT(*) FROM order_invoice_logs;"
    },
    {
        "source_table": "spree_invoices",
        "source_query": "select count(*) from spree_invoices",
        "dest_table": "order_invoices",
        "dest_query": "SELECT COUNT(*) FROM order_invoices;"
    },
    {
        "source_table": "spree_refunds",
        "source_query": "SELECT count(*) FROM (SELECT sr.id, sp.order_id, CASE WHEN sr.transaction_id IS NOT NULL THEN sr.transaction_id ELSE sp.response_code END AS transaction_id, sr.created_at, sr.updated_at, sr.amount, CASE WHEN sr.status = 'uncertain' THEN 'pending' WHEN sr.status = 'failed' THEN 'failed' WHEN sr.status = 'success' THEN 'approved' ELSE '' END AS status, 'SAR' AS currency, '' AS type FROM spree_refunds sr INNER JOIN spree_payments sp ON sp.id = sr.payment_id WHERE sr.payment_id IS NOT NULL) tb;",
        "dest_table": "order_payment_refund",
        "dest_query": "SELECT COUNT(*) FROM order_payment_refund;"
    },
    {
        "source_table": "spree_orders_promotions",
        "source_query": "select count(*) from spree_orders_promotions;",
        "dest_table": "order_promotions",
        "dest_query": "SELECT COUNT(*) FROM order_promotions;"
    },
    {
        "source_table": "spree_store_credits",
        "source_query": "select count(*) from spree_store_credits;",
        "dest_table": "store_credit",
        "dest_query": "SELECT COUNT(*) FROM store_credit;"
    },
    {
        "source_table": "spree_store_credit_categories",
        "source_query": "select count(*) from spree_store_credit_categories;",
        "dest_table": "store_credit_category",
        "dest_query": "SELECT COUNT(*) FROM store_credit_category;"
    },
    {
        "source_table": "spree_store_credit_events",
        "source_query": "select count(*) from spree_store_credit_events;",
        "dest_table": "store_credit_transaction",
        "dest_query": "SELECT COUNT(*) FROM store_credit_transaction;"
    },
    {
        "source_table": "spree_store_credit_types",
        "source_query": "select count(*) from spree_store_credit_types;",
        "dest_table": "store_credit_type",
        "dest_query": "SELECT COUNT(*) FROM store_credit_type;"
    },
    {
        "source_table": "spree_store_credit_update_reasons",
        "source_query": "select count(*) from spree_store_credit_update_reasons;",
        "dest_table": "store_credit_update_reason",
        "dest_query": "SELECT COUNT(*) FROM store_credit_update_reason;"
    },
    {
        "source_table": "spree_user_gift_cards",
        "source_query": "select count(*) from spree_user_gift_cards;",
        "dest_table": "user_gift_cards",
        "dest_query": "SELECT COUNT(*) FROM user_gift_cards;"
    }
]

userDataBaseValidations = [
    {
        "source_table": "spree_addresses",
        "source_query": "SELECT COUNT(*) FROM (SELECT DISTINCT LOWER(sst.name) AS name, ss.country_id, ss.created_at, ss.updated_at, TRUE AS is_visible, ds.state_id FROM danube_supermarkets ds JOIN spree_states ss ON ss.id = ds.state_id JOIN spree_state_translations sst ON sst.spree_state_id = ss.id AND sst.locale = 'en') tb;",
        "dest_table": "city",
        "dest_query": "select count(*) from city"
    },
    {
        "source_table": "spree_payment_methods",
        "source_query": "SELECT COUNT(*) FROM (SELECT spm.id, spmt.name, spm.created_at, spm.updated_at, spm.deleted_at, CASE WHEN type = 'Spree::PaymentMethod::StoreCredit' THEN 'e-wlt' WHEN type = 'Spree::Gateway::PayFort' THEN 'credit' WHEN type = 'Spree::Gateway::CheckoutCom' THEN 'credit' WHEN type = 'Spree::Gateway::Tamara' THEN 'tamara' WHEN type = 'Spree::Gateway::BogusSimple' THEN 'bogus-simple' WHEN type = 'Spree::PaymentMethod::Check' THEN 'cod' WHEN type = 'Spree::Gateway::CheckoutCom::ApplePay' THEN 'a-pay' WHEN type = 'Spree::Gateway::LoyaltyPoint' THEN 'loy-pts' WHEN type = 'Spree::Gateway::PayFort::ApplePay' THEN 'a-pay' ELSE '' END AS code FROM spree_payment_methods spm JOIN spree_payment_method_translations spmt ON spmt.spree_payment_method_id = spm.id AND locale = 'en' ORDER BY id ASC) tb;",
        "dest_table": "payment_option",
        "dest_query": "select count(*) from payment_option"
    },
    {
        "source_table": "danube_time_slot_schedules",
        "source_query": "SELECT COUNT(*) FROM (SELECT spree_shipping_method_id AS delivery_option_id, CASE WHEN dtss.day_of_week = 0 THEN 'sunday' WHEN dtss.day_of_week = 1 THEN 'monday' WHEN dtss.day_of_week = 2 THEN 'tuesday' WHEN dtss.day_of_week = 3 THEN 'wednesday' WHEN dtss.day_of_week = 4 THEN 'thursday' WHEN dtss.day_of_week = 5 THEN 'friday' WHEN dtss.day_of_week = 6 THEN 'saturday' ELSE '' END AS day_of_week, CAST(dts.start_time AS text), CAST(dts.end_time AS text), dts.enabled, 1 AS country_id FROM danube_time_slots_schedules dtss LEFT JOIN danube_time_slots dts ON dtss.time_slot_id = dts.id WHERE dts.enabled GROUP BY dtss.time_slot_id, dtss.spree_shipping_method_id, dtss.day_of_week, dts.start_time, dts.end_time, dts.enabled) tb;",
        "dest_table": "time_slot",
        "dest_query": "select count(*) from time_slot"
    },
{
        "source_table": "spree_shipping_methods",
        "source_query": "SELECT COUNT(*) FROM (SELECT ssm.id, ssmt.name, ssm.created_at, ssm.updated_at, ssm.deleted_at FROM spree_shipping_methods ssm LEFT JOIN spree_shipping_method_translations ssmt ON ssm.id = ssmt.spree_shipping_method_id AND locale = 'en') tb;",
        "dest_table": "delivery_option",
        "dest_query": "select count(*) from delivery_option"
    },
{
        "source_table": "spree_countries",
        "source_query": "select count(*) from spree_countries",
        "dest_table": "country",
        "dest_query": "select count(*) from country"
    },
    {
        "source_table": "spree_users",
        "source_query": "SELECT COUNT(*) FROM (WITH cte AS (SELECT u.id, CASE WHEN u.deleted_at IS NOT NULL THEN TRUE ELSE FALSE END AS is_deleted, u.created_at, u.updated_at, LEFT(COALESCE(u.first_name, ''), 40) AS first_name, LEFT(COALESCE(u.last_name, ''), 40) AS last_name, u.email, 'others' AS gender, COALESCE(CONCAT('+', u.mobile_number_country_code), '') AS country_code, LEFT(COALESCE(CASE WHEN u.mobile_phone_number LIKE CONCAT('+', u.mobile_number_country_code, '%') THEN SUBSTRING(u.mobile_phone_number, CHAR_LENGTH(u.mobile_number_country_code) + 2) WHEN u.mobile_phone_number LIKE CONCAT(u.mobile_number_country_code, '%') THEN SUBSTRING(u.mobile_phone_number, CHAR_LENGTH(u.mobile_number_country_code) + 1) ELSE COALESCE(u.mobile_phone_number, '') END, ''), 16) AS mobile_number, CAST(u.dob AS TEXT) AS dob, COALESCE(u.referral_code, '') AS referral_code, CASE WHEN u.locale = 'en' THEN 1 ELSE 2 END AS language_id, a.city, a.latitude, a.longitude, CASE WHEN a.country_id = '0' THEN '1' ELSE a.country_id END AS country_id, TRUE AS receive_marketing_promotions, CASE WHEN sua.provider = 'google_oauth2' THEN 'google' ELSE sua.provider END AS login_type, sua.uid AS social_id, 0 AS balance, u.blacklisted_at, u.blacklisted_reason, ROW_NUMBER() OVER (PARTITION BY u.id ORDER BY sua.updated_at DESC) AS rn FROM spree_users u LEFT JOIN spree_user_addresses ua ON u.id = ua.user_id AND ua.default = TRUE LEFT JOIN spree_addresses a ON ua.address_id = a.id LEFT JOIN spree_user_authentications sua ON u.id = sua.user_id ORDER BY u.id ASC) SELECT id, is_deleted, created_at, updated_at, first_name, last_name, email, gender, country_code, mobile_number, dob, referral_code, language_id, city, latitude, longitude, country_id, receive_marketing_promotions, login_type, social_id, balance, blacklisted_at, blacklisted_reason FROM cte WHERE rn = 1) tb;",
        "dest_table": "user",
        "dest_query": "select count(*) from public.user"
    },
    {
        "source_table": "spree_user_addresses",
        "source_query": "SELECT COUNT(*) FROM (SELECT DISTINCT sua.id, CASE WHEN sa.address1 IS NOT NULL AND sa.address2 IS NOT NULL THEN CONCAT(sa.address1, ' ', sa.address2, ', ') WHEN sa.address1 IS NOT NULL THEN CONCAT(sa.address1, ' ') WHEN sa.address2 IS NOT NULL THEN CONCAT(sa.address2, ', ') ELSE '' END AS formatted_address, COALESCE(COALESCE(sst_en.name, sst_ar.name), '') AS city, COALESCE(scon.name, 'Saudi Arabia') AS country, COALESCE(NULLIF(regexp_replace(sa.zipcode, '[^0-9]', '', 'g'), '')::BIGINT, NULL) AS postal_code, sua.created_at, sua.updated_at, COALESCE(sdt_en.name, sdt_ar.name) AS district, COALESCE(sa.latitude, 0) AS latitude, COALESCE(sa.longitude, 0) AS longitude, COALESCE(sua.default, 'false') AS is_default, sua.user_id AS user_id, 'other' AS type, COALESCE(CASE WHEN sa.driver_meta_data IS NOT NULL THEN sa.driver_meta_data->>'verified' ELSE 'false' END, 'false') AS is_verified, '' AS title, sa.driver_meta_data->>'notes' AS comments FROM spree_user_addresses sua LEFT JOIN spree_addresses sa ON sua.address_id = sa.id LEFT JOIN spree_countries scon ON sa.country_id = scon.id LEFT JOIN spree_districts sdist ON sdist.id = sa.district_id LEFT JOIN spree_district_translations sdt_en ON sdt_en.spree_district_id = sdist.id AND sdt_en.locale = 'en' LEFT JOIN spree_district_translations sdt_ar ON sdt_ar.spree_district_id = sdist.id AND sdt_ar.locale = 'ar' LEFT JOIN spree_state_translations sst_en ON sst_en.id = sa.state_id AND sst_en.locale = 'en' LEFT JOIN spree_state_translations sst_ar ON sst_ar.id = sa.state_id AND sst_ar.locale = 'ar' WHERE (sa.id IS NOT NULL AND city IS NOT NULL) ORDER BY sua.id DESC)tb;",
        "dest_table": "address",
        "dest_query": "select count(*) from address"
    },
    {
        "source_table": "spree_credit_cards",
        "source_query": "SELECT COUNT(*) FROM (SELECT a.id, a.user_id, COALESCE(a.name, '') AS name_on_card, COALESCE(a.cc_type, '') AS scheme, CASE WHEN a.cc_type = 'MADA' THEN 'mada' ELSE '' END AS scheme_local, COALESCE(a.gateway_payment_profile_id, '') AS instrument_id, a.last_digits, a.month, a.year, a.updated_at, a.created_at, 'CREDIT' AS card_type FROM spree_credit_cards a WHERE user_id IS NOT NULL AND gateway_customer_profile_id IS NOT NULL ORDER BY id ASC) tb;",
        "dest_table": "checkout_cards",
        "dest_query": "select count(*) from checkout_cards"
    },
    {
        "source_table": "danube_supermarkets",
        "source_query": "select count(*) from danube_supermarkets;",
        "dest_table": "super_market",
        "dest_query": "select count(*) from super_market"
    },
    {
        "source_table": "danube_supermarkets",
        "source_query": "SELECT COUNT(*) FROM (SELECT id AS super_market_id, payment_id, delivery_option_id FROM (SELECT id, UNNEST(REGEXP_MATCHES(REPLACE(REGEXP_REPLACE(REGEXP_REPLACE(REGEXP_REPLACE(payment_options::text, '^.*home_delivery:(.*)$', '\1'), 'store_pick_up:.*$', ''), '\n', ''), '''(\d+)''', '\1'), '(\d+)', 'g'))::INTEGER AS payment_id, '1' AS delivery_option_id FROM danube_supermarkets WHERE payment_options::text LIKE '%home_delivery%' UNION ALL SELECT id AS super_market_id, UNNEST(REGEXP_MATCHES(REPLACE(REGEXP_REPLACE(REGEXP_REPLACE(REGEXP_REPLACE(payment_options::text, '^.*store_pick_up:(.*)$', '\1'), 'home_delivery:.*$', ''), '\n', ''), '''(\d+)''', '\1'), '(\d+)', 'g'))::INTEGER AS payment_id, '2' AS delivery_option_id FROM danube_supermarkets WHERE payment_options::text LIKE '%store_pick_up%') AS subquery_alias ORDER BY super_market_id) tb;",
        "dest_table": "super_market_payment",
        "dest_query": "select count(*) from super_market_payment"
    },
    {
        "source_table": "danube_supermarkets",
        "source_query": "select count(*) from (select * from (SELECT id AS supermarket_id, 1 AS delivery_type_id FROM danube_supermarkets WHERE supermarket_type IN ('regular', 'regular_and_express') UNION SELECT id AS supermarket_id, 2 AS delivery_type_id FROM danube_supermarkets WHERE supermarket_type IN ('express', 'regular_and_express')) as ds order by supermarket_id asc)tb",
        "dest_table": "supermarket_delivery_type",
        "dest_query": "select count(*) from supermarket_delivery_type"
    },
{
        "source_table": "NA",
        "source_query": "select 2",
        "dest_table": "delivery_type",
        "dest_query": "select count(*) from delivery_type"
    },
    {
        "source_table": "danube_supermarkets",
        "source_query": "SELECT count(*) FROM (SELECT id AS supermarket_id, 2 AS delivery_option_id FROM danube_supermarkets WHERE payment_options::text LIKE '%store_pick_up%' UNION SELECT id, 1 AS delivery_option_id FROM danube_supermarkets WHERE payment_options::text LIKE '%home_delivery%') ts;",
        "dest_table": "supermarket_delivery_option",
        "dest_query": "select count(*) from supermarket_delivery_option"
    },
    {
        "source_table": "spree_feedback_reviews",
        "source_query": "select count(*) from spree_feedback_reviews",
        "dest_table": "feedback",
        "dest_query": "select count(*) from feedback"
    },
    {
        "source_table": "spree_loyalty_members",
        "source_query": "select count(*) from spree_loyalty_members",
        "dest_table": "loyalty_member",
        "dest_query": "select count(*) from loyalty_member"
    },
    {
        "source_table": "spree_users",
        "source_query": "SELECT COUNT(*) FROM (SELECT * FROM (SELECT u.id, sru.role_id, u.email, u.created_at, u.updated_at, CASE WHEN u.deleted_at IS NOT NULL THEN TRUE ELSE FALSE END AS is_deleted, LEFT(COALESCE(u.first_name, ''), 40) AS first_name, LEFT(COALESCE(u.last_name, ''), 40) AS last_name, LEFT(COALESCE(CASE WHEN u.mobile_phone_number LIKE CONCAT('+', u.mobile_number_country_code, '%') THEN SUBSTRING(u.mobile_phone_number, CHAR_LENGTH(u.mobile_number_country_code) + 2) WHEN u.mobile_phone_number LIKE CONCAT(u.mobile_number_country_code, '%') THEN SUBSTRING(u.mobile_phone_number, CHAR_LENGTH(u.mobile_number_country_code) + 1) ELSE COALESCE(u.mobile_phone_number, '') END, ''), 16) AS mobile_number, u.dob, COALESCE(CONCAT('+', u.mobile_number_country_code), '') AS country_code, CASE WHEN sa.country_id = '0' THEN '1' ELSE sa.country_id END AS country_id, 'others' AS gender, 'admin' AS user_type, 'available' AS availability, sr.name AS role_name, CASE WHEN u.deleted_at IS NOT NULL THEN FALSE ELSE TRUE END AS active, CASE WHEN u.deleted_at IS NOT NULL THEN FALSE ELSE TRUE END AS status, sa.city, ROW_NUMBER() OVER (PARTITION BY u.id ORDER BY sr.name) AS rn FROM spree_users u INNER JOIN spree_roles_users sru ON sru.user_id = u.id INNER JOIN spree_roles sr ON sr.id = sru.role_id AND sr.name <> 'user' LEFT JOIN spree_user_addresses sua ON sua.user_id = u.id AND sua.default = TRUE LEFT JOIN spree_addresses sa ON sua.address_id = sa.id) AS subquery WHERE rn = 1) AS tb;",
        "dest_table": "employee",
        "dest_query": "select count(*) from employee"
    },
    {
        "source_table":"danube_time_slots_schedules",
        "source_query":"SELECT COUNT(*) FROM (SELECT dtss.id, CAST(dts.start_time AS text) AS start_time, CAST(dts.end_time AS text) AS end_time, CASE WHEN dtss.day_of_week = 0 THEN 'sunday' WHEN dtss.day_of_week = 1 THEN 'monday' WHEN dtss.day_of_week = 2 THEN 'tuesday' WHEN dtss.day_of_week = 3 THEN 'wednesday' WHEN dtss.day_of_week = 4 THEN 'thursday' WHEN dtss.day_of_week = 5 THEN 'friday' WHEN dtss.day_of_week = 6 THEN 'saturday' ELSE 'sunday' END AS day_of_week, dtss.spree_shipping_method_id AS delivery_option_id, COALESCE(ds.id, 0) AS supermarket_id, COALESCE(dtss.delivery_capacity, 0) AS capacity, NULL AS time_slot_id, dtss.enabled AS is_enabled, dtss.created_at, dtss.updated_at FROM danube_time_slots_schedules dtss LEFT JOIN danube_time_slots dts ON dts.id = dtss.time_slot_id LEFT JOIN danube_supermarkets ds ON ds.zone_id = dtss.zone_id ORDER BY dts.id) tb;",
        "dest_table":"delivery_capacity",
        "dest_query":"select count(*) from delivery_capacity"
    }
]

productDataBaseValidations = [
    {
        "source_table": "spree_bin_categories",
        "source_query": "select count(*) from spree_bin_categories",
        "dest_table": "bin_category",
        "dest_query": "select count(*) from bin_category"
    },
    {
        "source_table": "spree_kitchen_recipes",
        "source_query": "select count(*) from spree_kitchen_recipes",
        "dest_table": "recipe",
        "dest_query": "select count(*) from recipe  "
    },
    {
        "source_table": "spree_custom_products",
            "source_query": "SELECT count(*) FROM (SELECT id AS offline_product_id, CASE WHEN (barcode_element ~ E'^\\d+$') THEN CAST(barcode_element AS BIGINT) ELSE -1 END AS barcode, 1 AS order FROM spree_custom_products CROSS JOIN LATERAL unnest(barcodes) AS barcode_element ORDER BY id DESC) tb;",
        "dest_table": "offline_product_barcode",
        "dest_query": "select count(*) from offline_product_barcode"
    },
{
        "source_table": "spree_product_inventory_modifiers",
        "source_query": "select count(*) from spree_product_inventory_modifiers",
        "dest_table": "inventory_modifiers",
        "dest_query": "select count(*) from inventory_modifiers"
    },
{
        "source_table": "spree_custom_products",
        "source_query": "select count(*) from spree_custom_products",
        "dest_table": "offline_product",
        "dest_query": "select count(*) from offline_product"
    },
    {
        "source_table": "spree_bundle_products",
        "source_query": "select count(*) from spree_bundle_products",
        "dest_table": "bundle_products",
        "dest_query": "select count(*) from bundle_products"
    },
    {
        "source_table": "spree_kitchen_cuisines",
        "source_query": "select count(*) from spree_kitchen_cuisines",
        "dest_table": "cuisine",
        "dest_query": "select count(*) from cuisine"
    },
    {
        "source_table": "spree_kitchen_ingredients",
        "source_query": "select count(*) from spree_kitchen_ingredients",
        "dest_table": "ingredient",
        "dest_query": "select count(*) from ingredient"
    },
    {
        "source_table": "spree_ingredient_products",
        "source_query": "select count(*) from spree_ingredient_products",
        "dest_table": "ingredient_product",
        "dest_query": "select count(*) from ingredient_product"
    },
    {
        "source_table": "spree_nutritional_facts",
        "source_query": "select count(*) from spree_nutritional_facts",
        "dest_table": "nutritional_facts",
        "dest_query": "select count(*) from nutritional_facts"
    },
    {
        "source_table": "spree_option_types",
        "source_query": "select count(*) from spree_option_types",
        "dest_table": "option_type",
        "dest_query": "select count(*) from option_type"
    },
    {
        "source_table": "spree_option_values",
        "source_query": "select count(*) from spree_option_values",
        "dest_table": "option_value",
        "dest_query": "select count(*) from option_value"
    },
    {
        "source_table": "spree_products",
        "source_query": "select count(*) from spree_products",
        "dest_table": "product",
        "dest_query": "select count(*) from product"
    },
    {
        "source_table": "spree_product_barcodes",
        "source_query": "select count(*) from spree_product_barcodes",
        "dest_table": "product_barcode",
        "dest_query": "select count(*) from product_barcode"
    },
    {
        "source_table": "spree_assets",
        "source_query": "Select Count(*) from spree_assets where viewable_type='Spree::Variant'",
        "dest_table": "product_image",
        "dest_query": "SELECT Count(*) FROM product_image"
    },
    {
        "source_table":"spree_products_taxons",
        "source_query":"select count(*) from(SELECT distinct product_id,taxon_id FROM spree_products_taxons)tb",
        "dest_table":"product_taxon",
        "dest_query":"select count(*) from product_taxon"
    },
    {
        "source_table":"spree_promotions",
        "source_query":"SELECT count(*) FROM (WITH Cte AS (SELECT DISTINCT sp.id, COALESCE(MAX(CASE WHEN spt.locale = 'en' THEN spt.name END), '') AS name_en, MAX(CASE WHEN spt.locale = 'en' THEN spt.description END) AS description_en, COALESCE(MAX(CASE WHEN spt.locale = 'ar' THEN spt.name END), '') AS name_ar, MAX(CASE WHEN spt.locale = 'ar' THEN spt.description END) AS description_ar, UPPER(REGEXP_REPLACE(TRANSLATE(MAX(CASE WHEN spt.locale = 'en' THEN spt.name END), ' ', '_'), '[^a-zA-Z0-9_]', '', 'g')) AS code, sp.expires_at, sp.starts_at, COALESCE(sp.usage_limit, 0) AS usage_limit, sp.match_policy, sp.created_at, sp.updated_at, sp.per_code_usage_limit, sp.apply_automatically, sp.deleted_at, TRUE AS is_visible FROM spree_promotions AS sp LEFT JOIN spree_promotion_translations AS spt ON spt.spree_promotion_id = sp.id WHERE spt.name IS NOT NULL GROUP BY sp.id ORDER BY sp.id ASC) SELECT id, name_en, description_en, name_ar, description_ar, code, expires_at, starts_at, usage_limit, match_policy, created_at, updated_at, per_code_usage_limit, apply_automatically, deleted_at, is_visible FROM (SELECT id, name_en, description_en, name_ar, description_ar, code, expires_at, starts_at, usage_limit, match_policy, created_at, updated_at, per_code_usage_limit, apply_automatically, deleted_at, is_visible, ROW_NUMBER() OVER (PARTITION BY name_en ORDER BY id) AS rn FROM Cte) AS temp WHERE rn = 1 ORDER BY name_en) tb;",
        "dest_table":"promotion",
        "dest_query":"select count(*) from promotion"
    },
    {
        "source_table":"spree_product_price_versions",
        "source_query":"select count(*) from spree_product_price_versions",
        "dest_table":"product_price_versions",
        "dest_query":"select count(*) from product_price_versions"
    },
    {
        "source_table":"spree_taxons",
        "source_query":"select count(*) from spree_taxons",
        "dest_table":"taxon",
        "dest_query":"select count(*) from taxon"
    },
    {
        "source_table":"spree_tenants_taxons",
        "source_query":"select count(*) from spree_tenants_taxons;",
        "dest_table":"taxon_country",
        "dest_query":"select count(*) from taxon_country"
    },
    {
        "source_table": "spree_taxon_groups",
        "source_query": "select count(*) from spree_taxon_groups;",
        "dest_table": "taxon_group",
        "dest_query": "select count(*) from taxon_group"
    },
    {
        "source_table": "spree_taxon_group_memberships",
        "source_query": "select count(*) from spree_taxon_group_memberships",
        "dest_table": "taxon_group_membership",
        "dest_query": "select count(*) from taxon_group_membership"
    },
    {
        "source_table": "spree_taxonomies",
        "source_query": "select count(*) from spree_taxonomies;",
        "dest_table": "taxonomies",
        "dest_query": "select count(*) from taxonomies"
    },
    {
        "source_table": "spree_taxons",
        "source_query": "SELECT count(*) FROM (SELECT rt.id, COALESCE(rt.name_en,'') AS name_en, COALESCE(CASE WHEN LENGTH(rt.name_en) < 5 THEN UPPER(REGEXP_REPLACE(TRANSLATE(rt.name_en, ' ', '_'), '[^a-zA-Z0-9_]', '', 'g'))||'_' || rt.id ELSE UPPER(SUBSTRING(REGEXP_REPLACE(TRANSLATE(rt.name_en, ' ', ''), '[^a-zA-Z0-9]', '', 'g'), 1, 1)) || UPPER(SUBSTRING(REGEXP_REPLACE(SUBSTRING(REGEXP_REPLACE(TRANSLATE(rt.name_en, ' ', ''), '[^a-zA-Z0-9]', ' ', 'g'), 2), ' ', ''), 1, 1)) || '_' || rt.id END,'') AS code, rt.created_at, rt.updated_at, rt.temp_taxon_id, COALESCE(rt.name_ar,'') AS name_ar FROM (SELECT ROW_NUMBER() OVER () AS id, st.id AS temp_taxon_id, MAX(CASE WHEN stt.locale = 'en' THEN stt.name END) AS name_en, MAX(CASE WHEN stt.locale = 'ar' THEN stt.name END) AS name_ar, st.created_at, st.updated_at FROM spree_taxons st LEFT JOIN spree_taxon_translations stt ON stt.spree_taxon_id = st.id WHERE st.parent_id IN (SELECT st.id AS brand_taxon_id FROM spree_taxons st JOIN spree_taxon_translations stt ON stt.spree_taxon_id = st.id AND locale = 'en' WHERE stt.name = 'Brands') GROUP BY st.id) AS rt ORDER BY rt.temp_taxon_id ASC) tb;",
        "dest_table": "brand",
        "dest_query": "select count(*) from brand"
    },
{
        "source_table": "spree_product_translations",
        "source_query": "select count(*) from (SELECT REGEXP_REPLACE(MAX(COALESCE(spt.supplier_name,'')), '-[0-9]+$', '') AS name, LEFT(COALESCE(spt.code, ''), 10) AS code, MAX(spt.created_at) as created_at, MAX(spt.updated_at) as updated_at, MAX(spt.deleted_at) as deleted_at FROM (SELECT spree_product_id, MAX(CASE WHEN locale = 'en' THEN manufacturer END) as supplier_name, MAX(CASE WHEN locale = 'ar' THEN manufacturer END) as code, MAX(created_at) as created_at, MAX(updated_at) as updated_at, MAX(deleted_at) as deleted_at FROM spree_product_translations WHERE manufacturer IS NOT NULL GROUP BY spree_product_id) as spt GROUP BY spt.code)tb",
        "dest_table": "supplier",
        "dest_query": "select count(*) from supplier"
    },
{
        "source_table": "spree_wishlists",
        "source_query": "select count(*) from spree_wishlists",
        "dest_table": "shopping_list",
        "dest_query": "select count(*) from shopping_list"
    },
{
        "source_table": "spree_wished_products",
        "source_query": "select count(*) from (select swp.wishlist_id as shopping_list_id,sv.product_id From spree_wished_products swp left join spree_variants sv on sv.id = swp.variant_id group by sv.product_id, swp.wishlist_id)tb",
        "dest_table": "shopping_list_products",
        "dest_query": "select count(*) from shopping_list_products"
    }
]


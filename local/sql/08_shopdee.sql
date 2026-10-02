-- ShopDee LOCAL — database + tables (Postgres postgres-rag, DB shopdee)
CREATE TABLE IF NOT EXISTS shop_products (
    id          SERIAL PRIMARY KEY,
    sku         TEXT NOT NULL UNIQUE,
    name        TEXT NOT NULL,
    category    TEXT NOT NULL,
    price       INTEGER NOT NULL CHECK (price >= 0),
    old_price   INTEGER NOT NULL DEFAULT 0,
    rating      NUMERIC(2,1) NOT NULL DEFAULT 0,
    reviews     INTEGER NOT NULL DEFAULT 0,
    stock       INTEGER NOT NULL DEFAULT 0,
    sold        INTEGER NOT NULL DEFAULT 0,
    shop_name   TEXT NOT NULL DEFAULT '',
    image_url   TEXT NOT NULL DEFAULT '',
    description TEXT NOT NULL DEFAULT '',
    specs       TEXT NOT NULL DEFAULT '',
    free_shipping BOOLEAN NOT NULL DEFAULT TRUE,
    cod           BOOLEAN NOT NULL DEFAULT TRUE,
    is_active   BOOLEAN NOT NULL DEFAULT TRUE,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS idx_shop_products_cat ON shop_products (category);
CREATE INDEX IF NOT EXISTS idx_shop_products_name ON shop_products USING gin (to_tsvector('simple', name));
CREATE INDEX IF NOT EXISTS idx_shop_products_active_price ON shop_products (is_active, price);

CREATE TABLE IF NOT EXISTS shop_orders (
    id          SERIAL PRIMARY KEY,
    code        TEXT NOT NULL UNIQUE,
    cust_name   TEXT NOT NULL,
    cust_phone  TEXT NOT NULL,
    address     TEXT NOT NULL DEFAULT '',
    note        TEXT NOT NULL DEFAULT '',
    subtotal    INTEGER NOT NULL DEFAULT 0,
    discount    INTEGER NOT NULL DEFAULT 0,
    shipping    INTEGER NOT NULL DEFAULT 0,
    total       INTEGER NOT NULL DEFAULT 0,
    status      TEXT NOT NULL DEFAULT 'pending',
    created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS idx_shop_orders_phone ON shop_orders (cust_phone);
CREATE INDEX IF NOT EXISTS idx_shop_orders_code ON shop_orders (code);

CREATE TABLE IF NOT EXISTS shop_order_items (
    id          SERIAL PRIMARY KEY,
    order_id    INTEGER NOT NULL REFERENCES shop_orders(id) ON DELETE CASCADE,
    product_id  INTEGER NOT NULL,
    name        TEXT NOT NULL,
    price       INTEGER NOT NULL,
    qty         INTEGER NOT NULL CHECK (qty > 0)
);
CREATE INDEX IF NOT EXISTS idx_shop_order_items_oid ON shop_order_items (order_id);

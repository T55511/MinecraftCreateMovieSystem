-- =========================
-- mst_ Master
-- =========================

-- mst_status_definition
CREATE TABLE IF NOT EXISTS mst_status_definition (
    status_key   text PRIMARY KEY,
    display_name text NOT NULL,
    scope        text NOT NULL CHECK (scope IN ('PROJECT', 'SUBTASK', 'COMMON')),
    is_done      boolean NOT NULL DEFAULT false,
    color_hex    text,
    is_active    boolean NOT NULL DEFAULT true,
    created_at   timestamptz NOT NULL DEFAULT now(),
    updated_at   timestamptz NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_mst_status_definition_scope
    ON mst_status_definition(scope);

-- mst_status_ui（mst_status_definition を参照）
CREATE TABLE IF NOT EXISTS mst_status_ui (
    scope         text NOT NULL CHECK (scope IN ('PROJECT', 'SUBTASK', 'COMMON')),
    status_key    text NOT NULL REFERENCES mst_status_definition(status_key),
    display_order integer NOT NULL,
    is_visible    boolean NOT NULL DEFAULT true,
    PRIMARY KEY (scope, status_key)
);

CREATE INDEX IF NOT EXISTS idx_mst_status_ui_scope_order
    ON mst_status_ui(scope, display_order);

-- mst_estimate_master（tpl_subtask_template を参照するので、実体は tpl_ の後に作る必要あり）
-- → このファイルでは作らない（03_tpl_template.sql の後半で作成する）

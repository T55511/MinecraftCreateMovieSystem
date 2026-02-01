-- =========================
-- tpl_ Template
-- =========================

-- tpl_checkitem
CREATE TABLE IF NOT EXISTS tpl_checkitem (
    checkitem_id    uuid PRIMARY KEY,
    name            text NOT NULL,
    description     text,
    default_checked boolean NOT NULL DEFAULT true,
    importance      integer,
    is_active       boolean NOT NULL DEFAULT true,
    created_at      timestamptz NOT NULL DEFAULT now(),
    updated_at      timestamptz NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_tpl_checkitem_active
    ON tpl_checkitem(is_active);

-- tpl_subtask_template
CREATE TABLE IF NOT EXISTS tpl_subtask_template (
    subtask_template_id uuid PRIMARY KEY,
    name            text NOT NULL,
    description     text,
    category        text,
    is_active       boolean NOT NULL DEFAULT true,
    latest_version  integer NOT NULL DEFAULT 1,
    created_at      timestamptz NOT NULL DEFAULT now(),
    updated_at      timestamptz NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_tpl_subtask_template_active
    ON tpl_subtask_template(is_active);

-- tpl_subtask_template_version
CREATE TABLE IF NOT EXISTS tpl_subtask_template_version (
    subtask_template_id uuid NOT NULL REFERENCES tpl_subtask_template(subtask_template_id),
    version     integer NOT NULL CHECK (version >= 1),
    snapshot    jsonb NOT NULL,
    change_note text,
    created_at  timestamptz NOT NULL DEFAULT now(),
    created_by  text NOT NULL DEFAULT 'local-user',
    PRIMARY KEY (subtask_template_id, version)
);

-- tpl_project_template（mst_status_definition を参照）
CREATE TABLE IF NOT EXISTS tpl_project_template (
    project_template_id uuid PRIMARY KEY,
    name              text NOT NULL,
    description       text,
    initial_status_key text NOT NULL REFERENCES mst_status_definition(status_key),
    default_angle_key  text,
    is_active         boolean NOT NULL DEFAULT true,
    latest_version    integer NOT NULL DEFAULT 1,
    created_at        timestamptz NOT NULL DEFAULT now(),
    updated_at        timestamptz NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_tpl_project_template_active
    ON tpl_project_template(is_active);

-- tpl_project_template_version
CREATE TABLE IF NOT EXISTS tpl_project_template_version (
    project_template_id uuid NOT NULL REFERENCES tpl_project_template(project_template_id),
    version     integer NOT NULL CHECK (version >= 1),
    snapshot    jsonb NOT NULL,
    change_note text,
    created_at  timestamptz NOT NULL DEFAULT now(),
    created_by  text NOT NULL DEFAULT 'local-user',
    PRIMARY KEY (project_template_id, version)
);

-- mst_angle（mst_だけど参照無しで独立。ここに置くかmstに置くかは自由）
CREATE TABLE IF NOT EXISTS mst_angle (
    angle_key           text PRIMARY KEY,
    display_name        text NOT NULL,
    description         text,
    recommended_seconds integer,
    is_active           boolean NOT NULL DEFAULT true,
    created_at          timestamptz NOT NULL DEFAULT now(),
    updated_at          timestamptz NOT NULL DEFAULT now()
);

-- =========================
-- mst_estimate_master（例外：tpl_subtask_template を参照するためここで作る）
-- =========================
CREATE TABLE IF NOT EXISTS mst_estimate_master (
    estimate_id         uuid PRIMARY KEY,
    subtask_template_id  uuid NOT NULL REFERENCES tpl_subtask_template(subtask_template_id),
    minutes             integer NOT NULL CHECK (minutes >= 0),
    note                text,
    is_active           boolean NOT NULL DEFAULT true,
    created_at          timestamptz NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_mst_estimate_master_subtask
    ON mst_estimate_master(subtask_template_id);

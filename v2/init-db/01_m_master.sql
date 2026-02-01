-- =========================
-- m_ Master / Rule / Checklist
-- =========================

-- m_phase
CREATE TABLE IF NOT EXISTS m_phase (
    phase_id      integer PRIMARY KEY,
    phase_key     varchar(50)  NOT NULL UNIQUE,
    display_name  varchar(100) NOT NULL,
    description   text,
    sort_order    integer      NOT NULL,
    is_active     boolean      NOT NULL DEFAULT true
);

-- m_task_template（m_phase を参照）
CREATE TABLE IF NOT EXISTS m_task_template (
    task_template_id integer PRIMARY KEY,
    task_name        varchar(200) NOT NULL,
    phase_id         integer      NOT NULL REFERENCES m_phase(phase_id),
    est_time_min     integer      NOT NULL DEFAULT 0,
    is_timer_target  boolean      NOT NULL DEFAULT false,

    -- 将来用（あなたの要望で追加）
    default_status   varchar(20)  NOT NULL DEFAULT '未着手',
    task_category    varchar(50)  NOT NULL DEFAULT 'GENERAL',

    sort_order       integer      NOT NULL DEFAULT 0,
    is_active        boolean      NOT NULL DEFAULT true
);

CREATE INDEX IF NOT EXISTS idx_m_task_template_phase
    ON m_task_template(phase_id);

-- m_check_item
CREATE TABLE IF NOT EXISTS m_check_item (
    check_item_id integer PRIMARY KEY,
    label         varchar(200) NOT NULL,
    sort_order    integer      NOT NULL DEFAULT 0,
    is_active     boolean      NOT NULL DEFAULT true
);

-- m_task_check_map（m_task_template / m_check_item を参照）
CREATE TABLE IF NOT EXISTS m_task_check_map (
    task_template_id integer NOT NULL REFERENCES m_task_template(task_template_id),
    check_item_id    integer NOT NULL REFERENCES m_check_item(check_item_id),
    PRIMARY KEY (task_template_id, check_item_id)
);

-- 追加仕様（将来用）----------------

-- m_status
CREATE TABLE IF NOT EXISTS m_status (
    status_id      SERIAL PRIMARY KEY,
    status_name    varchar(50) NOT NULL,
    display_order  int NOT NULL,
    is_active      boolean NOT NULL DEFAULT true
);

-- m_personal_angle
CREATE TABLE IF NOT EXISTS m_personal_angle (
    angle_id            SERIAL PRIMARY KEY,
    angle_name          varchar(50) NOT NULL,
    prompt_instruction  text NOT NULL,
    is_active           boolean NOT NULL DEFAULT true
);

-- m_transition_rule（m_status を参照）
CREATE TABLE IF NOT EXISTS m_transition_rule (
    rule_id             SERIAL PRIMARY KEY,
    current_status_id   int NOT NULL REFERENCES m_status(status_id),
    next_status_id      int NOT NULL REFERENCES m_status(status_id),
    required_task_ids   int[] NOT NULL,
    is_active           boolean NOT NULL DEFAULT true
);

-- m_quality_checklist（m_task_template を参照）
CREATE TABLE IF NOT EXISTS m_quality_checklist (
    check_id        SERIAL PRIMARY KEY,
    check_item      varchar(255) NOT NULL,
    target_task_id  int REFERENCES m_task_template(task_template_id),
    is_required     boolean NOT NULL DEFAULT true,
    is_active       boolean NOT NULL DEFAULT true
);

-- =========================
-- t_ Transaction / Logs
-- =========================

-- t_project（Models.py 版で統一）
CREATE TABLE IF NOT EXISTS t_project (
    project_id           integer PRIMARY KEY,
    theme                varchar(300) NOT NULL,
    due_date             date,
    publish_scheduled_at date,
    progress_rate        double precision NOT NULL DEFAULT 0.0,
    memo                 text,
    created_at           timestamptz NOT NULL,
    updated_at           timestamptz NOT NULL
);

-- t_project_task
CREATE TABLE IF NOT EXISTS t_project_task (
    project_task_id        integer PRIMARY KEY,
    project_id             integer NOT NULL REFERENCES t_project(project_id),
    task_template_id        integer NOT NULL REFERENCES m_task_template(task_template_id),
    task_name_snapshot      varchar(200) NOT NULL,
    phase_id_snapshot       integer NOT NULL,
    status                 varchar(20) NOT NULL DEFAULT '未着手',
    est_time_min_snapshot   integer NOT NULL DEFAULT 0,
    actual_time_min         double precision NOT NULL DEFAULT 0.0,
    sort_order              integer NOT NULL DEFAULT 0,
    is_active               boolean NOT NULL DEFAULT true,
    created_at              timestamptz NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_t_project_task_project
    ON t_project_task(project_id);

-- uq_project_task_template
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint WHERE conname = 'uq_project_task_template'
    ) THEN
        ALTER TABLE t_project_task
            ADD CONSTRAINT uq_project_task_template UNIQUE (project_id, task_template_id);
    END IF;
END$$;

-- t_timer_log
CREATE TABLE IF NOT EXISTS t_timer_log (
    timer_log_id    integer GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    project_task_id integer NOT NULL REFERENCES t_project_task(project_task_id),
    start_time      timestamptz NOT NULL,
    end_time        timestamptz,
    duration_min    double precision
);

CREATE INDEX IF NOT EXISTS idx_t_timer_log_task
    ON t_timer_log(project_task_id);

-- t_check_result
CREATE TABLE IF NOT EXISTS t_check_result (
    project_task_id integer NOT NULL REFERENCES t_project_task(project_task_id),
    check_item_id   integer NOT NULL REFERENCES m_check_item(check_item_id),
    is_checked      boolean NOT NULL DEFAULT false,
    PRIMARY KEY (project_task_id, check_item_id)
);

-- t_event_log（推奨: UUID）
CREATE TABLE IF NOT EXISTS t_event_log (
    id          BIGSERIAL PRIMARY KEY,
    event_id    uuid NOT NULL UNIQUE DEFAULT gen_random_uuid(),

    "timestamp" timestamptz NOT NULL,
    level       varchar(16) NOT NULL,
    event_type  varchar(16) NOT NULL,
    request_id  varchar(64),

    actor       varchar(64)  NOT NULL,
    action      varchar(200) NOT NULL,

    target_type varchar(64)  NOT NULL,
    target_id   varchar(128),

    summary     text NOT NULL,
    detail      jsonb,

    created_at  timestamptz NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS ix_event_log_ts
    ON t_event_log ("timestamp" DESC);

CREATE INDEX IF NOT EXISTS ix_event_log_level_ts
    ON t_event_log (level, "timestamp" DESC);

CREATE INDEX IF NOT EXISTS ix_event_log_type_ts
    ON t_event_log (event_type, "timestamp" DESC);

CREATE INDEX IF NOT EXISTS ix_event_log_reqid
    ON t_event_log (request_id);

CREATE INDEX IF NOT EXISTS ix_event_log_action
    ON t_event_log (action);

CREATE INDEX IF NOT EXISTS ix_event_log_target
    ON t_event_log (target_type, target_id);

-- 追加仕様（将来用）----------------

-- t_shorts_management
CREATE TABLE IF NOT EXISTS t_shorts_management (
    shorts_id             BIGSERIAL PRIMARY KEY,
    vod_project_id         bigint NOT NULL REFERENCES t_project(project_id),
    source_timestamp_sec   int NOT NULL,
    shorts_theme           varchar(100) NOT NULL,
    status                 varchar(20) NOT NULL,
    is_high_hook           boolean NOT NULL DEFAULT false,
    published_at           timestamp
);

-- t_channel_growth
CREATE TABLE IF NOT EXISTS t_channel_growth (
    record_id        BIGSERIAL PRIMARY KEY,
    start_date       date NOT NULL,
    end_date         date NOT NULL,
    views_count      bigint NOT NULL,
    subscriber_gain  int NOT NULL,
    watch_time_min   bigint NOT NULL,
    impression_count bigint NOT NULL,
    avg_ctr          numeric(4,2) NOT NULL,
    improvements_made text,
    recorded_at      timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- t_quality_check_result
CREATE TABLE IF NOT EXISTS t_quality_check_result (
    result_id   BIGSERIAL PRIMARY KEY,
    project_id  bigint NOT NULL REFERENCES t_project(project_id),
    check_id    int NOT NULL REFERENCES m_quality_checklist(check_id),
    is_checked  boolean NOT NULL,
    checked_at  timestamp,
    memo        text
);

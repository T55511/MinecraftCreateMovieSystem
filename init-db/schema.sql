-- 1. プロジェクトステータス定義マスタ (m_status)
CREATE TABLE m_status (
    status_id SERIAL PRIMARY KEY,
    status_name VARCHAR(50) NOT NULL,
    display_order INT NOT NULL,
    is_active BOOLEAN NOT NULL DEFAULT TRUE
);

-- 2. サブタスクテンプレートマスタ (m_task_template)
CREATE TABLE m_task_template (
    task_template_id SERIAL PRIMARY KEY,
    task_name VARCHAR(100) NOT NULL,
    est_time_min INT NOT NULL DEFAULT 0,
    is_timer_target BOOLEAN NOT NULL DEFAULT FALSE,
    default_status VARCHAR(20) NOT NULL DEFAULT '未着手',
    task_category VARCHAR(50) NOT NULL
);

-- 3. ステータス遷移ルールマスタ (m_transition_rule)
CREATE TABLE m_transition_rule (
    rule_id SERIAL PRIMARY KEY,
    current_status_id INT NOT NULL REFERENCES m_status(status_id),
    next_status_id INT NOT NULL REFERENCES m_status(status_id),
    required_task_ids INT[] NOT NULL,  -- 遷移に必要な完了済みサブタスクIDの配列
    is_active BOOLEAN NOT NULL DEFAULT TRUE
);

-- 4. パーソナルアングル選択マスタ (m_personal_angle)
CREATE TABLE m_personal_angle (
    angle_id SERIAL PRIMARY KEY,
    angle_name VARCHAR(50) NOT NULL,
    prompt_instruction TEXT NOT NULL,
    is_active BOOLEAN NOT NULL DEFAULT TRUE
);

-- 5. 品質チェックリストマスタ (m_quality_checklist)
CREATE TABLE m_quality_checklist (
    check_id SERIAL PRIMARY KEY,
    check_item VARCHAR(255) NOT NULL,
    target_task_id INT REFERENCES m_task_template(task_template_id),
    is_required BOOLEAN NOT NULL DEFAULT TRUE,
    is_active BOOLEAN NOT NULL DEFAULT TRUE
);

-- 6. プロジェクト実績テーブル (t_project)
CREATE TABLE t_project (
    project_id BIGSERIAL PRIMARY KEY,
    type_id INT NOT NULL, -- プロジェクトタイプ（マスタは省略、ここではINTで定義）
    current_status_id INT NOT NULL REFERENCES m_status(status_id),
    theme VARCHAR(255) NOT NULL,
    input_angle_id INT NOT NULL REFERENCES m_personal_angle(angle_id),
    scaffold_data JSONB NOT NULL, -- トーク骨子データ
    thumbnail_concept JSONB, -- サムネイルコンセプト
    progress_rate INT NOT NULL DEFAULT 0, -- 進捗率（0〜100）
    final_title VARCHAR(255),
    final_description TEXT,
    summary_data JSONB, -- 動画要約データ
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    published_at TIMESTAMP
);

-- 7. サブタスク実績テーブル (t_project_task)
CREATE TABLE t_project_task (
    project_task_id BIGSERIAL PRIMARY KEY,
    project_id BIGINT NOT NULL REFERENCES t_project(project_id),
    task_template_id INT NOT NULL REFERENCES m_task_template(task_template_id),
    status VARCHAR(20) NOT NULL, -- (未着手, 進行中, 完了)
    est_time_min INT NOT NULL,
    actual_time_min float,
    completed_at TIMESTAMP
);

-- 8. 時間計測ログテーブル (t_timer_log)
CREATE TABLE t_timer_log (
    log_id BIGSERIAL PRIMARY KEY,
    project_task_id BIGINT NOT NULL REFERENCES t_project_task(project_task_id),
    start_time TIMESTAMP NOT NULL,
    end_time TIMESTAMP,
    section_index INT,
    duration_min float, -- 分単位で記録
    memo TEXT
);

-- 9. VOD → Shorts ファネル管理テーブル (t_shorts_management)
CREATE TABLE t_shorts_management (
    shorts_id BIGSERIAL PRIMARY KEY,
    vod_project_id BIGINT NOT NULL REFERENCES t_project(project_id),
    source_timestamp_sec INT NOT NULL,
    shorts_theme VARCHAR(100) NOT NULL,
    status VARCHAR(20) NOT NULL, -- (未作成, 編集済, 公開済)
    is_high_hook BOOLEAN NOT NULL DEFAULT FALSE,
    published_at TIMESTAMP
);

-- 10. チャンネル成長トラッカーテーブル (t_channel_growth)
CREATE TABLE t_channel_growth (
    record_id BIGSERIAL PRIMARY KEY,
    start_date DATE NOT NULL,
    end_date DATE NOT NULL,
    views_count BIGINT NOT NULL,
    subscriber_gain INT NOT NULL,
    watch_time_min BIGINT NOT NULL,
    impression_count BIGINT NOT NULL,
    avg_ctr NUMERIC(4, 2) NOT NULL,
    improvements_made TEXT,
    recorded_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- 11. 品質チェックリスト実績テーブル (t_quality_check_result)
CREATE TABLE t_quality_check_result (
    result_id BIGSERIAL PRIMARY KEY,
    project_id BIGINT NOT NULL REFERENCES t_project(project_id),
    check_id INT NOT NULL REFERENCES m_quality_checklist(check_id),
    is_checked BOOLEAN NOT NULL,
    checked_at TIMESTAMP,
    memo TEXT
);
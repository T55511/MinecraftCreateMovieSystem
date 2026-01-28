-- 必要なら
CREATE EXTENSION IF NOT EXISTS pgcrypto;

-- =========================
-- 4) ステータス定義
-- =========================
CREATE TABLE IF NOT EXISTS mst_status_definition (
  status_key        text PRIMARY KEY,                 -- 変更不可
  display_name      text NOT NULL,
  scope             text NOT NULL CHECK (scope IN ('PROJECT','SUBTASK','COMMON')),
  is_done           boolean NOT NULL DEFAULT false,
  color_hex         text,                              -- 例: #RRGGBB
  is_active         boolean NOT NULL DEFAULT true,
  created_at        timestamptz NOT NULL DEFAULT now(),
  updated_at        timestamptz NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_mst_status_definition_scope
  ON mst_status_definition(scope);

-- =========================
-- 5) ステータス順序・表示（UI用）
-- =========================
CREATE TABLE IF NOT EXISTS mst_status_ui (
  scope             text NOT NULL CHECK (scope IN ('PROJECT','SUBTASK','COMMON')),
  status_key        text NOT NULL REFERENCES mst_status_definition(status_key),
  display_order     integer NOT NULL,
  is_visible        boolean NOT NULL DEFAULT true,     -- 非表示＝選択不可（UIルール）
  PRIMARY KEY (scope, status_key)
);

CREATE INDEX IF NOT EXISTS idx_mst_status_ui_scope_order
  ON mst_status_ui(scope, display_order);

-- =========================
-- 3) チェックリストテンプレ（上書き可）
-- =========================
CREATE TABLE IF NOT EXISTS tpl_checkitem (
  checkitem_id      uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  name              text NOT NULL,
  description       text,
  default_checked   boolean NOT NULL DEFAULT true,     -- デフォルトON（確定）
  importance        integer,                           -- 任意: 1-5等
  is_active         boolean NOT NULL DEFAULT true,
  created_at        timestamptz NOT NULL DEFAULT now(),
  updated_at        timestamptz NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_tpl_checkitem_active
  ON tpl_checkitem(is_active);

-- =========================
-- 6) 標準見積時間マスタ（分）
--  - “変更”は新規行を作る運用を推奨（既存テンプレ版を変えないため）
-- =========================
CREATE TABLE IF NOT EXISTS mst_estimate_master (
  estimate_id       uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  subtask_template_id uuid NOT NULL,                   -- FKは後で tpl_subtask_template 作成後に貼る
  minutes           integer NOT NULL CHECK (minutes >= 0),
  note              text,
  is_active         boolean NOT NULL DEFAULT true,
  created_at        timestamptz NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_mst_estimate_master_subtask
  ON mst_estimate_master(subtask_template_id);

-- =========================
-- 2) サブタスクテンプレ（版管理）
-- =========================
CREATE TABLE IF NOT EXISTS tpl_subtask_template (
  subtask_template_id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  name              text NOT NULL,
  description       text,
  category          text,
  is_active         boolean NOT NULL DEFAULT true,
  latest_version    integer NOT NULL DEFAULT 1,
  created_at        timestamptz NOT NULL DEFAULT now(),
  updated_at        timestamptz NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_tpl_subtask_template_active
  ON tpl_subtask_template(is_active);

CREATE TABLE IF NOT EXISTS tpl_subtask_template_version (
  subtask_template_id uuid NOT NULL REFERENCES tpl_subtask_template(subtask_template_id),
  version            integer NOT NULL CHECK (version >= 1),
  snapshot           jsonb NOT NULL,                   -- チェック項目順序・見積参照ID等を固定
  change_note        text,
  created_at         timestamptz NOT NULL DEFAULT now(),
  created_by         text NOT NULL DEFAULT 'local-user',
  PRIMARY KEY (subtask_template_id, version)
);

-- =========================
-- 1) プロジェクトテンプレ（版管理）
--  - サブタスク紐づけは「1件以上必須」(DBでも保証するならトリガ/手続き推奨)
-- =========================
CREATE TABLE IF NOT EXISTS tpl_project_template (
  project_template_id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  name              text NOT NULL,
  description       text,
  initial_status_key text NOT NULL REFERENCES mst_status_definition(status_key),
  default_angle_key  text,                             -- mst_angle の key を想定（後述）
  is_active         boolean NOT NULL DEFAULT true,
  latest_version    integer NOT NULL DEFAULT 1,
  created_at        timestamptz NOT NULL DEFAULT now(),
  updated_at        timestamptz NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_tpl_project_template_active
  ON tpl_project_template(is_active);

CREATE TABLE IF NOT EXISTS tpl_project_template_version (
  project_template_id uuid NOT NULL REFERENCES tpl_project_template(project_template_id),
  version            integer NOT NULL CHECK (version >= 1),
  snapshot           jsonb NOT NULL,                   -- 紐づけサブタスク(テンプレID+version+order)等を固定
  change_note        text,
  created_at         timestamptz NOT NULL DEFAULT now(),
  created_by         text NOT NULL DEFAULT 'local-user',
  PRIMARY KEY (project_template_id, version)
);

-- =========================
-- 7) アングルマスタ
-- =========================
CREATE TABLE IF NOT EXISTS mst_angle (
  angle_key         text PRIMARY KEY,
  display_name      text NOT NULL,
  description       text,
  recommended_seconds integer,
  is_active         boolean NOT NULL DEFAULT true,
  created_at        timestamptz NOT NULL DEFAULT now(),
  updated_at        timestamptz NOT NULL DEFAULT now()
);

-- =========================
-- 後付けFK（循環回避のため最後に）
-- =========================
ALTER TABLE mst_estimate_master
  ADD CONSTRAINT fk_estimate_subtask_template
  FOREIGN KEY (subtask_template_id)
  REFERENCES tpl_subtask_template(subtask_template_id);

ALTER TABLE t_project
  ADD COLUMN IF NOT EXISTS applied_project_template_id uuid,
  ADD COLUMN IF NOT EXISTS applied_project_template_version integer;

-- 参照整合性（任意）
ALTER TABLE t_project
  ADD CONSTRAINT fk_projects_applied_template
  FOREIGN KEY (applied_project_template_id)
  REFERENCES tpl_project_template(project_template_id);

ALTER TABLE t_project_task
  ADD COLUMN IF NOT EXISTS applied_subtask_template_id uuid,
  ADD COLUMN IF NOT EXISTS applied_subtask_template_version integer;

ALTER TABLE t_project_task
  ADD CONSTRAINT fk_subtasks_applied_template
  FOREIGN KEY (applied_subtask_template_id)
  REFERENCES tpl_subtask_template(subtask_template_id);

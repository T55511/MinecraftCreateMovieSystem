-- m_status: プロジェクトステータスの初期データ
INSERT INTO m_status (status_id, status_name, display_order) VALUES
(1, '企画中', 1),
(2, '収録・準備中', 2),
(3, '編集作業中', 3),
(4, '最終チェック', 4),
(5, '公開待ち', 5),
(6, '完了', 6)
ON CONFLICT (status_id) DO NOTHING;

-- m_personal_angle: パーソナルアングルの初期データ
INSERT INTO m_personal_angle (angle_id, angle_name, prompt_instruction) VALUES
(1, '矛盾と疑問', 'テーマに関する一般的な意見や、視聴者が抱くであろう「矛盾点」や「素朴な疑問」を突く質問を生成しなさい。'),
(2, '未来と変化', 'テーマが未来にどのような影響を与えるか、また現状からどのような変化が起きるかに焦点を当てた質問を生成しなさい。')
ON CONFLICT (angle_id) DO NOTHING;

-- m_task_template: サブタスクテンプレートの初期データ
INSERT INTO m_task_template (task_name, task_category, est_time_min, is_timer_target) VALUES
('トーク骨子生成', '企画', 20, FALSE),
('骨子の確定と調整', '企画', 20, FALSE),
('導入フック入力・ロック', '企画', 20, FALSE),
('収録作業', '収録', 20, TRUE),
('カット編集', '編集', 20, TRUE),
('テロップ・字幕の挿入', '編集', 20, TRUE),
('SE/BGM・装飾の挿入', '編集', 30, TRUE),
('サムネイル作成', '編集', 20, TRUE),
('タイトル・概要欄の最終調整', '編集', 20, FALSE),
('品質チェックリストの実行', 'チェック', 20, FALSE),
('公開（予約含む）', '公開', 15, FALSE),
('SNS告知予約', '公開', 10, FALSE)
ON CONFLICT (task_template_id) DO NOTHING;

-- m_transition_rule: 企画中 (1) から 収録・準備中 (2) への遷移ルール
INSERT INTO m_transition_rule (rule_id, current_status_id, next_status_id, required_task_ids) VALUES
(1, 1, 2, ARRAY[2, 3])
ON CONFLICT (rule_id) DO NOTHING;
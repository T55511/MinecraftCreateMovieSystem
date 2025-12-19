# app/services/ai_generator.py

from google import genai
from google.genai import types # type: ignore
from google.genai.errors import APIError # type: ignore
from sqlalchemy.orm import Session  # type: ignore
from ..models.master import DBAngle, DBTaskTemplate
from ..models.project import DBProject, DBProjectTask
from ..schemas.ai import ProjectSummary, TalkScaffold
from pydantic_settings import BaseSettings # type: ignore
import os
import json
from typing import Dict, Any, List

# 環境変数を読み込むための設定
class AISettings(BaseSettings):
    gemini_api_key: str = os.getenv("GEMINI_API_KEY", "DUMMY_KEY")

ai_settings = AISettings()

# 💡 修正1: APIキーが設定されているかチェック
if not ai_settings.gemini_api_key or ai_settings.gemini_api_key == "DUMMY_KEY":
    # キーがない場合は、接続を試みずにエラーを発生させる
    raise ValueError("GEMINI_API_KEY environment variable is not set or is invalid.")

# 💡 修正2: クライアント初期化時にAPIキーの有効性を確認
try:
    client = genai.Client(api_key=ai_settings.gemini_api_key)
except Exception as e:
    # 初期化時の致命的なエラーを捕捉
    raise RuntimeError(f"Failed to initialize Gemini Client: {e}")

# ----------------------------------------------------
# 💡 トーク骨子生成のメイン関数
# ----------------------------------------------------

def generate_talk_scaffold(db: Session, project_id: int) -> Dict[str, Any]:
    """
    Gemini APIを呼び出し、プロジェクト情報に基づきトーク骨子を生成する。
    """
    project: DBProject = db.get(DBProject, project_id)
    if not project:
        raise ValueError("Project not found.")

    # 1. パーソナルアングルの指示を取得
    angle: DBAngle = db.get(DBAngle, project.input_angle_id)
    if not angle:
        raise ValueError("Personal angle not found.")

    # 2. プロンプトの組み立て (役割、制約、JSONスキーマを明記)
    prompt_instruction = angle.prompt_instruction
    theme = project.theme
    
    # ターゲット温度設定: 創造性重視のため 0.7 を適用
    temperature = 0.7 

    system_prompt = f"""
    あなたは、人気YouTubeクリエイターのトーク構成アシスタントです。
    以下の情報に基づき、視聴者の興味を引きつけ、深い考察を促すための「トーク骨子」をJSON形式で生成してください。

    # 制約条件
    1. 生成するJSONは、指定されたスキーマ（TalkScaffold）に完全に準拠すること。
    2. discussion_flowには、必ず8つの異なる質問を含めること。
    3. {prompt_instruction}というアングルの指示を厳守し、テーマを多角的に掘り下げること。
    4. target_time_minは、合計で約12分〜15分になるように配分すること。
    5. JSON以外の説明文や装飾文字は一切含めないこと。

    # 入力データ
    - トークテーマ: {theme}
    """
    
    # 3. API呼び出し設定
    try:
        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=system_prompt,
            config=types.GenerateContentConfig(
                temperature=temperature,
                response_mime_type="application/json",
            )
        )
    # 💡 修正3: API通信エラーを捕捉し、詳細をログに出力
    except APIError as e:
        print(f"--- GEMINI API CALL FAILED ---")
        print(f"Error Code: {e.code}, Message: {e.message}")
        print("------------------------------")
        raise ValueError(f"Gemini API通信エラーが発生しました: {e.message}")
    except Exception as e:
        # その他の予期せぬエラー
        raise ValueError(f"Gemini API呼び出し中に予期せぬエラーが発生しました: {e}")
    
    # 4. JSONデータのパースとバリデーション (👈 ここを修正)
    try:
        # 💡 修正: 応答テキストから不要な空白・改行を一時的に除去し、JSONとしてロードする
        # この処理は、AIが生成したJSON文字列の前後や内部に予期せぬ空白・改行がある場合に有効
        cleaned_text = response.text.strip()
        
        # 応答が "```json\n{...}\n```" のようなMarkdownブロックで囲まれている場合を想定
        # これを除去する処理を組み込みます。
        if cleaned_text.startswith('```') and cleaned_text.endswith('```'):
            cleaned_text = cleaned_text.strip('```').strip()
            if cleaned_text.startswith('json'):
                cleaned_text = cleaned_text[len('json'):].strip()

        raw_data = json.loads(cleaned_text)
        
        # 💡 標準の辞書をそのまま返す
        return raw_data
    
    except Exception as e:
        print(f"AI出力のパースに失敗しました: {e}")
        # APIキーが空の場合、ここでエラーになる可能性が高い
        raise ValueError(f"AIからの純粋なJSONパースに失敗しました。エラー: {e}")

# ----------------------------------------------------
# 💡 骨子のDB更新関数
# ----------------------------------------------------

def update_scaffold_in_project(db: Session, project_id: int, scaffold: Dict[str, Any]): # 👈 引数の型を dict に変更
    """生成された骨子データをプロジェクトテーブルに保存する"""
    db_project: DBProject = db.get(DBProject, project_id)
    if not db_project:
        raise ValueError("Project not found for update.")

    # 💡 修正: scaffold は既に dict なので、そのまま代入する
    db_project.scaffold_data = scaffold # .model_dump() を削除
    db.add(db_project)
    db.commit()

# ----------------------------------------------------
# 💡 サムネイルコンセプト生成のメイン関数
# ----------------------------------------------------

def generate_thumbnail_concept(db: Session, project_id: int) -> Dict[str, Any]:
    """
    Gemini APIを呼び出し、トーク骨子に基づきサムネイルコンセプトを生成する。
    """
    project: DBProject = db.get(DBProject, project_id)
    if not project:
        raise ValueError("Project not found.")
    
    scaffold_data = project.scaffold_data # トーク骨子データ（dict）を取得
    if not scaffold_data:
        raise ValueError("Talk scaffold data (scaffold_data) is missing. Generate talk scaffold first.")

    theme = project.theme
    
    # トーク骨子の主要な要素をプロンプトに組み込む
    title_suggestion = scaffold_data.get('suggested_title', '（タイトル未定）')
    intro_text = scaffold_data.get('script_intro_text', '')
    
    # ターゲット温度設定: 創造性重視のため 0.9 を適用
    temperature = 0.9 

    system_prompt = f"""
    あなたは、視聴者のクリックを誘うプロのサムネイルデザイナーです。
    以下のプロジェクト情報に基づき、視聴者の目を引くサムネイルのコンセプトをJSON形式で生成してください。

    # 制約条件
    1. 生成するJSONは、指定されたスキーマ（ThumbnailConcept）の構造に完全に準拠すること。
    2. visual_theme、required_elements、emotion_targetの3つの要素を必ず含めること。
    3. JSON以外の説明文や装飾文字は一切含めないこと。

    # 入力データ
    - プロジェクトテーマ: {theme}
    - 推奨動画タイトル: {title_suggestion}
    - 導入フック（コンセプト把握のため）: {intro_text}
    """
    
    # API呼び出し
    try:
        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=system_prompt,
            config=types.GenerateContentConfig(
                temperature=temperature,
                response_mime_type="application/json",
            )
        )

        cleaned_text = response.text.strip()
        # ... (Markdownブロックのクリーンアップ処理は generate_talk_scaffold から流用) ...
        if cleaned_text.startswith('```') and cleaned_text.endswith('```'):
            cleaned_text = cleaned_text.strip('```').strip()
            if cleaned_text.startswith('json'):
                cleaned_text = cleaned_text[len('json'):].strip()
                
        raw_data = json.loads(cleaned_text)
        
        # 💡 ここでは、生成された辞書が最低限の構造を持っているかを確認する
        if not all(key in raw_data for key in ['visual_theme', 'required_elements', 'emotion_target']):
            raise ValueError("AI output is structurally incomplete.")

        return raw_data 

    except APIError as e:
        raise ValueError(f"Gemini API通信エラーが発生しました: {e.message}")
    except Exception as e:
        raise ValueError(f"AI出力のパースに失敗しました: {e}")

# ----------------------------------------------------
# 💡 サムネイルコンセプトのDB更新関数
# ----------------------------------------------------

def update_thumbnail_in_project(db: Session, project_id: int, thumbnail_concept: Dict[str, Any]):
    """生成されたサムネイルコンセプトをプロジェクトテーブルに保存する"""
    db_project: DBProject = db.get(DBProject, project_id)
    if not db_project:
        raise ValueError("Project not found for update.")

    # 辞書をJSONBとしてそのまま保存
    db_project.thumbnail_data = thumbnail_concept
    db.add(db_project)
    db.commit()

# ----------------------------------------------------
# 💡 プロジェクトサマリー生成のメイン関数
# ----------------------------------------------------

# def generate_project_summary(db: Session, project_id: int) -> Dict[str, Any]:
#     """
#     プロジェクトの実績時間と達成度に基づき、サマリーと反省点を生成する。
#     """
#     db_project: DBProject = db.get(DBProject, project_id)
#     if not db_project:
#         raise ValueError("Project not found.")

#     # 1. 必要な情報の収集
#     theme = db_project.theme
#     progress_rate = db_project.progress_rate
    
#     # 全タスクの実績時間データを取得
#     tasks: List[DBProjectTask] = db.query(DBProjectTask).filter(
#         DBProjectTask.project_id == project_id
#     ).all()

#     # タスクの実績データを整形
#     task_data_list = []
#     for task in tasks:
#         # DBProjectTaskには 'task_template_id' があるため、マスター名を取得したいが、
#         # ここではタスクIDと実績時間、ステータスを使用する
#         task_data_list.append({
#             "task_id": task.task_template_id,
#             "status": task.status,
#             "estimated_min": task.est_time_min,
#             "actual_min": task.actual_time_min,
#         })
    
#     # データが存在しない場合のチェック
#     if not task_data_list:
#         raise ValueError("No tasks found for this project.")

#     # ターゲット温度設定: 分析と創造性を兼ねるため 0.7 を適用
#     temperature = 0.7 

#     # 💡 修正: PydanticスキーマをJSON形式で取得
#     schema_json = ProjectSummary.model_json_schema()

#     # 2. プロンプトの構築を修正
#     system_prompt = f"""
#     あなたは、クリエイターの生産性を分析し、習慣を改善するためのコーチです。
#     以下のプロジェクト実績データに基づき、プロジェクト全体の成果サマリーと、
#     **実績時間と見積時間の差**、**タスク完了状況**を分析した具体的な反省点と改善提案をJSON形式で生成してください。

#     # 最重要制約条件
#     1. 生成するJSONは、**以下の[JSON SCHEMA]に完全に準拠**し、トップレベルのキーや構造を変更しないこと。
#     2. JSON以外の説明文や装飾文字は一切含めないこと。
#     3. すべてのフィールドを埋めること。
    
#     # [JSON SCHEMA]
#     {json.dumps(schema_json, ensure_ascii=False, indent=2)}

#     # 入力データ
#     - プロジェクトテーマ: {theme}
#     - 最終進捗率: {progress_rate}%
#     - タスク実績データ (分単位): {json.dumps(task_data_list, ensure_ascii=False)}
    
#     # 分析のポイント
#     - actual_min > estimated_min のタスクは、見積もりの甘さまたは非効率性を示します。
#     - actual_min = 0 のタスクは、未着手または計測漏れを示します。
#     """

def generate_project_summary(db: Session, project_id: int) -> Dict[str, Any]:
    db_project: DBProject = db.get(DBProject, project_id)
    if not db_project:
        raise ValueError("Project not found.")

    # 1. 必要な情報の収集（マスタからタスク名を取得）
    theme = db_project.theme
    progress_rate = db_project.progress_rate
    
    # タスクとテンプレート名を結合して取得
    # 💡 修正: タスク名を取得することでAIが「何をしたか」理解できるようにする
    tasks_with_names = db.query(
        DBProjectTask, DBTaskTemplate.task_name
    ).join(
        DBTaskTemplate, DBProjectTask.task_template_id == DBTaskTemplate.task_template_id
    ).filter(
        DBProjectTask.project_id == project_id
    ).all()

    task_data_list = []
    for task, task_name in tasks_with_names:
        # 乖離率の計算
        diff = task.actual_time_min - task.est_time_min
        status_label = "✅完了" if task.status == "完了" else f"⚠️{task.status}"
        
        task_data_list.append({
            "作業名": task_name,
            "ステータス": status_label,
            "見積(分)": task.est_time_min,
            "実績(分)": round(task.actual_time_min, 1),
            "乖離(分)": round(diff, 1)
        })
    
    if not task_data_list:
        raise ValueError("No tasks found for this project.")
    
    # ターゲット温度設定: 分析と創造性を兼ねるため 0.7 を適用
    temperature = 0.7 

    # 2. プロンプトの構築（コーチング能力を強化）
    schema_json = ProjectSummary.model_json_schema()

    system_prompt = f"""
    あなたは動画クリエイター専門の生産性コンサルタントです。
    以下のプロジェクト実績データを分析し、次回の制作をより楽に、効率的にするための「戦略的振り返り」を生成してください。

    # データ
    - テーマ: {theme}
    - 完了率: {progress_rate}%
    - 詳細データ: {json.dumps(task_data_list, ensure_ascii=False, indent=2)}

    # 分析の極意
    1. 【時間管理】見積もりより20%以上オーバーしたタスクを特定し、その原因（技術不足、集中力、外的要因など）を推論して。
    2. 【達成度】未完了のタスクがある場合、ボトルネックがどこにあったか指摘して。
    3. 【称賛】予定通り、あるいは予定より早く終わったタスクはしっかり褒めて。
    4. 【具体策】次回、同じテーマで動画を作るなら「どのタスクの見積もりを増やすべきか」「どの工程を自動化すべきか」提案して。

    # 制約
    - 指定のJSONスキーマに完全準拠すること。
    {json.dumps(schema_json, ensure_ascii=False, indent=2)}
    """
    
    # 3. API呼び出し
    try:
        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=system_prompt,
            config=types.GenerateContentConfig(
                temperature=temperature,
                response_mime_type="application/json",
            )
        )

        # 4. JSONのパースと検証
        cleaned_text = response.text.strip()
        if cleaned_text.startswith('```'):
            # 最初に見つかった '```' と最後の '```' の間を抽出する
            try:
                # 最初の '```' 以降の文字列を取得
                start_index = cleaned_text.find('```') + 3
                # その後の 'json' や改行をスキップ
                if cleaned_text[start_index:].strip().startswith('json'):
                    start_index += len('json')
                
                # 最後の '```' の位置を取得
                end_index = cleaned_text.rfind('```')
                
                # 有効なJSON部分を抽出
                if end_index > start_index:
                    json_string = cleaned_text[start_index:end_index].strip()
                else:
                    json_string = cleaned_text.strip() # ラッパーが不完全な場合は全体を試す
            except:
                json_string = cleaned_text.strip() # エラー時は全体を試す
        else:
            json_string = cleaned_text
            
        # 最終的なJSON文字列をパース
        raw_data = json.loads(json_string)
        
        # 構造の検証 (最低限のキーが存在するか)
        # 💡 検証するキーをより絞り込み、確実に存在すると期待されるキーに限定
        required_keys = ['overall_assessment', 'time_management_reflection']
        if not all(key in raw_data for key in required_keys):
            # 💡 エラーメッセージに、AIが出力したデータ構造を含めるとデバッグが容易になる
            raise ValueError(f"AI output is structurally incomplete. Missing keys: {required_keys}. Raw output keys: {list(raw_data.keys())}")

        return raw_data

    except APIError as e:
        raise ValueError(f"Gemini API通信エラーが発生しました: {e.message}")
    except Exception as e:
        raise ValueError(f"AI出力のパースに失敗しました: {e}")

# ----------------------------------------------------
# 💡 サマリーのDB更新関数
# ----------------------------------------------------

def update_summary_in_project(db: Session, project_id: int, summary_data: Dict[str, Any]):
    """生成されたサマリーをプロジェクトテーブルに保存する"""
    db_project: DBProject = db.get(DBProject, project_id)
    if not db_project:
        raise ValueError("Project not found for update.")

    # 辞書をJSONBとしてそのまま保存
    db_project.summary_data = summary_data
    db.add(db_project)
    db.commit()
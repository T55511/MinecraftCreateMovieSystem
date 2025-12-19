# app/schemas/ai.py

from pydantic import BaseModel, Field, ConfigDict # type: ignore
from typing import List, Optional

# --- AIが生成する質問リストの各項目 ---
class DiscussionQuestion(BaseModel):
    """トークフローの質問一つ一つに対応するスキーマ"""
    question_text: str = Field(..., description="クリエイターが話すべき具体的な質問文")
    target_time_min: float = Field(..., description="この質問に割り当てる目標トーク時間（分）")
    angle_type: str = Field(..., description="質問の角度（例: 共感, 疑問, 具体的体験）")
    model_config = ConfigDict(extra='ignore')  # 不要なフィールドを無視する設定

# --- AI生成データの全体構造 (scaffold_data) ---
class TalkScaffold(BaseModel):
    """トーク骨子全体を格納するスキーマ"""
    suggested_title: str = Field(..., description="AIが生成した推奨タイトル案")
    script_intro_text: str = Field(..., description="動画の導入部で話すべきフックとなる文章案")
    discussion_flow: List[DiscussionQuestion] = Field(..., description="AIが生成した8つの質問リスト")
    model_config = ConfigDict(extra='ignore')  # 不要なフィールドを無視する設定

# --- AIが生成するサムネイルコンセプトの構造 ---
class ThumbnailConcept(BaseModel):
    """サムネイルコンセプト全体を格納するスキーマ"""
    visual_theme: str = Field(..., description="視覚的なテーマ（例: 衝撃的な対比、クエスチョンマーク、未来的なUI）")
    required_elements: List[str] = Field(..., description="サムネイルに必ず含めるべきテキストまたはビジュアル要素（例: '視聴者を挑発する一文', '主要なキービジュアル'）")
    emotion_target: str = Field(..., description="視聴者に感じさせたい感情（例: 疑問, 驚愕, 解決への期待感）")
    concept_description: str = Field(..., description="サムネイルコンセプト全体の詳細な説明")

    # 💡 Pydantic v2 エラー対策の継続
    model_config = ConfigDict(extra='ignore')

# --- AIが生成するプロジェクトサマリーの構造 ---
class ProjectSummary(BaseModel):
    """プロジェクトの成果サマリーと反省点を格納するスキーマ"""
    # 成果サマリー
    overall_assessment: str = Field(..., description="プロジェクト全体に対する包括的な評価（成功、目標未達など）")
    key_achievements: List[str] = Field(..., description="プロジェクトで達成された主な成果")
    
    # 時間と習慣に関する反省点
    time_management_reflection: str = Field(..., description="実績時間データに基づいた時間管理の反省点と、次への具体的な改善策")
    habit_improvement_suggestion: str = Field(..., description="習慣化を促進するための具体的な行動提案（例: 収録作業は午前中に実施する、休憩を定期的に取るなど）")

    # 💡 Pydantic v2 エラー対策の継続
    model_config = ConfigDict(extra='ignore')
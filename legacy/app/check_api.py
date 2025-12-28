# check_api.py

import os
from google import genai
from google.genai.errors import APIError

# 1. 環境変数からキーを取得
API_KEY = os.getenv("GEMINI_API_KEY")

if not API_KEY or API_KEY == "DUMMY_KEY":
    print("❌ エラー: GEMINI_API_KEYが設定されていません。")
    exit()

print("✅ APIキーを環境変数から検出しました。")

# 2. クライアントの初期化
try:
    client = genai.Client(api_key=API_KEY)
    print("✅ Geminiクライアントの初期化に成功しました。")

    # 3. 簡単なAPI呼び出しを試みる
    print("🚀 API呼び出しをテストします...")
    response = client.models.generate_content(
        model='gemini-2.5-flash',
        contents="こんにちは。あなたは誰ですか？",
        config=genai.types.GenerateContentConfig(
            temperature=0.01  # 高速な応答のために温度を低く設定
        )
    )

    # 4. 応答を確認
    if response.text:
        print("\n🎉 APIキーは有効です。応答メッセージの一部:")
        print(response.text[:50].strip() + "...")
        print("---------------------------------")
    else:
        print("⚠️ 警告: 応答は得られましたが、テキストが空でした。サービスに問題がある可能性があります。")

except APIError as e:
    print(f"\n❌ 認証または権限エラーが発生しました。")
    print(f"   コード: {e.code}")
    print(f"   メッセージ: {e.message}")
    print("   -> **APIキーが無効であるか、APIが有効化されていません。**")
except Exception as e:
    print(f"\n❌ 予期せぬエラーが発生しました: {e}")
    print("   -> ネットワーク、またはその他の設定に問題があります。")
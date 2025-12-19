// 'use client';
// import { useState } from 'react';

// export default function PlannerPage() {
//   const [theme, setTheme] = useState('');
//   const [hookText, setHookText] = useState('');
//   const [selectedAngle, setSelectedAngle] = useState('1'); // マスタID想定

//   const angles = [
//     { id: '1', name: '矛盾と疑問', description: '世の中の当たり前に疑問を投げかける' },
//     { id: '2', name: '挫折と教訓', description: '失敗から得た学びを共有する' },
//     { id: '3', name: '未来と想像力', description: '一歩先の未来を予測し考察する' },
//   ];

//   const handleGenerate = () => {
//     // 💡 ここでバックエンドの generate_talk_scaffold APIを叩く
//     alert(`${theme} のトーク構成を生成します...`);
//   };

'use client';
import { useState } from 'react';
import api from '@/lib/api'; // 先ほど作った共通クライアント
import { useRouter } from 'next/navigation';

export default function PlannerPage() {
  const router = useRouter();
  const [theme, setTheme] = useState('');
  const [hookText, setHookText] = useState('');
  const [selectedAngle, setSelectedAngle] = useState('1');
  const [isGenerating, setIsGenerating] = useState(false);

  const angles = [
    { id: '1', name: '矛盾と疑問', description: '世の中の当たり前に疑問を投げかける' },
    { id: '2', name: '挫折と教訓', description: '失敗から得た学びを共有する' },
    { id: '3', name: '未来と想像力', description: '一歩先の未来を予測し考察する' },
  ];

  const handleGenerate = async () => {
    if (!theme || !hookText) {
      alert("テーマと導入フックを入力してください。");
      return;
    }

    setIsGenerating(true);
    try {
      // 1. プロジェクトを新規作成
      const projectRes = await api.post('/projects/', {
        theme: theme,
        input_angle_id: parseInt(selectedAngle),
        // 実際の実装に合わせて他の必須フィールドも送る
      });
      
      const projectId = projectRes.data.project_id;

      // 2. AIトーク骨子を生成（Geminiを叩く）
      // バックエンドの generate_talk_scaffold 関数を呼び出すエンドポイントを想定
      await api.post(`/projects/${projectId}/scaffold`);

      alert("AI構成の生成が完了しました！スタジオに移動します。");
      
      // 3. 生成された構成を持ってStudio画面へ移動
      router.push(`/studio?projectId=${projectId}`);
      
    } catch (error) {
      console.error("生成エラー:", error);
      alert("AI生成中にエラーが発生しました。バックエンドのログを確認してください。");
    } finally {
      setIsGenerating(false);
    }
  };

  return (
    <div className="p-10 max-w-5xl mx-auto">
      <header className="mb-10">
        <h1 className="text-3xl font-black text-slate-800">New Project</h1>
        <p className="text-slate-500">トークの核となる「導入フック」を固定し、AIと構成を練ります。</p>
      </header>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        {/* 左側：入力フォーム */}
        <div className="lg:col-span-2 space-y-8">
          <section className="bg-white p-8 rounded-[32px] shadow-sm border border-slate-100">
            <label className="block text-sm font-bold text-slate-400 uppercase tracking-widest mb-4">Step 1: トークテーマ</label>
            <input 
              type="text"
              value={theme}
              onChange={(e) => setTheme(e.target.value)}
              placeholder="例：AI時代の労働の価値について"
              className="w-full text-2xl font-bold p-0 border-none focus:ring-0 placeholder:text-slate-200"
            />
          </section>

          <section className="bg-white p-8 rounded-[32px] shadow-sm border border-slate-100">
            <label className="block text-sm font-bold text-slate-400 uppercase tracking-widest mb-4">Step 2: 導入フック（主張の固定）</label>
            <textarea 
              rows={4}
              value={hookText}
              onChange={(e) => setHookText(e.target.value)}
              placeholder="最初の90秒で語る感情や主張を入力してください。これがAI生成の核になります。"
              className="w-full text-lg p-0 border-none focus:ring-0 bg-transparent placeholder:text-slate-200 resize-none"
            />
          </section>
        </div>

        {/* 右側：設定と実行 */}
        <div className="space-y-6">
          <section className="bg-slate-900 text-white p-8 rounded-[32px] shadow-xl">
            <label className="block text-xs font-bold text-slate-500 uppercase tracking-widest mb-6">Step 3: アングル選択</label>
            <div className="space-y-3">
              {angles.map((angle) => (
                <button
                  key={angle.id}
                  onClick={() => setSelectedAngle(angle.id)}
                  className={`w-full text-left p-4 rounded-2xl border-2 transition-all ${
                    selectedAngle === angle.id 
                    ? 'border-emerald-500 bg-emerald-500/10' 
                    : 'border-slate-800 hover:border-slate-700'
                  }`}
                >
                  <div className="font-bold">{angle.name}</div>
                  <div className="text-xs text-slate-400">{angle.description}</div>
                </button>
              ))}
            </div>

            <button 
                onClick={handleGenerate}
                disabled={isGenerating}
                className={`w-full mt-8 py-4 rounded-2xl font-black text-lg transition-all shadow-lg ${
                    isGenerating ? 'bg-slate-700 cursor-not-allowed' : 'bg-emerald-500 hover:bg-emerald-400 text-white shadow-emerald-900/20'
                }`}
                >
                {isGenerating ? 'AI思考中...' : '構成を自動生成する'}
    </button>
          </section>
        </div>
      </div>
    </div>
  );
}
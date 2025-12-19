'use client';
import { useState } from 'react';

export default function StudioPage() {
  // 仕様書の「雑談フローリスト（8個の質問）」を想定
  const [questions] = useState([
    "最近、何かに矛盾を感じたことはありますか？",
    "その矛盾を解決するために、どんな行動をとりましたか？",
    "労働の価値について、あなたの考えを教えてください。",
    "人間性と思考の境界線はどこにあると思いますか？",
    "未来の想像力が欠如した世界はどうなると思いますか？",
    "自己と感情を切り離して考えたことはありますか？",
    "教訓を得るために支払った最大の代償は何ですか？",
    "最後に、このテーマの結論を30秒でまとめてください。"
  ]);
  
  const [currentIndex, setCurrentIndex] = useState(0);

  const handleNext = () => {
    if (currentIndex < questions.length - 1) {
      // 💡 ここでバックエンドの stop_timer/start_timer を呼ぶ予定
      setCurrentIndex(currentIndex + 1);
    } else {
      alert("すべての収録が完了しました！");
    }
  };

  return (
    <div className="p-12 flex flex-col items-center justify-center min-h-[80vh]">
      <div className="max-w-4xl w-full bg-white p-20 rounded-[50px] shadow-[0_20px_60px_-15px_rgba(0,0,0,0.1)] border border-slate-100 relative overflow-hidden">
        {/* 背景の装飾的な数字 */}
        <div className="absolute top-[-20px] left-[-20px] text-[200px] font-black text-slate-50 opacity-[0.03] pointer-events-none">
          {currentIndex + 1}
        </div>

        <div className="relative">
          <div className="flex items-center justify-between mb-12">
            <span className="px-4 py-1 bg-emerald-100 text-emerald-700 rounded-full text-xs font-black tracking-widest">
              STEP {currentIndex + 1} / {questions.length}
            </span>
            <div className="flex gap-1">
              {questions.map((_, i) => (
                <div key={i} className={`h-1 w-6 rounded-full ${i <= currentIndex ? 'bg-emerald-500' : 'bg-slate-100'}`} />
              ))}
            </div>
          </div>
          
          <h2 className="text-5xl font-extrabold text-slate-800 mb-16 leading-[1.3] min-h-[200px] flex items-center">
            {questions[currentIndex]}
          </h2>

          <button 
            onClick={handleNext}
            className="w-full bg-slate-900 text-white py-8 rounded-3xl font-black text-2xl hover:bg-emerald-600 transition-all transform hover:-translate-y-1 active:scale-95 shadow-2xl shadow-slate-200"
          >
            {currentIndex === questions.length - 1 ? '収録完了' : '回答完了、次の質問へ'}
          </button>
        </div>
      </div>
    </div>
  );
}
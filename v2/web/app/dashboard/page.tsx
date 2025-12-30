"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import type { Workload } from "lib/api";
import { getWorkload } from "lib/api";

export default function DashboardPage() {
  const [w, setW] = useState<Workload | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    (async () => {
      try {
        const data = await getWorkload();
        setW(data);
      } catch (e: any) {
        setError(e?.message ?? "Failed");
      }
    })();
  }, []);

  const percent = w?.load_percent ?? 0;
  const label =
    percent >= 100 ? "過負荷（要調整）" :
    percent >= 80 ? "高め（注意）" :
    percent >= 50 ? "適正" :
    "余裕あり";

  return (
    <>
      <div className="row" style={{ justifyContent: "space-between", marginBottom: 12 }}>
        <div style={{ fontWeight: 800, fontSize: 18 }}>Dashboard</div>
        <Link href="/projects">Projectsへ</Link>
      </div>

      <div className="card">
        <div style={{ fontWeight: 700 }}>週間負荷（直近7日）</div>

        {error && <div style={{ color: "tomato", marginTop: 10 }}>{error}</div>}
        {!w ? (
          <div style={{ marginTop: 10 }}>読み込み中...</div>
        ) : (
          <>
            <div className="small" style={{ marginTop: 8 }}>{label}</div>

            <div style={{ marginTop: 10 }}>
              <div className="small">実績：{w.actual_minutes_7d} 分</div>
              <div className="small">標準：{w.estimated_minutes_7d} 分</div>
              <div className="small">負荷：{w.load_percent}%</div>
            </div>

            <div style={{ height: 10, background: "rgba(128,128,128,0.25)", borderRadius: 6, overflow: "hidden", marginTop: 10 }}>
              <div style={{ width: `${Math.min(100, percent)}%`, height: "100%", background: "deepskyblue" }} />
            </div>

            <div className="small" style={{ marginTop: 8 }}>
              ※ 直近7日で作業したプロジェクトを母集団に集計
            </div>
          </>
        )}
      </div>
    </>
  );
}

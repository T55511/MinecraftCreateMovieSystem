"use client";

import { useEffect, useMemo, useState } from "react";
import type { Project } from "lib/api";
import { createProject, listProjects } from "lib/api";
import Link from "next/link";

function formatDate(d: string | null) {
  if (!d) return "未設定";
  return d;
}

export default function ProjectsPage() {
  const [projects, setProjects] = useState<Project[]>([]);
  const [loading, setLoading] = useState(true);
  const [creating, setCreating] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const [theme, setTheme] = useState("");
  const [dueDate, setDueDate] = useState<string>("");

  async function refresh() {
    setError(null);
    setLoading(true);
    try {
      const data = await listProjects();
      setProjects(data);
    } catch (e: any) {
      setError(e?.message ?? "Unknown error");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    refresh();
  }, []);

  const canCreate = useMemo(() => theme.trim().length > 0 && !creating, [theme, creating]);

  async function onCreate() {
    if (!canCreate) return;
    setCreating(true);
    setError(null);
    try {
      await createProject({
        theme: theme.trim(),
        due_date: dueDate ? dueDate : null
      });
      setTheme("");
      setDueDate("");
      await refresh();
    } catch (e: any) {
      setError(e?.message ?? "Failed to create");
    } finally {
      setCreating(false);
    }
  }

  return (
    <>
      <h1>Projects（v2）</h1>

      <div className="card">
        <div className="row">
          <input
            style={{ minWidth: 280 }}
            placeholder="プロジェクト名"
            value={theme}
            onChange={(e) => setTheme(e.target.value)}
          />
          <input type="date" value={dueDate} onChange={(e) => setDueDate(e.target.value)} />
          <button onClick={onCreate} disabled={!canCreate}>
            {creating ? "作成中..." : "作成"}
          </button>
          <button onClick={refresh} disabled={loading || creating}>
            {loading ? "更新中..." : "更新"}
          </button>
        </div>
        <div className="small">表示は最小：プロジェクト名 / 完了予定日</div>
        {error && <div style={{ marginTop: 10, color: "tomato" }}>{error}</div>}
      </div>

      {loading ? (
        <div>読み込み中...</div>
      ) : projects.length === 0 ? (
        <div>プロジェクトがありません。上のフォームで作成してください。</div>
      ) : (
        <div>
            {projects.map((p) => (
            <Link
                key={p.project_id}
                href={`/projects/${p.project_id}`}
                style={{ textDecoration: "none", color: "inherit" }}
            >
                <div className="card" style={{ cursor: "pointer" }}>
                <div style={{ fontWeight: 700 }}>{p.theme}</div>
                <div className="small">完了予定日：{formatDate(p.due_date)}</div>
                {/* <div className="small">project_id: {p.project_id}</div> */}
                <div className="small" style={{ marginTop: 6 }}>
                  進捗：{Math.round(p.progress_rate)}%
                </div>

                <div
                  style={{
                    height: 6,
                    background: "rgba(128,128,128,0.25)",
                    borderRadius: 4,
                    marginTop: 4,
                    overflow: "hidden",
                  }}
                >
                  <div
                    style={{
                      width: `${p.progress_rate}%`,
                      height: "100%",
                      background: "limegreen",
                    }}
                  />
                </div>
                <div className="small">クリックで詳細へ</div>
                </div>
            </Link>
            ))}
        </div>
        )}
    </>
    );
}

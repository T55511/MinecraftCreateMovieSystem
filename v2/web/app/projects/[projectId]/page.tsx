"use client";

import { useEffect, useMemo, useState } from "react";
import { useParams } from "next/navigation";
import Link from "next/link";
import type { ProjectDetail, ProjectTask, ChecklistItem } from "lib/api";
import { getProject, listProjectTasks, patchProjectTaskStatus, getTaskChecklist, putTaskChecklist } from "lib/api";
import { startTaskTimer, stopTaskTimer, getTaskTimerStatus } from "lib/api";


function formatDate(d: string | null | undefined) {
  if (!d) return "未設定";
  return d;
}

function groupByStatus(tasks: ProjectTask[]) {
  const g: Record<string, ProjectTask[]> = { "未着手": [], "進行中": [], "完了": [] };
  for (const t of tasks) (g[t.status] ??= []).push(t);
  return g;
}


export default function ProjectDetailPage() {
  const params = useParams();
  const projectId = useMemo(() => Number(params.projectId), [params.projectId]);

  const [project, setProject] = useState<ProjectDetail | null>(null);
  const [tasks, setTasks] = useState<ProjectTask[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const grouped = groupByStatus(tasks);
  const [draggingTaskId, setDraggingTaskId] = useState<number | null>(null);
  const [selectedTask, setSelectedTask] = useState<ProjectTask | null>(null);
  const [checklist, setChecklist] = useState<ChecklistItem[]>([]);
  const [modalLoading, setModalLoading] = useState(false);
  const [timerRunning, setTimerRunning] = useState(false);
  const [elapsedMin, setElapsedMin] = useState<number | null>(null);

  function canMove(from: string, to: string) {
    // 今のAPI側ルールに合わせる（未着手→完了、完了→未着手は禁止）
    if (from === "未着手" && to === "完了") return false;
    if (from === "完了" && to === "未着手") return false;
    return true;
  }

    async function moveTask(t: ProjectTask, next: "未着手" | "進行中" | "完了") {
      try {
        setLoading(true);
        setError(null);
        await patchProjectTaskStatus(projectId, t.project_task_id, next);
        await refresh();
      } catch (e: any) {
        setError(e?.message ?? "Failed to move");
        setLoading(false);
      }
    }
  
    async function moveTaskByDrop(task: ProjectTask, toStatus: "未着手" | "進行中" | "完了") {
      if (!canMove(task.status, toStatus)) {
        setError(`この移動はできません: ${task.status} → ${toStatus}`);
        return;
      }
      try {
        setLoading(true);
        setError(null);
        await patchProjectTaskStatus(projectId, task.project_task_id, toStatus);
        await refresh();
      } catch (e: any) {
        setError(e?.message ?? "Failed to move");
        setLoading(false);
      } finally {
        setDraggingTaskId(null);
      }
    }


    async function refresh() {
        setLoading(true);
        setError(null);
        try {
        const [p, t] = await Promise.all([
            getProject(projectId),
            listProjectTasks(projectId),
        ]);
        setProject(p);
        setTasks(t);
        } catch (e: any) {
        setError(e?.message ?? "Unknown error");
        } finally {
        setLoading(false);
        }
    }

  useEffect(() => {
    if (!Number.isFinite(projectId) || projectId <= 0) return;
    refresh();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [projectId]);

  return (
    <>
      <div className="row" style={{ justifyContent: "space-between", marginBottom: 12 }}>
        <Link href="/projects">← Projectsへ戻る</Link>
        <button onClick={refresh} disabled={loading}>
          {loading ? "更新中..." : "更新"}
        </button>
      </div>

      <div className="card">
        <div style={{ fontWeight: 700, marginBottom: 10 }}>サブタスク（Kanban）</div>

        <div style={{ display: "grid", gridTemplateColumns: "repeat(3, 1fr)", gap: 12 }}>
            {(["未着手", "進行中", "完了"] as const).map((col) => (
            <div
              key={col}
              className="card"
              onDragOver={(e) => {
                e.preventDefault(); // これが無いと drop できない
                e.dataTransfer.dropEffect = "move";
              }}
              onDrop={(e) => {
                e.preventDefault();
                const taskIdStr = e.dataTransfer.getData("text/plain");
                const taskId = Number(taskIdStr);
                const task = tasks.find((x) => x.project_task_id === taskId);
                if (!task) return;
                moveTaskByDrop(task, col);
              }}
              style={{
                marginBottom: 0,
                outline: draggingTaskId ? "2px dashed rgba(128,128,128,0.45)" : "none",
                background: draggingTaskId ? "rgba(128,128,128,0.06)" : "transparent",
              }}
            >
            <div style={{ fontWeight: 800, marginBottom: 8 }}>{col}</div>
                {grouped[col].length === 0 ? (
                <div className="small">（なし）</div>
                ) : (
                grouped[col].map((t) => (
                  <div
                    key={t.project_task_id}
                    className="card"
                    draggable
                    onDragStart={(e) => {
                      setDraggingTaskId(t.project_task_id);
                      e.dataTransfer.setData("text/plain", String(t.project_task_id));
                      e.dataTransfer.effectAllowed = "move";
                    }}
                    onDragEnd={() => setDraggingTaskId(null)}
                    onClick={async () => {
                      if (draggingTaskId) return;

                      setSelectedTask(t);
                      setModalLoading(true);
                      try {
                        const [items, status] = await Promise.all([
                          getTaskChecklist(projectId, t.project_task_id),
                          getTaskTimerStatus(projectId, t.project_task_id),
                        ]);
                        setChecklist(items);
                        setTimerRunning(status.running);
                        setElapsedMin(status.elapsed_min ?? null);
                      } catch (e: any) {
                        setError(e?.message ?? "Failed to load modal data");
                      } finally {
                        setModalLoading(false);
                      }
                    }}
                    style={{
                      marginBottom: 8,
                      cursor: "grab",
                      opacity: draggingTaskId === t.project_task_id ? 0.6 : 1,
                    }}
                  >
                    <div style={{ fontWeight: 700 }}>{t.task_name}</div>
                    <div className="small">est: {t.est_time_min} / actual: {t.actual_time_min.toFixed(1)}</div>
                    <div className="small" style={{ marginTop: 6 }}>status: {t.status}</div>
                  </div>
                ))
              )}
            </div>
            ))}
        </div>

        <div className="small" style={{ marginTop: 10 }}>
            ※D&Dは次段階で追加。まずは状態更新が確実に動くことを優先。
        </div>
        </div>

      <div className="card">
        <div style={{ fontWeight: 700, marginBottom: 10 }}>サブタスク一覧（Table）</div>

        {loading ? (
          <div>読み込み中...</div>
        ) : tasks.length === 0 ? (
          <div>サブタスクがありません</div>
        ) : (
          <table style={{ width: "100%", borderCollapse: "collapse" }}>
            <thead>
              <tr>
                <th style={{ textAlign: "left", padding: 8 }}>順</th>
                <th style={{ textAlign: "left", padding: 8 }}>タスク名</th>
                <th style={{ textAlign: "left", padding: 8 }}>状態</th>
                <th style={{ textAlign: "left", padding: 8 }}>見積</th>
                <th style={{ textAlign: "left", padding: 8 }}>実績</th>
              </tr>
            </thead>
            <tbody>
              {tasks.map((t) => (
                <tr key={t.project_task_id}>
                  <td style={{ padding: 8 }}>{t.sort_order}</td>
                  <td style={{ padding: 8, fontWeight: 650 }}>{t.task_name}</td>
                  <td style={{ padding: 8 }}>{t.status}</td>
                  <td style={{ padding: 8 }}>{t.est_time_min} min</td>
                  <td style={{ padding: 8 }}>{t.actual_time_min.toFixed(1)} min</td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>

      {selectedTask && (
      <div
        onClick={() => setSelectedTask(null)}
        style={{
          position: "fixed",
          inset: 0,
          background: "rgba(0,0,0,0.5)",
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
          padding: 16,
          zIndex: 50,
        }}
      >
        <div
          onClick={(e) => e.stopPropagation()}
          className="card"
          style={{
            width: "min(720px, 96vw)", 
            maxHeight: "85vh", 
            overflow: "auto", 
            background: "rgb(20,20,20)", // rgba(0,0,0,0.65)
          }}
        >
          <div className="row" style={{ justifyContent: "space-between" }}>
            <div style={{ fontWeight: 800, fontSize: 16 }}>{selectedTask.task_name}</div>
            <button onClick={() => setSelectedTask(null)}>閉じる</button>
          </div>

          <div className="small" style={{ marginTop: 6 }}>
            status: {selectedTask.status}
          </div>

          <div style={{ marginTop: 14, fontWeight: 700 }}>Checklist</div>

          {modalLoading ? (
            <div style={{ marginTop: 10 }}>読み込み中...</div>
          ) : checklist.length === 0 ? (
            <div className="small" style={{ marginTop: 10 }}>チェック項目なし（このタスクはガードなし）</div>
          ) : (
            <div style={{ marginTop: 10 }}>
              {checklist.map((c) => (
                <label key={c.check_item_id} className="row" style={{ gap: 10, marginBottom: 8 }}>
                  <input
                    type="checkbox"
                    checked={c.is_checked}
                    onChange={async (e) => {
                      const next = checklist.map(x =>
                        x.check_item_id === c.check_item_id ? { ...x, is_checked: e.target.checked } : x
                      );
                      setChecklist(next);
                      try {
                        const saved = await putTaskChecklist(projectId, selectedTask.project_task_id, next);
                        setChecklist(saved);
                      } catch (err: any) {
                        setError(err?.message ?? "Failed to save checklist");
                      }
                    }}
                  />
                  <span>{c.label}</span>
                </label>
              ))}
            </div>
          )}

          <div style={{ marginTop: 16 }}>
            <div style={{ fontWeight: 700 }}>Timer</div>

            <div className="row" style={{ marginTop: 8 }}>
              {!timerRunning ? (
                <button
                  onClick={async () => {
                    try {
                      await startTaskTimer(projectId, selectedTask.project_task_id);
                      setTimerRunning(true);
                    } catch (e: any) {
                      setError(e?.message ?? "Failed to start timer");
                    }
                  }}
                >
                  ▶ 開始
                </button>
              ) : (
                <button
                  onClick={async () => {
                    try {
                      await stopTaskTimer(projectId, selectedTask.project_task_id);
                      setTimerRunning(false);
                      await refresh(); // 実績時間を即反映
                    } catch (e: any) {
                      setError(e?.message ?? "Failed to stop timer");
                    }
                  }}
                >
                  ■ 停止
                </button>
              )}
            </div>
          </div>

          <div className="row" style={{ justifyContent: "flex-end", marginTop: 14 }}>
            <button
              onClick={async () => {
                // 完了にする（ガードはAPI側が判定）
                try {
                  setLoading(true);
                  setError(null);
                  await patchProjectTaskStatus(projectId, selectedTask.project_task_id, "完了");
                  setSelectedTask(null);
                  await refresh();
                } catch (e: any) {
                  setError(e?.message ?? "Failed to complete");
                  setLoading(false);
                }
              }}
            >
              完了にする
            </button>
          </div>
        </div>
      </div>
    )}
    </>
  );
}

export type Project = {
    project_id: number;
    theme: string;
    due_date: string | null; // FastAPIのdateは "YYYY-MM-DD"
    progress_rate: number;
};

const API_BASE = process.env.NEXT_PUBLIC_API_BASE ?? "http://localhost:8010";

export async function listProjects(): Promise<Project[]> {
    console.log("API_BASE:", API_BASE);
    const res = await fetch(`${API_BASE}/v2/projects`, { cache: "no-store" });
    if (!res.ok) throw new Error(`Failed to list projects: ${res.status}`);
    return res.json();
}

export async function createProject(input: { theme: string; due_date?: string | null }): Promise<Project> {
    console.log("API_BASE:", API_BASE);
    const res = await fetch(`${API_BASE}/v2/projects`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
        theme: input.theme,
        due_date: input.due_date ?? null
    })
    });
    if (!res.ok) throw new Error(`Failed to create project: ${res.status}`);
    return res.json();
}

export type ProjectDetail = {
    project_id: number;
    theme: string;
    due_date: string | null;
    publish_scheduled_at?: string | null;
    memo?: string | null;
};

export type ProjectTask = {
    project_task_id: number;
    project_id: number;
    task_template_id: number;
    task_name: string;
    status: string;
    est_time_min: number;
    actual_time_min: number;
    sort_order: number;
    is_active: boolean;
};

export async function getProject(projectId: number): Promise<ProjectDetail> {
    const res = await fetch(`${API_BASE}/v2/projects/${projectId}`, { cache: "no-store" });
    if (!res.ok) throw new Error(`Failed to get project: ${res.status}`);
    return res.json();
}

export async function listProjectTasks(projectId: number): Promise<ProjectTask[]> {
    const res = await fetch(`${API_BASE}/v2/projects/${projectId}/tasks/list`, { cache: "no-store" });
    if (!res.ok) throw new Error(`Failed to list project tasks: ${res.status}`);
    return res.json();
}

export async function patchProjectTaskStatus(projectId: number, projectTaskId: number, status: string): Promise<ProjectTask> {
  const res = await fetch(`${API_BASE}/v2/projects/${projectId}/tasks/${projectTaskId}`, {
    method: "PATCH",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ status })
  });
  if (!res.ok) {
    const text = await res.text().catch(() => "");
    throw new Error(`Failed to patch task: ${res.status} ${text}`);
  }
  return res.json();
}

export type ChecklistItem = {
  check_item_id: number;
  label: string;
  is_checked: boolean;
};

export async function getTaskChecklist(projectId: number, projectTaskId: number): Promise<ChecklistItem[]> {
  const res = await fetch(`${API_BASE}/v2/projects/${projectId}/tasks/${projectTaskId}/checklist`, { cache: "no-store" });
  if (!res.ok) throw new Error(`Failed to get checklist: ${res.status}`);
  return res.json();
}

export async function putTaskChecklist(projectId: number, projectTaskId: number, items: ChecklistItem[]): Promise<ChecklistItem[]> {
  const res = await fetch(`${API_BASE}/v2/projects/${projectId}/tasks/${projectTaskId}/checklist`, {
    method: "PUT",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(items.map(i => ({ check_item_id: i.check_item_id, is_checked: i.is_checked })))
  });
  if (!res.ok) {
    const text = await res.text().catch(() => "");
    throw new Error(`Failed to update checklist: ${res.status} ${text}`);
  }
  return res.json();
}

export async function startTaskTimer(projectId: number, taskId: number) {
  const res = await fetch(
    `${API_BASE}/v2/projects/${projectId}/tasks/${taskId}/timer/start`,
    { method: "POST" }
  );
  if (!res.ok) throw new Error("Failed to start timer");
}

export async function stopTaskTimer(projectId: number, taskId: number) {
  const res = await fetch(
    `${API_BASE}/v2/projects/${projectId}/tasks/${taskId}/timer/stop`,
    { method: "POST" }
  );
  if (!res.ok) throw new Error("Failed to stop timer");
  return res.json();
}

export async function getTaskTimerStatus(projectId: number, taskId: number): Promise<{running: boolean; elapsed_min?: number}> {
  const res = await fetch(`${API_BASE}/v2/projects/${projectId}/tasks/${taskId}/timer/status`, { cache: "no-store" });
  if (!res.ok) throw new Error(`Failed to get timer status: ${res.status}`);
  return res.json();
}

export type Workload = {
  from: string;
  to: string;
  actual_minutes_7d: number;
  estimated_minutes_7d: number;
  load_percent: number;
};

export async function getWorkload(): Promise<Workload> {
  const res = await fetch(`${API_BASE}/v2/dashboard/workload`, { cache: "no-store" });
  if (!res.ok) throw new Error(`Failed to get workload: ${res.status}`);
  return res.json();
}


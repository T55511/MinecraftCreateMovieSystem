// src/lib/auditLogs.ts
export type AuditLevel = "INFO" | "WARNING" | "ERROR";

export type AuditEvent = {
  timestamp: string;
  level: AuditLevel;
  actor: string;
  action: string;
  target_type: string;
  target_id?: string | null;
  summary: string;
  detail?: Record<string, any> | null;
};

export type AuditLogListResponse = {
  total: number;
  items: AuditEvent[];
};

export type AuditLogQuery = {
  level?: AuditLevel | "";
  q?: string;
  time_from?: string; // ISO8601
  time_to?: string;   // ISO8601
  limit?: number;
  offset?: number;
};

function buildQuery(params: AuditLogQuery): string {
  const sp = new URLSearchParams();
  if (params.level) sp.set("level", params.level);
  if (params.q) sp.set("q", params.q);
  if (params.time_from) sp.set("time_from", params.time_from);
  if (params.time_to) sp.set("time_to", params.time_to);
  if (typeof params.limit === "number") sp.set("limit", String(params.limit));
  if (typeof params.offset === "number") sp.set("offset", String(params.offset));
  return sp.toString();
}

export async function fetchAuditLogs(params: AuditLogQuery): Promise<AuditLogListResponse> {
  const base = process.env.NEXT_PUBLIC_API_BASE;
  if (!base) throw new Error("NEXT_PUBLIC_API_BASE_URL is not set");

  const qs = buildQuery(params);
  const url = `${base}/admin/audit-logs${qs ? `?${qs}` : ""}`;

  const res = await fetch(url, { cache: "no-store" });
  if (!res.ok) {
    const text = await res.text().catch(() => "");
    throw new Error(`Failed to fetch audit logs: ${res.status} ${text}`);
  }
  return res.json();
}

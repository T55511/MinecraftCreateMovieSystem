"use client";

import React, { useEffect, useMemo, useState } from "react";
import { fetchAuditLogs, type AuditEvent, type AuditLevel } from "lib/auditLogs";

type FetchState =
  | { kind: "idle" }
  | { kind: "loading" }
  | { kind: "loaded"; total: number; items: AuditEvent[] }
  | { kind: "error"; message: string };

const PAGE_SIZE = 200;

function formatLocal(tsIso: string): string {
  const d = new Date(tsIso);
  if (Number.isNaN(d.getTime())) return tsIso;
  return d.toLocaleString();
}

function toIsoFromDatetimeLocal(v: string): string {
  if (!v) return "";
  const d = new Date(v);
  return Number.isNaN(d.getTime()) ? "" : d.toISOString();
}

function sameEvent(a: AuditEvent | null, b: AuditEvent): boolean {
  if (!a) return false;
  // timestamp+action+summaryあたりで十分（同一判定）
  return a.timestamp === b.timestamp && a.action === b.action && a.summary === b.summary && a.level === b.level;
}

function pickDetail(detail: AuditEvent["detail"]): { main: Array<{ label: string; value: string }>; others: Array<{ label: string; value: string }> } {
  const d = (detail ?? {}) as Record<string, any>;

  // よく出るキーを「必要最低限」として優先表示
  const preferredKeys: Array<[string, string]> = [
    ["version", "version"],
    ["change_note", "change_note"],
    ["project_id", "project_id"],
    ["template_id", "template_id"],
    ["template_version", "template_version"],
    ["subtask_template_id", "subtask_template_id"],
    ["subtask_template_version", "subtask_template_version"],
    ["status_key", "status_key"],
    ["reason", "reason"],
    ["path", "path"],
    ["method", "method"],
  ];

  const used = new Set<string>();
  const main: Array<{ label: string; value: string }> = [];

  for (const [key, label] of preferredKeys) {
    if (d[key] === undefined || d[key] === null || d[key] === "") continue;
    main.push({ label, value: String(d[key]) });
    used.add(key);
  }

  // 残りは「その他」として最小表示（括弧/JSONは出さない）
  const others: Array<{ label: string; value: string }> = [];
  for (const key of Object.keys(d)) {
    if (used.has(key)) continue;
    const v = d[key];
    if (v === undefined || v === null || v === "") continue;

    // オブジェクト/配列は「必要最低限」方針なので文字列化は抑制
    // ただしプリミティブは出す
    if (typeof v === "string" || typeof v === "number" || typeof v === "boolean") {
      others.push({ label: key, value: String(v) });
    } else {
      // 複雑型は存在だけ示す（括弧など出さない）
      others.push({ label: key, value: "(complex value)" });
    }
  }

  return { main, others };
}

export default function AuditLogsPage() {
  const [level, setLevel] = useState<AuditLevel | "">("");
  const [q, setQ] = useState("");
  const [timeFrom, setTimeFrom] = useState("");
  const [timeTo, setTimeTo] = useState("");
  const [offset, setOffset] = useState(0);

  const [state, setState] = useState<FetchState>({ kind: "idle" });
  const [selected, setSelected] = useState<AuditEvent | null>(null);

  const time_from_iso = useMemo(() => toIsoFromDatetimeLocal(timeFrom), [timeFrom]);
  const time_to_iso = useMemo(() => toIsoFromDatetimeLocal(timeTo), [timeTo]);

  async function load(nextOffset: number) {
    setState({ kind: "loading" });
    try {
      const data = await fetchAuditLogs({
        level,
        q: q.trim() ? q.trim() : undefined,
        time_from: time_from_iso || undefined,
        time_to: time_to_iso || undefined,
        limit: PAGE_SIZE,
        offset: nextOffset,
      });
      setState({ kind: "loaded", total: data.total, items: data.items });
    } catch (e: any) {
      setState({ kind: "error", message: e?.message ?? "Unknown error" });
    }
  }

  useEffect(() => {
    load(0);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  function onSearchSubmit(e: React.FormEvent) {
    e.preventDefault();
    setOffset(0);
    load(0);
  }

  const loaded = state.kind === "loaded" ? state : null;
  const total = loaded?.total ?? 0;
  const items = loaded?.items ?? [];

  const page = Math.floor(offset / PAGE_SIZE) + 1;
  const maxPage = Math.max(1, Math.ceil(total / PAGE_SIZE));
  const canPage = state.kind === "loaded" && total > PAGE_SIZE;
  const canPrev = canPage && offset > 0;
  const canNext = canPage && offset + PAGE_SIZE < total;

  function goPrev() {
    const next = Math.max(0, offset - PAGE_SIZE);
    setOffset(next);
    load(next);
  }
  function goNext() {
    const next = offset + PAGE_SIZE;
    if (next >= total) return;
    setOffset(next);
    load(next);
  }

  return (
    <div style={{ minHeight: "calc(100vh - 32px)", padding: 24, display: "flex", justifyContent: "center" }}>
      <div style={{ width: "min(1100px, 100%)", display: "grid", gap: 16, color: "#eaeaea" }}>
        <header style={{ display: "flex", alignItems: "baseline", gap: 12 }}>
          <h1 style={{ fontSize: 22, fontWeight: 800, margin: 0 }}>監査ログ</h1>
          <span style={{ fontSize: 12, opacity: 0.75 }}>クリックで詳細（モーダル）</span>
        </header>

        <form
          onSubmit={onSearchSubmit}
          style={{
            border: "1px solid rgba(255,255,255,0.12)",
            borderRadius: 12,
            padding: 12,
            background: "rgba(0,0,0,0.35)",
            display: "grid",
            gridTemplateColumns: "140px 1fr 180px 180px 110px",
            gap: 10,
            alignItems: "end",
          }}
        >
          <Field label="レベル">
            <select value={level} onChange={(e) => setLevel(e.target.value as any)} style={inputStyle}>
              <option value="">すべて</option>
              <option value="INFO">INFO</option>
              <option value="WARNING">WARNING</option>
              <option value="ERROR">ERROR</option>
            </select>
          </Field>

          <Field label="検索（summary/actor/action/target）">
            <input value={q} onChange={(e) => setQ(e.target.value)} placeholder="例：CREATE / プロジェクト / ERROR" style={inputStyle} />
          </Field>

          <Field label="開始">
            <input type="datetime-local" value={timeFrom} onChange={(e) => setTimeFrom(e.target.value)} style={inputStyle} />
          </Field>

          <Field label="終了">
            <input type="datetime-local" value={timeTo} onChange={(e) => setTimeTo(e.target.value)} style={inputStyle} />
          </Field>

          <button type="submit" style={primaryButtonStyle}>
            検索
          </button>

          <div style={{ gridColumn: "1 / -1", display: "flex", gap: 10, alignItems: "center", marginTop: 6 }}>
            <button type="button" onClick={() => load(offset)} disabled={state.kind === "loading"} style={secondaryButtonStyle}>
              再読み込み
            </button>

            {canPage && (
              <div style={{ marginLeft: "auto", display: "flex", gap: 10, alignItems: "center" }}>
                <button type="button" onClick={goPrev} disabled={!canPrev} style={secondaryButtonStyle}>
                  前へ
                </button>
                <span style={{ fontSize: 12, opacity: 0.9 }}>
                  {page}/{maxPage}（total: {total}）
                </span>
                <button type="button" onClick={goNext} disabled={!canNext} style={secondaryButtonStyle}>
                  次へ
                </button>
              </div>
            )}
          </div>
        </form>

        {state.kind === "error" && (
          <div style={errorBoxStyle}>
            <div style={{ fontWeight: 800, marginBottom: 6 }}>取得に失敗</div>
            <div style={{ whiteSpace: "pre-wrap", fontSize: 13 }}>{state.message}</div>
          </div>
        )}

        <div
          style={{
            border: "1px solid rgba(255,255,255,0.12)",
            borderRadius: 12,
            overflow: "hidden",
            background: "rgba(0,0,0,0.35)",
          }}
        >
          <div
            style={{
              display: "grid",
              gridTemplateColumns: "180px 90px 240px 1fr",
              padding: "10px 12px",
              fontSize: 12,
              fontWeight: 800,
              background: "rgba(255,255,255,0.06)",
              borderBottom: "1px solid rgba(255,255,255,0.10)",
            }}
          >
            <div>時刻</div>
            <div>Lv</div>
            <div>Action</div>
            <div>Summary</div>
          </div>

          {state.kind === "loading" && <div style={{ padding: 12, fontSize: 13, opacity: 0.9 }}>読み込み中...</div>}
          {state.kind === "loaded" && items.length === 0 && <div style={{ padding: 12, fontSize: 13, opacity: 0.9 }}>該当ログなし</div>}

          {state.kind === "loaded" &&
            items.map((evt, idx) => {
              const active = sameEvent(selected, evt);
              return (
                <button
                  key={`${evt.timestamp}-${idx}`}
                  onClick={() => setSelected(evt)}
                  style={{
                    width: "100%",
                    textAlign: "left",
                    display: "grid",
                    gridTemplateColumns: "180px 90px 240px 1fr",
                    padding: "10px 12px",
                    border: "none",
                    borderTop: idx === 0 ? "none" : "1px solid rgba(255,255,255,0.08)",
                    cursor: "pointer",
                    color: "#eaeaea",
                    background: active ? "rgba(80, 140, 255, 0.22)" : "transparent", // 選択中カラー（ダーク向け）
                  }}
                  onMouseEnter={(e) => {
                    if (!active) e.currentTarget.style.background = "rgba(255,255,255,0.05)";
                  }}
                  onMouseLeave={(e) => {
                    if (!active) e.currentTarget.style.background = "transparent";
                  }}
                >
                  <div style={{ fontSize: 12 }}>{formatLocal(evt.timestamp)}</div>
                  <div style={{ fontSize: 12, fontWeight: 800 }}>{evt.level}</div>
                  <div style={ellipsis12}>{evt.action}</div>
                  <div style={ellipsis12}>{evt.summary}</div>
                </button>
              );
            })}
        </div>

        {selected && (
          <Modal onClose={() => setSelected(null)} title="ログ詳細">
            <DetailMinimal event={selected} />
          </Modal>
        )}
      </div>
    </div>
  );
}

/** --- detail minimal --- */

function DetailMinimal({ event }: { event: AuditEvent }) {
  const { main, others } = pickDetail(event.detail);

  return (
    <div style={{ display: "grid", gap: 12 }}>
      <Section title="基本">
        <KV label="時刻" value={formatLocal(event.timestamp)} />
        <KV label="レベル" value={event.level} />
        <KV label="actor" value={event.actor} />
        <KV label="action" value={event.action} />
        <KV label="target" value={`${event.target_type}${event.target_id ? ` / ${event.target_id}` : ""}`} />
        <KV label="summary" value={event.summary} />
      </Section>

      {(main.length > 0 || others.length > 0) && (
        <Section title="詳細（必要最低限）">
          {main.map((x) => (
            <KV key={`m-${x.label}`} label={x.label} value={x.value} />
          ))}
          {others.length > 0 && (
            <div style={{ marginTop: 6, display: "grid", gap: 6 }}>
              <div style={{ fontSize: 12, fontWeight: 800, opacity: 0.85 }}>その他</div>
              {others.slice(0, 12).map((x) => (
                <KV key={`o-${x.label}`} label={x.label} value={x.value} />
              ))}
              {others.length > 12 && <div style={{ fontSize: 12, opacity: 0.75 }}>…他 {others.length - 12} 件</div>}
            </div>
          )}
        </Section>
      )}
    </div>
  );
}

/** --- UI parts --- */

function Field({ label, children }: { label: string; children: React.ReactNode }) {
  return (
    <label style={{ display: "grid", gap: 6 }}>
      <span style={{ fontSize: 12, opacity: 0.85 }}>{label}</span>
      {children}
    </label>
  );
}

function Section({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <div
      style={{
        border: "1px solid rgba(255,255,255,0.10)",
        borderRadius: 12,
        padding: 12,
        background: "rgba(0,0,0,0.30)",
      }}
    >
      <div style={{ fontSize: 12, fontWeight: 900, opacity: 0.9, marginBottom: 10 }}>{title}</div>
      <div style={{ display: "grid", gap: 8 }}>{children}</div>
    </div>
  );
}

function KV({ label, value }: { label: string; value: string }) {
  return (
    <div style={{ display: "grid", gridTemplateColumns: "140px 1fr", gap: 10 }}>
      <div style={{ fontSize: 12, fontWeight: 800, opacity: 0.85 }}>{label}</div>
      <div style={{ fontSize: 12, wordBreak: "break-word", color: "#f2f2f2" }}>{value}</div>
    </div>
  );
}

function Modal({ title, onClose, children }: { title: string; onClose: () => void; children: React.ReactNode }) {
  return (
    <div
      onClick={onClose} // 背景クリックで閉じる
      style={{
        position: "fixed",
        inset: 0,
        background: "rgba(0,0,0,0.65)",
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
        padding: 16,
        zIndex: 9999,
      }}
    >
      <div
        onClick={(e) => e.stopPropagation()} // 本体クリックは閉じない
        role="dialog"
        aria-modal="true"
        style={{
          width: "min(900px, 100%)",
          maxHeight: "min(86vh, 900px)",
          overflow: "hidden",
          borderRadius: 14,
          border: "1px solid rgba(255,255,255,0.14)",
          background: "rgba(20,20,20,0.96)",
          boxShadow: "0 10px 40px rgba(0,0,0,0.6)",
        }}
      >
        <div
          style={{
            padding: "12px 14px",
            display: "flex",
            alignItems: "center",
            borderBottom: "1px solid rgba(255,255,255,0.10)",
            background: "rgba(255,255,255,0.04)",
          }}
        >
          <div style={{ fontSize: 14, fontWeight: 900 }}>{title}</div>
          <div style={{ marginLeft: "auto", fontSize: 12, opacity: 0.75 }}>
            背景クリックで閉じます
          </div>
        </div>

        <div style={{ padding: 14, overflow: "auto", maxHeight: "calc(86vh - 56px)" }}>{children}</div>
      </div>
    </div>
  );
}

/** --- styles --- */

const inputStyle: React.CSSProperties = {
  padding: 10,
  borderRadius: 10,
  border: "1px solid rgba(255,255,255,0.16)",
  background: "rgba(0,0,0,0.45)",
  color: "#eaeaea",
  outline: "none",
};

const primaryButtonStyle: React.CSSProperties = {
  padding: "10px 12px",
  borderRadius: 10,
  border: "1px solid rgba(255,255,255,0.18)",
  background: "rgba(255,255,255,0.10)",
  color: "#ffffff",
  fontWeight: 900,
  cursor: "pointer",
};

const secondaryButtonStyle: React.CSSProperties = {
  padding: "9px 12px",
  borderRadius: 10,
  border: "1px solid rgba(255,255,255,0.14)",
  background: "rgba(0,0,0,0.35)",
  color: "#eaeaea",
  fontWeight: 800,
  cursor: "pointer",
};

const errorBoxStyle: React.CSSProperties = {
  padding: 12,
  borderRadius: 12,
  border: "1px solid rgba(255, 80, 80, 0.35)",
  background: "rgba(120, 20, 20, 0.25)",
};

const ellipsis12: React.CSSProperties = {
  fontSize: 12,
  overflow: "hidden",
  textOverflow: "ellipsis",
  whiteSpace: "nowrap",
};

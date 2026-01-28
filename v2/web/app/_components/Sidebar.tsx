"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { useEffect, useState } from "react";
import type { Workload } from "lib/api";
import { getWorkload } from "lib/api";
import { APP_DATA_CHANGED } from "lib/events";

type NavItem = {
    label: string;
    href?: string;     // まだ未実装なら省略OK
    disabled?: boolean;
};

const NAV: { title: string; items: NavItem[] }[] = [
    {
        title: "Main",
        items: [
        { label: "Dashboard", href: "/dashboard" },
        { label: "Projects", href: "/projects" },
        ],
    },
    {
        title: "Create",
        items: [
        { label: "Planner", href: "/planner", disabled: true },
        { label: "Studio", href: "/studio", disabled: true },
        { label: "Analytics", href: "/analytics", disabled: true },
        ],
    },
    {
        title: "Manage",
        items: [
        { label: "Calendar", href: "/calendar", disabled: true },
        { label: "Templates", href: "/templates", disabled: true },
        { label: "Master / Settings", href: "/settings", disabled: true }, // 角度/タスク/チェックリスト等
        { label: "Version History", href: "/versions", disabled: true },   // 差分保存の管理
        { label: "Check Log", href: "/admin/audit-logs" },   // 
        ],
    },
    {
        title: "Tools",
        items: [
        { label: "Timer Logs", href: "/logs/timer", disabled: true },
        { label: "AI Coach", href: "/ai/coach", disabled: true },
        { label: "Export", href: "/export", disabled: true }, // 概要欄/台本/CSVなど
        ],
    },
];

export default function Sidebar() {
    const pathname = usePathname();
    const [workload, setWorkload] = useState<Workload | null>(null);
    const [workloadError, setWorkloadError] = useState<string | null>(null);

    const fetchWorkload = async () => {
        try {
            setWorkloadError(null);
            const w = await getWorkload();
            setWorkload(w);
        } catch (e: any) {
            setWorkloadError(e?.message ?? "Failed to load workload");
        }
    };

    useEffect(() => {
        fetchWorkload();
        // eslint-disable-next-line react-hooks/exhaustive-deps
    }, []);

    useEffect(() => {
        const handler = () => fetchWorkload();
        window.addEventListener(APP_DATA_CHANGED, handler);
        return () => window.removeEventListener(APP_DATA_CHANGED, handler);
        // eslint-disable-next-line react-hooks/exhaustive-deps
    }, []);

    return (
        <aside
        style={{
            width: 260,
            minWidth: 260,
            borderRight: "1px solid rgba(128,128,128,0.25)",
            padding: 12,
            height: "100vh",
            position: "sticky",
            top: 0,
            overflow: "auto",
        }}
        >
        <div style={{ fontWeight: 900, fontSize: 16, marginBottom: 10 }}>
            Minecraft Create Movie
        </div>

        <div className="card" style={{ marginBottom: 12 }}>
            <div style={{ fontWeight: 800 }}>週間負荷</div>

            {workloadError ? (
                <div className="small" style={{ marginTop: 6, opacity: 0.8 }}>
                取得失敗
                </div>
            ) : !workload ? (
                <div className="small" style={{ marginTop: 6, opacity: 0.8 }}>
                読み込み中...
                </div>
            ) : (
                <>
                <div className="small" style={{ marginTop: 6 }}>
                    負荷：{Math.round(workload.load_percent)}%
                </div>

                <div style={{ height: 8, background: "rgba(128,128,128,0.25)", borderRadius: 6, overflow: "hidden", marginTop: 6 }}>
                    <div
                    style={{
                        width: `${Math.min(100, workload.load_percent)}%`,
                        height: "100%",
                        background: "rgba(0,180,255,0.8)",
                    }}
                    />
                </div>

                <div className="small" style={{ marginTop: 6, opacity: 0.85 }}>
                    実績 {workload.actual_minutes_7d} / 標準 {workload.estimated_minutes_7d} 分
                </div>

                <div className="small" style={{ marginTop: 4, opacity: 0.85 }}>
                    {workload.load_percent >= 100
                    ? "過負荷（調整推奨）"
                    : workload.load_percent >= 80
                    ? "高め（注意）"
                    : workload.load_percent >= 50
                    ? "適正"
                    : "余裕あり"}
                </div>
                </>
            )}
            </div>

        {NAV.map((group) => (
            <div key={group.title} style={{ marginBottom: 12 }}>
            <div className="small" style={{ opacity: 0.75, marginBottom: 6 }}>
                {group.title}
            </div>

            <div style={{ display: "flex", flexDirection: "column", gap: 6 }}>
                {group.items.map((item) => {
                const isActive = item.href ? pathname === item.href || pathname.startsWith(item.href + "/") : false;
                const commonStyle: React.CSSProperties = {
                    padding: "8px 10px",
                    borderRadius: 10,
                    border: "1px solid rgba(128,128,128,0.22)",
                    textDecoration: "none",
                    opacity: item.disabled ? 0.45 : 1,
                    cursor: item.disabled ? "not-allowed" : "pointer",
                    background: isActive ? "rgba(0,180,255,0.15)" : "transparent",
                };

                if (!item.href || item.disabled) {
                    return (
                    <div key={item.label} style={commonStyle} title="未実装（後で追加）">
                        {item.label}
                        <span className="small" style={{ marginLeft: 8, opacity: 0.7 }}>
                        (soon)
                        </span>
                    </div>
                    );
                }

                return (
                    <Link key={item.label} href={item.href} style={commonStyle}>
                    {item.label}
                    </Link>
                );
                })}
            </div>
            </div>
        ))}

        <div className="small" style={{ opacity: 0.7, marginTop: 16 }}>
            ※ “(soon)” は未実装プレースホルダ
        </div>
        </aside>
    );
}

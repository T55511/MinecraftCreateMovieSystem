import type { Metadata } from "next";
import "./globals.css";
import Sidebar from "@/components/Sidebar";

export const metadata: Metadata = {
  title: "Radio Flow Studio",
  description: "音声収録・制作管理システム",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="ja">
      <body className="flex bg-slate-50">
        {/* 左サイドバー */}
        <Sidebar />
        {/* メインコンテンツエリア（サイドバーの幅256px分を空ける） */}
        <main className="flex-1 ml-64 min-h-screen">
          {children}
        </main>
      </body>
    </html>
  );
}
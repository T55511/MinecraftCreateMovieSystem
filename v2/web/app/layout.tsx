import "./globals.css";
import "./globals.css";
import Sidebar from "./_components/Sidebar";

export const metadata = {
  title: "MCMS v2",
  description: "Minecraft Create Movie System v2"
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="ja">
      <body>
        <div style={{ display: "flex", minHeight: "100vh" }}>
          <Sidebar />
          <main style={{ flex: 1, padding: 12 }}>
            {children}
          </main>
        </div>
      </body>
    </html>
  );
}

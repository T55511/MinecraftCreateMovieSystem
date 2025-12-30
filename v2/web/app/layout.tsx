import "./globals.css";


export const metadata = {
  title: "MCMS v2",
  description: "Minecraft Create Movie System v2"
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="ja">
      <body>
        <main>{children}</main>
      </body>
    </html>
  );
}

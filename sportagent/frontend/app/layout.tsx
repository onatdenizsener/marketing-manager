import type { Metadata } from "next";
import { Inter } from "next/font/google";
import "./globals.css";
import Link from "next/link";
import { BarChart2, MessageSquare, Activity, FileText } from "lucide-react";

const inter = Inter({ subsets: ["latin"], variable: "--font-sans" });

export const metadata: Metadata = {
  title: "Sport Trends Marketing Agent",
  description: "Futbol, spor oyuncakları ve 3D oyuncak nişleri için günlük trend ajanı",
};

const navItems = [
  { href: "/", label: "Raporlar", icon: FileText },
  { href: "/chat", label: "Chat", icon: MessageSquare },
  { href: "/sources", label: "Sources", icon: Activity },
];

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="tr" className="dark">
      <body className={`${inter.variable} font-sans bg-background text-foreground antialiased`}>
        <div className="flex min-h-screen">
          <aside className="w-56 border-r border-border bg-card flex flex-col shrink-0">
            <div className="p-4 border-b border-border">
              <div className="flex items-center gap-2">
                <BarChart2 className="h-5 w-5 text-primary" />
                <span className="font-semibold text-sm">Sport Trends</span>
              </div>
            </div>
            <nav className="flex-1 p-3 space-y-1">
              {navItems.map(({ href, label, icon: Icon }) => (
                <Link
                  key={href}
                  href={href}
                  className="flex items-center gap-3 px-3 py-2 rounded-md text-sm text-muted-foreground hover:text-foreground hover:bg-accent transition-colors"
                >
                  <Icon className="h-4 w-4" />
                  {label}
                </Link>
              ))}
            </nav>
          </aside>
          <main className="flex-1 overflow-auto p-6">{children}</main>
        </div>
      </body>
    </html>
  );
}

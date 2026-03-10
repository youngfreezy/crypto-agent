"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { cn } from "@/lib/utils";

const navItems = [
  { href: "/", label: "Dashboard" },
  { href: "/ai", label: "AI Agent" },
  { href: "/portfolio", label: "Portfolio" },
  { href: "/trades", label: "Trades" },
  { href: "/strategies", label: "Strategies" },
  { href: "/market", label: "Market" },
];

export default function Sidebar() {
  const pathname = usePathname();

  return (
    <aside className="w-56 border-r border-border bg-card flex flex-col py-6 px-4 shrink-0">
      <h1 className="text-lg font-bold mb-8 px-2 tracking-tight">
        Crypto Agent
      </h1>
      <nav className="flex flex-col gap-1">
        {navItems.map((item) => {
          const isActive =
            item.href === "/"
              ? pathname === "/"
              : pathname.startsWith(item.href);
          return (
            <Link
              key={item.href}
              href={item.href}
              className={cn(
                "px-3 py-2 rounded-md text-sm transition-colors",
                isActive
                  ? "bg-accent text-foreground font-medium"
                  : "text-muted-foreground hover:text-foreground hover:bg-accent/50"
              )}
            >
              {item.label}
            </Link>
          );
        })}
      </nav>
    </aside>
  );
}

"use client";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { useAuth } from "@/hooks/useAuth";
import { Camera, ShoppingCart, BarChart2, LogOut, User } from "lucide-react";
import clsx from "clsx";

const NAV = [
  { href: "/scan",     icon: Camera,       label: "Scan Food"     },
  { href: "/shopping", icon: ShoppingCart, label: "Shopping List" },
  { href: "/spending", icon: BarChart2,    label: "Spending"      },
];

export default function AppLayout({ children }: { children: React.ReactNode }) {
  const { user, logout } = useAuth();
  const pathname = usePathname();

  return (
    <div className="flex min-h-screen">
      {/* Sidebar */}
      <aside className="w-56 bg-white border-r border-gray-100 flex flex-col fixed h-full">
        <div className="p-5 border-b border-gray-100">
          <span className="text-xl font-bold flex items-center gap-2">
            🥗 <span>NutriTrack</span>
          </span>
        </div>

        <nav className="flex-1 p-3 space-y-1">
          {NAV.map(({ href, icon: Icon, label }) => (
            <Link key={href} href={href}
              className={clsx(
                "flex items-center gap-3 px-3 py-2 rounded-lg text-sm font-medium transition-colors",
                pathname === href
                  ? "bg-brand-50 text-brand-700"
                  : "text-gray-600 hover:bg-gray-50"
              )}
            >
              <Icon size={18} />
              {label}
            </Link>
          ))}
        </nav>

        <div className="p-3 border-t border-gray-100">
          <div className="flex items-center gap-2 px-3 py-2 text-sm text-gray-600 mb-1">
            <User size={16} />
            <span className="truncate">{user?.full_name || user?.email}</span>
          </div>
          <button onClick={logout}
            className="flex items-center gap-3 px-3 py-2 w-full rounded-lg text-sm
                       text-gray-500 hover:bg-gray-50 hover:text-red-500 transition-colors">
            <LogOut size={16} />
            Sign out
          </button>
        </div>
      </aside>

      {/* Main content */}
      <main className="ml-56 flex-1 p-8 max-w-4xl">
        {children}
      </main>
    </div>
  );
}

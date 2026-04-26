import { Link } from "@tanstack/react-router";
import {
  Activity,
  Inbox as InboxIcon,
  GitCompare,
  FileText,
  Lock,
  ToggleLeft,
  HeartPulse,
  Sparkles,
} from "lucide-react";
import { cn } from "@/lib/utils";

const NAV_ITEMS = [
  { to: "/today", label: "Today", icon: Activity },
  { to: "/inbox", label: "Inbox", icon: InboxIcon },
  { to: "/diff", label: "Diff", icon: GitCompare },
  { to: "/outputs", label: "Outputs", icon: FileText },
  { to: "/privacy", label: "Privacy", icon: Lock },
  { to: "/mode", label: "Mode", icon: ToggleLeft },
  { to: "/health", label: "Health", icon: HeartPulse },
] as const;

export function Sidebar() {
  return (
    <aside
      className="flex h-full w-56 flex-col border-r border-sidebar-muted bg-sidebar text-sidebar-foreground"
      aria-label="Primary navigation"
    >
      <div className="flex items-center gap-2 px-5 py-5">
        <div className="grid h-8 w-8 place-items-center rounded-md bg-primary text-primary-foreground">
          <Sparkles className="size-4" />
        </div>
        <div className="flex flex-col leading-tight">
          <span className="text-sm font-semibold">TraceWeaver</span>
          <span className="text-[10px] uppercase tracking-wider text-sidebar-muted-foreground/70">
            local context
          </span>
        </div>
      </div>

      <nav className="flex-1 px-2">
        <ul className="flex flex-col gap-0.5">
          {NAV_ITEMS.map((item) => {
            const Icon = item.icon;
            return (
              <li key={item.to}>
                <Link
                  to={item.to}
                  activeOptions={{ exact: true }}
                  className={cn(
                    "group flex items-center gap-3 rounded-md px-3 py-2 text-sm font-medium",
                    "text-sidebar-foreground/80 transition-colors hover:bg-sidebar-muted hover:text-sidebar-foreground",
                  )}
                  activeProps={{
                    className:
                      "bg-sidebar-muted text-sidebar-foreground shadow-[inset_2px_0_0_0_var(--color-primary)]",
                  }}
                >
                  <Icon className="size-4 shrink-0 opacity-80 group-hover:opacity-100" />
                  <span>{item.label}</span>
                </Link>
              </li>
            );
          })}
        </ul>
      </nav>

      <div className="border-t border-sidebar-muted px-4 py-3 text-[11px] leading-5 text-sidebar-muted-foreground/70">
        <p>v0.1.0 — local-only</p>
        <p className="opacity-70">No data leaves this machine.</p>
      </div>
    </aside>
  );
}

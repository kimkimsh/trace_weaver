import { jsx as _jsx, jsxs as _jsxs } from "react/jsx-runtime";
import { Link } from "@tanstack/react-router";
import { Activity, Inbox as InboxIcon, GitCompare, FileText, Lock, ToggleLeft, HeartPulse, Sparkles, } from "lucide-react";
import { cn } from "@/lib/utils";
const NAV_ITEMS = [
    { to: "/today", label: "Today", icon: Activity },
    { to: "/inbox", label: "Inbox", icon: InboxIcon },
    { to: "/diff", label: "Diff", icon: GitCompare },
    { to: "/outputs", label: "Outputs", icon: FileText },
    { to: "/privacy", label: "Privacy", icon: Lock },
    { to: "/mode", label: "Mode", icon: ToggleLeft },
    { to: "/health", label: "Health", icon: HeartPulse },
];
export function Sidebar() {
    return (_jsxs("aside", { className: "flex h-full w-56 flex-col border-r border-sidebar-muted bg-sidebar text-sidebar-foreground", "aria-label": "Primary navigation", children: [_jsxs("div", { className: "flex items-center gap-2 px-5 py-5", children: [_jsx("div", { className: "grid h-8 w-8 place-items-center rounded-md bg-primary text-primary-foreground", children: _jsx(Sparkles, { className: "size-4" }) }), _jsxs("div", { className: "flex flex-col leading-tight", children: [_jsx("span", { className: "text-sm font-semibold", children: "TraceWeaver" }), _jsx("span", { className: "text-[10px] uppercase tracking-wider text-sidebar-muted-foreground/70", children: "local context" })] })] }), _jsx("nav", { className: "flex-1 px-2", children: _jsx("ul", { className: "flex flex-col gap-0.5", children: NAV_ITEMS.map((item) => {
                        const Icon = item.icon;
                        return (_jsx("li", { children: _jsxs(Link, { to: item.to, activeOptions: { exact: true }, className: cn("group flex items-center gap-3 rounded-md px-3 py-2 text-sm font-medium", "text-sidebar-foreground/80 transition-colors hover:bg-sidebar-muted hover:text-sidebar-foreground"), activeProps: {
                                    className: "bg-sidebar-muted text-sidebar-foreground shadow-[inset_2px_0_0_0_var(--color-primary)]",
                                }, children: [_jsx(Icon, { className: "size-4 shrink-0 opacity-80 group-hover:opacity-100" }), _jsx("span", { children: item.label })] }) }, item.to));
                    }) }) }), _jsxs("div", { className: "border-t border-sidebar-muted px-4 py-3 text-[11px] leading-5 text-sidebar-muted-foreground/70", children: [_jsx("p", { children: "v0.1.0 \u2014 local-only" }), _jsx("p", { className: "opacity-70", children: "No data leaves this machine." })] })] }));
}

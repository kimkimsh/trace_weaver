import { jsx as _jsx, jsxs as _jsxs } from "react/jsx-runtime";
import { Search, Sun, Moon, Command as CommandIcon, Activity } from "lucide-react";
import { useQuery } from "@tanstack/react-query";
import { api } from "@/lib/api";
import { useUi } from "@/store/ui";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { formatDuration } from "@/lib/utils";
export function Header() {
    const { theme, setTheme, toggleCommandPalette } = useUi();
    const status = useQuery({
        queryKey: ["status"],
        queryFn: api.status,
        refetchInterval: 5_000,
        retry: 1,
    });
    const daemonOk = status.data?.daemon_state === "running";
    return (_jsxs("header", { className: "flex h-14 items-center justify-between border-b bg-background/80 px-6 backdrop-blur-md", children: [_jsxs("div", { className: "flex items-center gap-3", children: [_jsxs(Badge, { variant: daemonOk ? "success" : status.isError ? "destructive" : "secondary", children: [_jsx(Activity, { className: "mr-1 size-3" }), status.isError
                                ? "daemon offline"
                                : status.isLoading
                                    ? "connecting…"
                                    : `daemon ${status.data?.daemon_state ?? "—"}`] }), status.data && (_jsxs("span", { className: "text-xs text-muted-foreground", children: ["uptime ", formatDuration(status.data.uptime_s * 1000)] }))] }), _jsxs("div", { className: "flex items-center gap-2", children: [_jsxs(Button, { variant: "outline", size: "sm", onClick: toggleCommandPalette, className: "gap-2 text-muted-foreground", children: [_jsx(Search, { className: "size-4" }), _jsx("span", { children: "Search\u2026" }), _jsxs("kbd", { className: "ml-2 hidden items-center gap-0.5 rounded border bg-muted px-1.5 py-0.5 font-mono text-[10px] text-muted-foreground sm:inline-flex", children: [_jsx(CommandIcon, { className: "size-3" }), "K"] })] }), _jsxs(Button, { variant: "ghost", size: "icon", onClick: () => setTheme(theme === "dark" ? "light" : "dark"), "aria-label": "Toggle theme", children: [_jsx(Sun, { className: "size-4 dark:hidden" }), _jsx(Moon, { className: "hidden size-4 dark:block" })] })] })] }));
}

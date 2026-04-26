import { jsx as _jsx, jsxs as _jsxs } from "react/jsx-runtime";
import * as React from "react";
import { Command } from "cmdk";
import { useNavigate } from "@tanstack/react-router";
import { Activity, Inbox, GitCompare, FileText, Lock, ToggleLeft, HeartPulse, PlayCircle, } from "lucide-react";
import { useUi } from "@/store/ui";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { api } from "@/lib/api";
const ROUTES = [
    { to: "/today", label: "Go to Today", icon: Activity },
    { to: "/inbox", label: "Go to Inbox", icon: Inbox },
    { to: "/diff", label: "Go to Diff Approval", icon: GitCompare },
    { to: "/outputs", label: "Go to Outputs", icon: FileText },
    { to: "/privacy", label: "Go to Privacy Center", icon: Lock },
    { to: "/mode", label: "Go to Mode Toggle", icon: ToggleLeft },
    { to: "/health", label: "Go to Model & Health", icon: HeartPulse },
];
export function CommandPalette() {
    const open = useUi((s) => s.commandPaletteOpen);
    const setOpen = useUi((s) => s.setCommandPaletteOpen);
    const navigate = useNavigate();
    const queryClient = useQueryClient();
    React.useEffect(() => {
        function onKey(event) {
            if ((event.metaKey || event.ctrlKey) && event.key.toLowerCase() === "k") {
                event.preventDefault();
                setOpen(!open);
            }
        }
        window.addEventListener("keydown", onKey);
        return () => window.removeEventListener("keydown", onKey);
    }, [open, setOpen]);
    const triggerExtraction = useMutation({
        mutationFn: api.triggerExtraction,
        onSuccess: () => {
            void queryClient.invalidateQueries({ queryKey: ["status"] });
            void queryClient.invalidateQueries({ queryKey: ["conventions"] });
        },
    });
    if (!open)
        return null;
    return (_jsx("div", { className: "fixed inset-0 z-50 grid place-items-start bg-background/70 pt-[15vh] backdrop-blur-sm", role: "dialog", "aria-modal": "true", onClick: () => setOpen(false), children: _jsx("div", { className: "w-full max-w-xl px-4", onClick: (e) => e.stopPropagation(), children: _jsxs(Command, { className: "overflow-hidden rounded-lg border bg-popover text-popover-foreground shadow-2xl", children: [_jsx("div", { className: "flex items-center border-b px-4", children: _jsx(Command.Input, { autoFocus: true, placeholder: "Type a command or search\u2026", className: "h-12 w-full bg-transparent text-sm outline-none placeholder:text-muted-foreground" }) }), _jsxs(Command.List, { className: "max-h-[420px] overflow-y-auto p-1", children: [_jsx(Command.Empty, { className: "px-4 py-6 text-center text-sm text-muted-foreground", children: "No matches." }), _jsx(Command.Group, { heading: "Navigate", className: "px-2 py-1.5 text-xs text-muted-foreground", children: ROUTES.map((item) => {
                                    const Icon = item.icon;
                                    return (_jsxs(Command.Item, { value: item.label, onSelect: () => {
                                            void navigate({ to: item.to });
                                            setOpen(false);
                                        }, className: "flex cursor-pointer items-center gap-2 rounded-md px-3 py-2 text-sm aria-selected:bg-accent aria-selected:text-accent-foreground", children: [_jsx(Icon, { className: "size-4" }), item.label] }, item.to));
                                }) }), _jsx(Command.Group, { heading: "Actions", className: "px-2 py-1.5 text-xs text-muted-foreground", children: _jsxs(Command.Item, { value: "Trigger extraction now", onSelect: () => {
                                        triggerExtraction.mutate();
                                        setOpen(false);
                                    }, className: "flex cursor-pointer items-center gap-2 rounded-md px-3 py-2 text-sm aria-selected:bg-accent aria-selected:text-accent-foreground", children: [_jsx(PlayCircle, { className: "size-4" }), "Trigger extraction now (ADR-15)"] }) })] })] }) }) }));
}

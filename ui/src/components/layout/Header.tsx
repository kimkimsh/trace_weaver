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

  return (
    <header className="flex h-14 items-center justify-between border-b bg-background/80 px-6 backdrop-blur-md">
      <div className="flex items-center gap-3">
        <Badge variant={daemonOk ? "success" : status.isError ? "destructive" : "secondary"}>
          <Activity className="mr-1 size-3" />
          {status.isError
            ? "daemon offline"
            : status.isLoading
              ? "connecting…"
              : `daemon ${status.data?.daemon_state ?? "—"}`}
        </Badge>
        {status.data && (
          <span className="text-xs text-muted-foreground">
            uptime {formatDuration(status.data.uptime_s * 1000)}
          </span>
        )}
      </div>

      <div className="flex items-center gap-2">
        <Button
          variant="outline"
          size="sm"
          onClick={toggleCommandPalette}
          className="gap-2 text-muted-foreground"
        >
          <Search className="size-4" />
          <span>Search…</span>
          <kbd className="ml-2 hidden items-center gap-0.5 rounded border bg-muted px-1.5 py-0.5 font-mono text-[10px] text-muted-foreground sm:inline-flex">
            <CommandIcon className="size-3" />K
          </kbd>
        </Button>
        <Button
          variant="ghost"
          size="icon"
          onClick={() => setTheme(theme === "dark" ? "light" : "dark")}
          aria-label="Toggle theme"
        >
          <Sun className="size-4 dark:hidden" />
          <Moon className="hidden size-4 dark:block" />
        </Button>
      </div>
    </header>
  );
}

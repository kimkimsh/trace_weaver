import { createFileRoute } from "@tanstack/react-router";
import { useQuery } from "@tanstack/react-query";
import { Activity, FolderGit2, Inbox as InboxIcon, FileText, AlertTriangle } from "lucide-react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Separator } from "@/components/ui/separator";
import { api } from "@/lib/api";
import { cn, formatBytes, formatRelativeTime } from "@/lib/utils";
import type { CollectorHealth } from "@/types/domain";
import {
  ResponsiveContainer,
  AreaChart,
  Area,
  XAxis,
  YAxis,
  Tooltip,
  CartesianGrid,
} from "recharts";

export const Route = createFileRoute("/today")({
  component: TodayPage,
});

const COLLECTOR_LABEL: Record<string, string> = {
  shell: "Shell",
  git: "Git",
  fs: "Filesystem",
  browser: "Browser",
  tmux: "tmux",
  tilix: "Tilix",
};

function collectorBadgeVariant(state: CollectorHealth["state"]): "success" | "warning" | "destructive" | "secondary" {
  switch (state) {
    case "ok":
      return "success";
    case "backpressure":
      return "warning";
    case "degraded":
      return "destructive";
    default:
      return "secondary";
  }
}

function TodayPage() {
  const status = useQuery({
    queryKey: ["status"],
    queryFn: api.status,
    refetchInterval: 5_000,
  });
  const conventions = useQuery({ queryKey: ["conventions"], queryFn: api.conventions });
  const projects = useQuery({ queryKey: ["projects"], queryFn: api.projects });
  const outputs = useQuery({ queryKey: ["outputs"], queryFn: api.outputs });

  const collectors = status.data?.collectors ?? [];
  const pendingConventions =
    conventions.data?.items.filter((c) => c.user_status === "pending").length ?? 0;
  const recentOutputs =
    outputs.data?.items
      .filter((o) => o.last_applied_at !== null)
      .slice(0, 4)
      .sort((a, b) => (b.last_applied_at ?? 0) - (a.last_applied_at ?? 0)) ?? [];

  // synthesize a sparkline from collector throughput; in v1 the timeline data
  // comes from the daemon /api/v1/events stream — until that lands we plot
  // events_per_min as a snapshot bar.
  const collectorChart = collectors.map((c) => ({
    name: COLLECTOR_LABEL[c.source] ?? c.source,
    epm: c.events_per_min,
    dropped: c.dropped_count,
  }));

  return (
    <div className="mx-auto flex w-full max-w-6xl flex-col gap-6">
      <div>
        <h1 className="text-2xl font-semibold tracking-tight">Today</h1>
        <p className="text-sm text-muted-foreground">
          Ambient activity across {COLLECTOR_LABEL.shell}, {COLLECTOR_LABEL.git},{" "}
          {COLLECTOR_LABEL.fs}, browser & terminal — 100% local.
        </p>
      </div>

      <div className="grid grid-cols-1 gap-4 lg:grid-cols-3">
        <Card>
          <CardHeader className="pb-2">
            <CardDescription>Pending conventions</CardDescription>
            <CardTitle className="flex items-baseline gap-2 text-3xl tabular-nums">
              {pendingConventions}
              <span className="text-sm font-normal text-muted-foreground">in inbox</span>
            </CardTitle>
          </CardHeader>
          <CardContent className="text-sm text-muted-foreground">
            <InboxIcon className="mr-1 inline size-3" />
            Review & accept to ship into the seven output formats.
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="pb-2">
            <CardDescription>SQLite store</CardDescription>
            <CardTitle className="text-3xl tabular-nums">
              {status.data ? formatBytes(status.data.store.db_size_bytes) : "—"}
            </CardTitle>
          </CardHeader>
          <CardContent className="text-sm text-muted-foreground">
            {status.data?.store.events_total.toLocaleString() ?? 0} events ·{" "}
            {status.data?.store.conventions_total ?? 0} conventions
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="pb-2">
            <CardDescription>Model backend</CardDescription>
            <CardTitle className="text-xl">
              {status.data?.model.backend ?? "—"}
              <Badge
                variant={status.data?.model.state === "active" ? "success" : "warning"}
                className="ml-2 align-middle text-[10px]"
              >
                {status.data?.model.state ?? "—"}
              </Badge>
            </CardTitle>
          </CardHeader>
          <CardContent className="text-sm text-muted-foreground">
            {status.data?.model.model_id ?? "no model loaded"}
          </CardContent>
        </Card>
      </div>

      <Card>
        <CardHeader className="flex-row items-center justify-between gap-4">
          <div>
            <CardTitle>Collector throughput</CardTitle>
            <CardDescription>events / min, last 5-minute EWMA</CardDescription>
          </div>
        </CardHeader>
        <CardContent className="h-56">
          {collectorChart.length === 0 ? (
            <EmptyState
              icon={Activity}
              title="No collectors active yet"
              description="Run `tw shell init bash` and source the snippet to start ingesting events."
            />
          ) : (
            <ResponsiveContainer width="100%" height="100%">
              <AreaChart data={collectorChart}>
                <defs>
                  <linearGradient id="epm" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="0%" stopColor="var(--color-chart-1)" stopOpacity={0.6} />
                    <stop offset="100%" stopColor="var(--color-chart-1)" stopOpacity={0} />
                  </linearGradient>
                </defs>
                <CartesianGrid strokeDasharray="3 3" opacity={0.2} />
                <XAxis dataKey="name" stroke="currentColor" fontSize={12} />
                <YAxis stroke="currentColor" fontSize={12} allowDecimals={false} />
                <Tooltip
                  contentStyle={{
                    backgroundColor: "var(--color-popover)",
                    border: "1px solid var(--color-border)",
                    fontSize: 12,
                  }}
                />
                <Area type="monotone" dataKey="epm" stroke="var(--color-chart-1)" fill="url(#epm)" />
              </AreaChart>
            </ResponsiveContainer>
          )}
        </CardContent>
      </Card>

      <div className="grid grid-cols-1 gap-4 lg:grid-cols-2">
        <Card>
          <CardHeader>
            <CardTitle>Collector health</CardTitle>
            <CardDescription>Per source state + last event</CardDescription>
          </CardHeader>
          <CardContent>
            {collectors.length === 0 ? (
              <p className="text-sm text-muted-foreground">No collectors registered.</p>
            ) : (
              <ul className="divide-y">
                {collectors.map((c) => (
                  <li key={c.source} className="flex items-center justify-between gap-4 py-2">
                    <div className="flex items-center gap-3">
                      <span
                        className={cn(
                          "inline-block h-2.5 w-2.5 rounded-full",
                          c.state === "ok" && "bg-success",
                          c.state === "backpressure" && "bg-warning",
                          c.state === "degraded" && "bg-destructive",
                          c.state === "off" && "bg-muted-foreground/40",
                        )}
                      />
                      <span className="text-sm font-medium">
                        {COLLECTOR_LABEL[c.source] ?? c.source}
                      </span>
                    </div>
                    <div className="flex items-center gap-3 text-xs text-muted-foreground">
                      <span>{c.events_per_min.toFixed(1)} epm</span>
                      <Badge variant={collectorBadgeVariant(c.state)} className="text-[10px]">
                        {c.state}
                      </Badge>
                    </div>
                  </li>
                ))}
              </ul>
            )}
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Recent outputs</CardTitle>
            <CardDescription>Last applied per agent format</CardDescription>
          </CardHeader>
          <CardContent>
            {recentOutputs.length === 0 ? (
              <EmptyState
                icon={FileText}
                title="Nothing applied yet"
                description="Accept conventions in the Inbox, then run `tw apply` from Outputs."
              />
            ) : (
              <ul className="divide-y">
                {recentOutputs.map((o) => (
                  <li key={o.id} className="flex items-center justify-between gap-4 py-2">
                    <div className="flex items-center gap-2 text-sm">
                      <FileText className="size-4 text-muted-foreground" />
                      <span className="font-mono">{o.agent_kind}</span>
                    </div>
                    <span className="text-xs text-muted-foreground">
                      {o.last_applied_at ? formatRelativeTime(o.last_applied_at) : "—"}
                    </span>
                  </li>
                ))}
              </ul>
            )}
          </CardContent>
        </Card>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Active projects</CardTitle>
          <CardDescription>
            Projects currently being observed (Codex round-2 patch P3)
          </CardDescription>
        </CardHeader>
        <CardContent>
          {projects.data?.items.length ? (
            <ul className="grid grid-cols-1 gap-2 md:grid-cols-2">
              {projects.data.items.map((p) => (
                <li
                  key={p.id}
                  className="flex items-center justify-between gap-3 rounded-md border bg-background px-3 py-2"
                >
                  <div className="flex min-w-0 items-center gap-2">
                    <FolderGit2 className="size-4 shrink-0 text-muted-foreground" />
                    <span className="truncate font-mono text-xs">{p.root_path}</span>
                  </div>
                  <Badge variant={p.enabled ? "success" : "secondary"} className="text-[10px]">
                    {p.enabled ? "active" : "paused"}
                  </Badge>
                </li>
              ))}
            </ul>
          ) : (
            <EmptyState
              icon={FolderGit2}
              title="No active projects"
              description="Add a project root via the Privacy Center or the CLI."
            />
          )}
        </CardContent>
      </Card>

      <Separator />

      {status.isError && (
        <div className="flex items-center gap-2 rounded-md border border-destructive/40 bg-destructive/10 p-3 text-sm text-destructive">
          <AlertTriangle className="size-4 shrink-0" />
          <span>
            Daemon at <code>127.0.0.1:7777</code> is unreachable — start it with{" "}
            <code className="rounded bg-destructive/20 px-1">tw daemon start</code>.
          </span>
        </div>
      )}
    </div>
  );
}

function EmptyState({
  icon: Icon,
  title,
  description,
}: {
  icon: React.ComponentType<{ className?: string }>;
  title: string;
  description: string;
}) {
  return (
    <div className="flex flex-col items-center justify-center gap-2 px-4 py-8 text-center">
      <Icon className="size-8 text-muted-foreground/60" />
      <p className="text-sm font-medium">{title}</p>
      <p className="max-w-md text-xs text-muted-foreground">{description}</p>
    </div>
  );
}

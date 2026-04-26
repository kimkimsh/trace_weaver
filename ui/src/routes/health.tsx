import * as React from "react";
import { createFileRoute } from "@tanstack/react-router";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Switch } from "@/components/ui/switch";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import { Separator } from "@/components/ui/separator";
import { HeartPulse, Cpu, Database, PlayCircle, Clock } from "lucide-react";
import { api } from "@/lib/api";
import type { ExtractionMode } from "@/types/domain";
import { formatBytes, formatRelativeTime } from "@/lib/utils";

export const Route = createFileRoute("/health")({
  component: HealthPage,
});

function HealthPage() {
  const status = useQuery({ queryKey: ["status"], queryFn: api.status, refetchInterval: 5_000 });

  return (
    <div className="mx-auto flex w-full max-w-6xl flex-col gap-6">
      <div className="flex items-center gap-3">
        <HeartPulse className="size-6 text-muted-foreground" />
        <div>
          <h1 className="text-2xl font-semibold tracking-tight">Model & Health</h1>
          <p className="text-sm text-muted-foreground">
            Backend status, model RAM, redaction tier counts, and the ADR-15 extraction schedule.
          </p>
        </div>
      </div>

      <div className="grid grid-cols-1 gap-4 lg:grid-cols-3">
        <Card>
          <CardHeader className="pb-2">
            <CardDescription>Active backend</CardDescription>
            <CardTitle className="flex items-baseline gap-2 text-xl">
              <Cpu className="size-5 text-primary" />
              {status.data?.model.backend ?? "—"}
            </CardTitle>
          </CardHeader>
          <CardContent className="text-sm text-muted-foreground">
            <div className="font-mono text-xs">{status.data?.model.model_id ?? "—"}</div>
            <div className="mt-2 flex items-center gap-2 text-xs">
              <span>RAM</span>
              <span className="tabular-nums">
                {status.data ? formatBytes(status.data.model.rss_bytes) : "—"}
              </span>
              <Badge
                variant={status.data?.model.state === "active" ? "success" : "warning"}
                className="text-[10px]"
              >
                {status.data?.model.state ?? "—"}
              </Badge>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-2">
            <CardDescription>SQLite store</CardDescription>
            <CardTitle className="flex items-baseline gap-2 text-xl">
              <Database className="size-5 text-primary" />
              {status.data ? formatBytes(status.data.store.db_size_bytes) : "—"}
            </CardTitle>
          </CardHeader>
          <CardContent className="text-sm text-muted-foreground">
            {status.data?.store.events_total.toLocaleString() ?? 0} events stored
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-2">
            <CardDescription>Daemon uptime</CardDescription>
            <CardTitle className="flex items-baseline gap-2 text-xl">
              <Clock className="size-5 text-primary" />
              {status.data ? formatDuration(status.data.uptime_s) : "—"}
            </CardTitle>
          </CardHeader>
          <CardContent className="text-sm text-muted-foreground">
            {status.isError ? "daemon offline" : "active"}
          </CardContent>
        </Card>
      </div>

      <ExtractionScheduleCard />

      <Card>
        <CardHeader>
          <CardTitle>Diagnostics</CardTitle>
          <CardDescription>
            Equivalent to the CLI&apos;s <code>tw doctor --bundle</code> output.
          </CardDescription>
        </CardHeader>
        <CardContent>
          <DoctorView />
        </CardContent>
      </Card>
    </div>
  );
}

function ExtractionScheduleCard() {
  // ADR-15 — user-configurable extraction schedule, mirrors the canonical
  // PATCH /api/v1/extraction/schedule contract.
  const queryClient = useQueryClient();
  const schedule = useQuery({
    queryKey: ["extraction_schedule"],
    queryFn: api.extractionSchedule,
    refetchInterval: 10_000,
  });
  const [interval, setInterval] = React.useState<number | "">("");

  const setMode = useMutation({
    mutationFn: (mode: ExtractionMode) => api.setExtractionSchedule({ mode }),
    onSuccess: () => void queryClient.invalidateQueries({ queryKey: ["extraction_schedule"] }),
  });

  const setIntervalSeconds = useMutation({
    mutationFn: (sec: number) => api.setExtractionSchedule({ interval_seconds: sec }),
    onSuccess: () => void queryClient.invalidateQueries({ queryKey: ["extraction_schedule"] }),
  });

  const trigger = useMutation({
    mutationFn: api.triggerExtraction,
    onSuccess: () => void queryClient.invalidateQueries({ queryKey: ["extraction_schedule"] }),
  });

  const auto = schedule.data?.mode === "auto";

  return (
    <Card>
      <CardHeader className="flex-row items-center justify-between gap-4">
        <div>
          <CardTitle className="flex items-center gap-2">
            <PlayCircle className="size-5 text-primary" />
            Extraction schedule
          </CardTitle>
          <CardDescription>
            ADR-15 — toggle automatic insight extraction or trigger manually.
          </CardDescription>
        </div>
        <Button onClick={() => trigger.mutate()} disabled={trigger.isPending}>
          <PlayCircle className="size-4" />
          Trigger now
        </Button>
      </CardHeader>
      <CardContent className="grid grid-cols-1 gap-4 md:grid-cols-3">
        <div className="flex items-center justify-between gap-3 rounded-md border p-3">
          <div>
            <p className="text-sm font-medium">Auto mode</p>
            <p className="text-xs text-muted-foreground">
              {auto ? "Running on a schedule" : "Manual triggers only"}
            </p>
          </div>
          <Switch
            checked={auto}
            onCheckedChange={(v) => setMode.mutate(v ? "auto" : "manual")}
            disabled={schedule.isLoading || setMode.isPending}
          />
        </div>

        <div className="rounded-md border p-3">
          <p className="text-sm font-medium">Interval</p>
          <p className="text-xs text-muted-foreground">
            current{" "}
            <span className="font-mono">
              {schedule.data?.interval_seconds ?? "—"}s
            </span>
          </p>
          <div className="mt-2 flex gap-2">
            <Input
              type="number"
              min={60}
              max={86_400}
              value={interval}
              onChange={(e) => setInterval(e.target.value === "" ? "" : Number(e.target.value))}
              placeholder="60–86400 s"
              className="h-8"
              disabled={!auto}
            />
            <Button
              size="sm"
              variant="outline"
              disabled={interval === "" || setIntervalSeconds.isPending}
              onClick={() => interval !== "" && setIntervalSeconds.mutate(interval)}
            >
              Save
            </Button>
          </div>
        </div>

        <div className="rounded-md border p-3 text-sm">
          <p className="font-medium">Last run</p>
          <p className="text-xs text-muted-foreground">
            {schedule.data?.last_run_at
              ? formatRelativeTime(schedule.data.last_run_at)
              : "never"}
            {schedule.data?.last_run_status && (
              <Badge
                variant={schedule.data.last_run_status === "ok" ? "success" : "destructive"}
                className="ml-2 text-[10px]"
              >
                {schedule.data.last_run_status}
              </Badge>
            )}
          </p>
          <Separator className="my-2" />
          <p className="font-medium">Next run</p>
          <p className="text-xs text-muted-foreground">
            {schedule.data?.next_run_at
              ? formatRelativeTime(schedule.data.next_run_at)
              : "—"}
          </p>
        </div>
      </CardContent>
    </Card>
  );
}

function DoctorView() {
  const doctor = useQuery({ queryKey: ["doctor"], queryFn: api.doctor });
  if (doctor.isLoading) return <p className="text-sm text-muted-foreground">Running checks…</p>;
  if (doctor.isError)
    return (
      <p className="text-sm text-destructive">Daemon unreachable — start it with `tw daemon start`.</p>
    );
  return (
    <pre className="max-h-[420px] overflow-auto rounded-md border bg-muted/30 p-3 font-mono text-xs leading-5">
      {JSON.stringify(doctor.data, null, 2)}
    </pre>
  );
}

function formatDuration(seconds: number): string {
  if (seconds < 60) return `${seconds}s`;
  if (seconds < 3600) return `${Math.floor(seconds / 60)}m`;
  if (seconds < 86_400) return `${Math.floor(seconds / 3600)}h ${Math.floor((seconds % 3600) / 60)}m`;
  return `${Math.floor(seconds / 86_400)}d ${Math.floor((seconds % 86_400) / 3600)}h`;
}

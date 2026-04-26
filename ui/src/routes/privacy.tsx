import * as React from "react";
import { createFileRoute } from "@tanstack/react-router";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Switch } from "@/components/ui/switch";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import { Lock, Trash2, ShieldAlert } from "lucide-react";
import { api } from "@/lib/api";
import { COLLECTOR_SOURCES } from "@/types/domain";

export const Route = createFileRoute("/privacy")({
  component: PrivacyPage,
});

function PrivacyPage() {
  const status = useQuery({ queryKey: ["status"], queryFn: api.status, refetchInterval: 5_000 });
  const queryClient = useQueryClient();
  const [confirmText, setConfirmText] = React.useState("");

  const forget = useMutation({
    mutationFn: () => api.forget({ scope: "all", confirm: confirmText }),
    onSuccess: () => void queryClient.invalidateQueries(),
  });

  return (
    <div className="mx-auto flex w-full max-w-5xl flex-col gap-6">
      <div className="flex items-center gap-3">
        <Lock className="size-6 text-muted-foreground" />
        <div>
          <h1 className="text-2xl font-semibold tracking-tight">Privacy Center</h1>
          <p className="text-sm text-muted-foreground">
            Everything is local. Toggle collectors per source, audit redactions, and forget data on
            demand.
          </p>
        </div>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Collectors</CardTitle>
          <CardDescription>
            Disabled collectors stop ingesting immediately. Already-stored events are retained
            until you forget them below.
          </CardDescription>
        </CardHeader>
        <CardContent>
          <ul className="divide-y">
            {COLLECTOR_SOURCES.map((src) => {
              const c = status.data?.collectors.find((it) => it.source === src);
              return (
                <li
                  key={src}
                  className="flex items-center justify-between gap-4 py-3 text-sm"
                >
                  <div>
                    <span className="font-medium capitalize">{src}</span>
                    <p className="text-xs text-muted-foreground">
                      {c
                        ? `${c.events_per_min.toFixed(1)} epm · ${c.dropped_count} dropped`
                        : "—"}
                    </p>
                  </div>
                  <Switch checked={c?.enabled ?? false} aria-label={`Toggle ${src}`} />
                </li>
              );
            })}
          </ul>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Redaction audit</CardTitle>
          <CardDescription>
            4-tier pipeline (ADR-9). Tier 0 path guard → Tier 1 regex + gitleaks → Tier 2 SLM →
            Tier 3 pre-output rescan.
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-2 gap-3 sm:grid-cols-4">
            {(["tier0", "tier1", "tier1_gitleaks", "tier2", "tier3", "tier4"] as const).map(
              (tier) => (
                <div key={tier} className="rounded-md border bg-background p-3">
                  <Badge variant="outline" className="text-[10px]">
                    {tier}
                  </Badge>
                  <p className="mt-1 text-2xl font-semibold tabular-nums">0</p>
                  <p className="text-xs text-muted-foreground">redacted last 24h</p>
                </div>
              ),
            )}
          </div>
        </CardContent>
      </Card>

      <Card className="border-destructive/40">
        <CardHeader>
          <div className="flex items-center gap-2">
            <ShieldAlert className="size-5 text-destructive" />
            <CardTitle>Forget</CardTitle>
          </div>
          <CardDescription>
            Type the exact phrase{" "}
            <code className="rounded bg-muted px-1 font-mono text-foreground">FORGET ALL</code> to
            wipe events, conventions, and audit shadow rows. The hash chain remains so the
            deletion itself is verifiable.
          </CardDescription>
        </CardHeader>
        <CardContent className="flex flex-col gap-3 sm:flex-row sm:items-center">
          <Input
            placeholder="Type FORGET ALL"
            value={confirmText}
            onChange={(e) => setConfirmText(e.target.value)}
            className="sm:max-w-xs"
          />
          <Button
            variant="destructive"
            onClick={() => forget.mutate()}
            disabled={confirmText !== "FORGET ALL" || forget.isPending}
          >
            <Trash2 className="size-4" />
            Forget all data
          </Button>
        </CardContent>
      </Card>
    </div>
  );
}

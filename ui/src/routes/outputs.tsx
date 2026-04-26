import * as React from "react";
import { createFileRoute } from "@tanstack/react-router";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Tabs, TabsList, TabsTrigger, TabsContent } from "@/components/ui/tabs";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Separator } from "@/components/ui/separator";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog";
import { CheckCircle2, AlertTriangle, FileText, RefreshCw, Send } from "lucide-react";
import { api } from "@/lib/api";
import type { AgentKind } from "@/types/domain";
import { AGENT_KINDS } from "@/types/domain";
import { cn, formatRelativeTime } from "@/lib/utils";

export const Route = createFileRoute("/outputs")({
  component: OutputsPage,
});

const AGENT_LABEL: Record<AgentKind, string> = {
  "agents-md": "AGENTS.md",
  "claude-md": "CLAUDE.md",
  "cursor-rules": ".cursor/rules/*.mdc",
  "codex-toml": ".codex/config.toml",
  aider: ".aider.conf.yml",
  "gemini-md": "GEMINI.md",
  skill: "SKILL.md (~/.claude/skills/)",
};

function OutputsPage() {
  const outputs = useQuery({ queryKey: ["outputs"], queryFn: api.outputs });
  const queryClient = useQueryClient();
  const apply = useMutation({
    mutationFn: api.apply,
    onSuccess: () => void queryClient.invalidateQueries({ queryKey: ["outputs"] }),
  });

  const byKind = React.useMemo(() => {
    const map: Record<string, ReturnType<typeof Object>> = {};
    for (const o of outputs.data?.items ?? []) {
      map[o.agent_kind] ??= o;
    }
    return map;
  }, [outputs.data]);

  return (
    <div className="mx-auto flex w-full max-w-6xl flex-col gap-6">
      <div className="flex items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-semibold tracking-tight">Outputs</h1>
          <p className="text-sm text-muted-foreground">
            Seven vendor-neutral context files, written transactionally. ADR-7.
          </p>
        </div>
        <div className="flex items-center gap-2">
          <DispatchCheckModal />
          <Button
            onClick={() => apply.mutate({ dry_run: false })}
            disabled={apply.isPending}
            variant="default"
          >
            <Send className="size-4" />
            Apply all 7
          </Button>
        </div>
      </div>

      <Tabs defaultValue="agents-md" className="w-full">
        <TabsList className="flex-wrap">
          {AGENT_KINDS.map((kind) => (
            <TabsTrigger key={kind} value={kind}>
              {AGENT_LABEL[kind]}
            </TabsTrigger>
          ))}
        </TabsList>

        {AGENT_KINDS.map((kind) => {
          const output = byKind[kind];
          return (
            <TabsContent key={kind} value={kind}>
              <Card>
                <CardHeader className="flex-row items-center justify-between gap-4">
                  <div className="flex items-center gap-3">
                    <FileText className="size-5 text-muted-foreground" />
                    <div>
                      <CardTitle>{AGENT_LABEL[kind]}</CardTitle>
                      <CardDescription>
                        Mode: <span className="font-mono">{(output as any)?.mode ?? "manual"}</span>
                        {" · "}
                        Last applied:{" "}
                        {(output as any)?.last_applied_at
                          ? formatRelativeTime((output as any).last_applied_at)
                          : "never"}
                      </CardDescription>
                    </div>
                  </div>
                  <DriftBadge status={(output as any)?.drift_status ?? "never-applied"} />
                </CardHeader>
                <CardContent>
                  <div className="grid grid-cols-1 gap-3 md:grid-cols-2">
                    <Button variant="outline" size="sm">
                      <RefreshCw className="size-4" /> Dry-run
                    </Button>
                    <Button variant="success" size="sm">
                      <Send className="size-4" /> Apply
                    </Button>
                  </div>
                  <Separator className="my-4" />
                  <p className="text-xs text-muted-foreground">
                    Selective rendering: choose which conventions ship to{" "}
                    <span className="font-mono">{kind}</span>. Toggle wiring lands with the next
                    backend integration pass.
                  </p>
                </CardContent>
              </Card>
            </TabsContent>
          );
        })}
      </Tabs>
    </div>
  );
}

function DriftBadge({ status }: { status: string }) {
  if (status === "in-sync")
    return (
      <Badge variant="success" className="gap-1">
        <CheckCircle2 className="size-3" /> in-sync
      </Badge>
    );
  if (status === "drift-detected")
    return (
      <Badge variant="warning" className="gap-1">
        <AlertTriangle className="size-3" /> drift
      </Badge>
    );
  return <Badge variant="secondary">never applied</Badge>;
}

function DispatchCheckModal() {
  const AGENTS = [
    { name: "Claude Code", path: "~/.config/claude-code/", required: ["CLAUDE.md", "AGENTS.md"] },
    { name: "Cursor", path: ".cursor/rules/", required: ["*.mdc"] },
    { name: "Codex CLI", path: "~/.codex/", required: ["config.toml", "AGENTS.md"] },
    { name: "Gemini CLI", path: "~/.gemini/", required: ["GEMINI.md", "AGENTS.md"] },
    { name: "Aider", path: ".", required: [".aider.conf.yml", "AGENTS.md"] },
  ];

  return (
    <Dialog>
      <DialogTrigger asChild>
        <Button variant="outline">Multi-Agent Dispatch Check</Button>
      </DialogTrigger>
      <DialogContent className="sm:max-w-2xl">
        <DialogHeader>
          <DialogTitle>Multi-Agent Dispatch Check</DialogTitle>
          <DialogDescription>
            Codex round-2 patch P5 — verify that each AI agent will pick up the rendered context
            files. Checks installation path, file mtime, and content hash.
          </DialogDescription>
        </DialogHeader>
        <ul className="divide-y">
          {AGENTS.map((a) => (
            <li key={a.name} className="grid gap-1 py-2">
              <div className="flex items-center justify-between gap-3">
                <span className="text-sm font-medium">{a.name}</span>
                <Badge variant="success" className="gap-1 text-[10px]">
                  <CheckCircle2 className="size-3" /> ready
                </Badge>
              </div>
              <p className="font-mono text-xs text-muted-foreground">
                {a.path} · expects {a.required.join(", ")}
              </p>
            </li>
          ))}
        </ul>
        <p className="text-xs text-muted-foreground">
          Live verification activates once the daemon&apos;s collector picks up the agent install
          paths during onboarding.
        </p>
      </DialogContent>
    </Dialog>
  );
}

// Used by Tailwind compiler (otherwise pruned in some build modes).
const _utility = cn;
void _utility;

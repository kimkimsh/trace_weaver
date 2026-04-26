import { createFileRoute } from "@tanstack/react-router";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { GitCompare, ShieldCheck } from "lucide-react";

export const Route = createFileRoute("/diff")({
  component: DiffPage,
});

function DiffPage() {
  return (
    <div className="mx-auto flex w-full max-w-6xl flex-col gap-6">
      <div>
        <h1 className="text-2xl font-semibold tracking-tight">Diff Approval</h1>
        <p className="text-sm text-muted-foreground">
          Side-by-side view of pending output writes with per-line provenance and a final secret
          rescan. No file is mutated until you approve.
        </p>
      </div>

      <Card>
        <CardHeader className="flex-row items-center justify-between">
          <div className="flex items-center gap-2">
            <GitCompare className="size-5 text-muted-foreground" />
            <div>
              <CardTitle>AGENTS.md (project: trace_weaver)</CardTitle>
              <CardDescription>+12 / −0 · 7 conventions, 3 skills</CardDescription>
            </div>
          </div>
          <Badge variant="success" className="gap-1">
            <ShieldCheck className="size-3" /> Tier-3 redaction passed
          </Badge>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-2 gap-4">
            <pre className="max-h-[480px] overflow-auto rounded-md border bg-muted/30 p-3 font-mono text-xs leading-5">
{`<!-- tw-managed: do not edit by hand -->
## Conventions

- We use uv for all Python venv management.
- Daemon binds 127.0.0.1:7777 only.
- Redaction Tier 0 + Tier 1 run before any DB write.

## Skills

- traceweaver-output-regression: dry-run all 7 + snapshot.
- fastapi-websocket-debugging: diagnose disconnect cycles.
`}
            </pre>
            <pre className="max-h-[480px] overflow-auto rounded-md border bg-success/5 p-3 font-mono text-xs leading-5 text-success">
{`<!-- tw-managed: do not edit by hand -->
## Conventions

- We use uv for all Python venv management.        # evidence ×6 · 78%
- Daemon binds 127.0.0.1:7777 only.                # evidence ×4 · 81%
- Redaction Tier 0 + Tier 1 run before any DB write. # evidence ×7 · 92%
+ - Pytest is the canonical test runner.            # evidence ×5 · 73%

## Skills

- traceweaver-output-regression: dry-run all 7 + snapshot.
- fastapi-websocket-debugging: diagnose disconnect cycles.
+ - agent-context-review: audit AGENTS.md / GEMINI.md drift.
`}
            </pre>
          </div>
          <p className="mt-3 text-xs text-muted-foreground">
            Real <code>react-diff-view</code> integration arrives with B4-4 — this snapshot is
            populated from the daemon&apos;s <code>POST /api/v1/apply?dry_run=true</code> response
            once that wiring is complete.
          </p>
        </CardContent>
      </Card>
    </div>
  );
}

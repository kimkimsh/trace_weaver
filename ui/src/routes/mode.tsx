import { createFileRoute } from "@tanstack/react-router";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { ToggleLeft } from "lucide-react";
import { AGENT_KINDS, APPLY_MODES } from "@/types/domain";

export const Route = createFileRoute("/mode")({
  component: ModePage,
});

const MODE_LABEL: Record<string, string> = {
  manual: "Manual",
  "auto-proposal": "Auto propose",
  "auto-apply": "Auto apply",
  off: "Off",
};

function ModePage() {
  const projects = ["~/projects/trace_weaver", "~/projects/example-fastapi"];

  return (
    <div className="mx-auto flex w-full max-w-6xl flex-col gap-6">
      <div className="flex items-center gap-3">
        <ToggleLeft className="size-6 text-muted-foreground" />
        <div>
          <h1 className="text-2xl font-semibold tracking-tight">Mode Toggle</h1>
          <p className="text-sm text-muted-foreground">
            Per-project × per-format dispatch policy. Auto-apply is blocked for global files
            (ADR-7).
          </p>
        </div>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Dispatch matrix</CardTitle>
          <CardDescription>
            Click a cell to cycle through {APPLY_MODES.join(" → ")}.
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b text-left text-xs text-muted-foreground">
                  <th className="px-3 py-2">Project</th>
                  {AGENT_KINDS.map((k) => (
                    <th key={k} className="px-3 py-2 text-center font-mono">
                      {k}
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {projects.map((p) => (
                  <tr key={p} className="border-b">
                    <td className="px-3 py-2 font-mono text-xs">{p}</td>
                    {AGENT_KINDS.map((k) => (
                      <td key={k} className="px-3 py-2 text-center">
                        <Badge variant="outline" className="text-[10px]">
                          {MODE_LABEL.manual}
                        </Badge>
                      </td>
                    ))}
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Korean Code Mode</CardTitle>
          <CardDescription>
            11-state machine (Codex round-2 patch P6) — swaps the active SLM between Qwen3-8B
            (Korean) and Qwen2.5-Coder-7B (English) based on detected language signal.
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="flex flex-wrap items-center gap-2">
            {[
              "off",
              "detect",
              "candidate",
              "warm",
              "swap-pending",
              "swap-running",
              "active",
              "fallback-en",
              "fallback-cpu",
              "rules-only",
              "error",
            ].map((s) => (
              <Badge key={s} variant={s === "off" ? "secondary" : "outline"} className="text-[10px]">
                {s}
              </Badge>
            ))}
          </div>
        </CardContent>
      </Card>
    </div>
  );
}

import * as React from "react";
import { createFileRoute } from "@tanstack/react-router";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Check, X, Pencil, Inbox as InboxIcon, AlertCircle } from "lucide-react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Tabs, TabsList, TabsTrigger, TabsContent } from "@/components/ui/tabs";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Separator } from "@/components/ui/separator";
import { api } from "@/lib/api";
import { cn } from "@/lib/utils";
import type { Convention, ConventionStatus } from "@/types/domain";

export const Route = createFileRoute("/inbox")({
  component: InboxPage,
});

function InboxPage() {
  return (
    <div className="mx-auto flex w-full max-w-6xl flex-col gap-6">
      <div>
        <h1 className="text-2xl font-semibold tracking-tight">Evidence Inbox</h1>
        <p className="text-sm text-muted-foreground">
          Review what the local SLM extracted from the last 30 days of activity. Accepted items
          ship to your AGENTS.md / CLAUDE.md / Cursor rules etc. ETH Zürich 4-gate enforced.
        </p>
      </div>

      <Tabs defaultValue="conventions" className="w-full">
        <TabsList>
          <TabsTrigger value="conventions">Conventions</TabsTrigger>
          <TabsTrigger value="recommendations">Recommendations</TabsTrigger>
          <TabsTrigger value="skills">Skill candidates</TabsTrigger>
        </TabsList>

        <TabsContent value="conventions">
          <ConventionList />
        </TabsContent>
        <TabsContent value="recommendations">
          <RecommendationList />
        </TabsContent>
        <TabsContent value="skills">
          <SkillList />
        </TabsContent>
      </Tabs>
    </div>
  );
}

function ConventionList() {
  const conventions = useQuery({ queryKey: ["conventions"], queryFn: api.conventions });
  const queryClient = useQueryClient();
  const [filter, setFilter] = React.useState<ConventionStatus | "all">("pending");

  const patch = useMutation({
    mutationFn: (vars: { id: number; status: ConventionStatus }) =>
      api.patchConvention(vars.id, { user_status: vars.status }),
    onSuccess: () => void queryClient.invalidateQueries({ queryKey: ["conventions"] }),
  });

  const items = (conventions.data?.items ?? []).filter(
    (c) => filter === "all" || c.user_status === filter,
  );

  return (
    <Card>
      <CardHeader className="flex-row items-center justify-between">
        <div>
          <CardTitle>Pending conventions</CardTitle>
          <CardDescription>
            Each convention shows evidence count + confidence so you can audit signal vs. noise.
          </CardDescription>
        </div>
        <div className="flex items-center gap-2">
          {(["pending", "accepted", "rejected", "edited", "all"] as const).map((s) => (
            <Button
              key={s}
              size="sm"
              variant={filter === s ? "default" : "outline"}
              onClick={() => setFilter(s)}
            >
              {s}
            </Button>
          ))}
        </div>
      </CardHeader>
      <CardContent>
        {conventions.isLoading ? (
          <ListSkeleton />
        ) : items.length === 0 ? (
          <EmptyInbox label={filter === "pending" ? "No pending conventions" : `No ${filter} items`} />
        ) : (
          <ul className="divide-y">
            {items.map((c) => (
              <ConventionRow
                key={c.id}
                convention={c}
                onAccept={() => patch.mutate({ id: c.id, status: "accepted" })}
                onReject={() => patch.mutate({ id: c.id, status: "rejected" })}
                pending={patch.isPending}
              />
            ))}
          </ul>
        )}
      </CardContent>
    </Card>
  );
}

function ConventionRow({
  convention,
  onAccept,
  onReject,
  pending,
}: {
  convention: Convention;
  onAccept: () => void;
  onReject: () => void;
  pending: boolean;
}) {
  return (
    <li className="grid grid-cols-1 gap-3 py-3 md:grid-cols-[1fr_auto] md:items-center">
      <div>
        <div className="flex items-center gap-2">
          <Badge variant="outline" className="text-[10px] uppercase">
            {convention.kind}
          </Badge>
          <span className="text-xs text-muted-foreground">
            {convention.evidence_count} evidence · {(convention.confidence * 100).toFixed(0)}%
            confidence
          </span>
          {convention.is_inferable && (
            <Badge variant="warning" className="gap-1 text-[10px]">
              <AlertCircle className="size-3" /> inferable from code
            </Badge>
          )}
        </div>
        <p className="mt-1 text-sm leading-snug">{convention.rule_text}</p>
        {convention.examples.length > 0 && (
          <details className="mt-1 text-xs text-muted-foreground">
            <summary className="cursor-pointer select-none">
              {convention.examples.length} example{convention.examples.length > 1 ? "s" : ""}
            </summary>
            <ul className="mt-1 space-y-0.5 font-mono">
              {convention.examples.slice(0, 3).map((ex, i) => (
                <li key={i} className="truncate">
                  · {ex}
                </li>
              ))}
            </ul>
          </details>
        )}
      </div>
      <div className="flex items-center gap-1.5">
        <Button
          size="sm"
          variant="success"
          onClick={onAccept}
          disabled={pending || convention.user_status === "accepted"}
        >
          <Check className="size-4" /> Accept
        </Button>
        <Button size="sm" variant="ghost" disabled>
          <Pencil className="size-4" /> Edit
        </Button>
        <Button
          size="sm"
          variant="outline"
          onClick={onReject}
          disabled={pending || convention.user_status === "rejected"}
        >
          <X className="size-4" />
        </Button>
      </div>
    </li>
  );
}

function RecommendationList() {
  const recommendations = useQuery({ queryKey: ["recommendations"], queryFn: api.recommendations });
  const items = recommendations.data?.items ?? [];

  return (
    <Card>
      <CardHeader>
        <CardTitle>Recommendations</CardTitle>
        <CardDescription>
          Automation suggestions: skills, slash commands, MDC rules, AGENTS.md sections.
        </CardDescription>
      </CardHeader>
      <CardContent>
        {recommendations.isLoading ? (
          <ListSkeleton />
        ) : items.length === 0 ? (
          <EmptyInbox label="No recommendations queued" />
        ) : (
          <ul className="divide-y">
            {items.map((r) => (
              <li key={r.id} className="grid gap-1 py-3">
                <div className="flex items-center gap-2">
                  <Badge variant="info" className="text-[10px]">
                    {r.kind}
                  </Badge>
                  <span className="text-sm font-medium">{r.title}</span>
                </div>
                <p className="text-sm text-muted-foreground">{r.body}</p>
              </li>
            ))}
          </ul>
        )}
      </CardContent>
    </Card>
  );
}

function SkillList() {
  const skills = useQuery({ queryKey: ["skill_candidates"], queryFn: api.skillCandidates });
  const items = skills.data?.items ?? [];

  return (
    <Card>
      <CardHeader>
        <CardTitle>Skill candidates (inert SKILL.md proposals)</CardTitle>
        <CardDescription>
          Repeated workflows the daemon noticed. Generated SKILL files are{" "}
          <code className="rounded bg-muted px-1 text-xs">chmod 644</code> (ADR-13). Activation
          requires a typed-confirm.
        </CardDescription>
      </CardHeader>
      <CardContent>
        {skills.isLoading ? (
          <ListSkeleton />
        ) : items.length === 0 ? (
          <EmptyInbox label="No skill candidates yet" />
        ) : (
          <ul className="divide-y">
            {items.map((s) => (
              <li key={s.id} className="grid gap-1 py-3">
                <div className="flex items-center gap-2">
                  <Badge variant="secondary" className="text-[10px]">
                    {s.evidence_count}× repeats
                  </Badge>
                  <span className="text-sm font-medium">{s.title}</span>
                </div>
                <p className="text-sm text-muted-foreground">{s.description}</p>
              </li>
            ))}
          </ul>
        )}
      </CardContent>
    </Card>
  );
}

function ListSkeleton() {
  return (
    <ul className="divide-y">
      {Array.from({ length: 4 }).map((_, i) => (
        <li key={i} className="grid gap-2 py-3">
          <div className="flex items-center gap-2">
            <span className="h-4 w-16 animate-pulse rounded bg-muted" />
            <span className="h-3 w-32 animate-pulse rounded bg-muted" />
          </div>
          <span className={cn("h-4 animate-pulse rounded bg-muted", i % 2 ? "w-2/3" : "w-3/4")} />
        </li>
      ))}
    </ul>
  );
}

function EmptyInbox({ label }: { label: string }) {
  return (
    <div className="flex flex-col items-center justify-center gap-2 px-4 py-10 text-center">
      <InboxIcon className="size-8 text-muted-foreground/60" />
      <p className="text-sm font-medium">{label}</p>
      <Separator className="my-2 max-w-xs" />
      <p className="max-w-md text-xs text-muted-foreground">
        Trigger an extraction now from the command palette (<kbd>⌘K</kbd>) or run{" "}
        <code className="rounded bg-muted px-1">tw extract</code>.
      </p>
    </div>
  );
}

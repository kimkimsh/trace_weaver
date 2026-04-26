import{c as s,j as e,M as a,B as n}from"./index-Bn-lPNIf.js";import{C as t,a as i,c as r,b as d,d as o}from"./card-SHpF-bED.js";/**
 * @license lucide-react v0.469.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const c=s("ShieldCheck",[["path",{d:"M20 13c0 5-3.5 7.5-7.66 8.95a1 1 0 0 1-.67-.01C7.5 20.5 4 18 4 13V6a1 1 0 0 1 1-1c2 0 4.5-1.2 6.24-2.72a1.17 1.17 0 0 1 1.52 0C14.51 3.81 17 5 19 5a1 1 0 0 1 1 1z",key:"oel41y"}],["path",{d:"m9 12 2 2 4-4",key:"dzmm74"}]]);function x(){return e.jsxs("div",{className:"mx-auto flex w-full max-w-6xl flex-col gap-6",children:[e.jsxs("div",{children:[e.jsx("h1",{className:"text-2xl font-semibold tracking-tight",children:"Diff Approval"}),e.jsx("p",{className:"text-sm text-muted-foreground",children:"Side-by-side view of pending output writes with per-line provenance and a final secret rescan. No file is mutated until you approve."})]}),e.jsxs(t,{children:[e.jsxs(i,{className:"flex-row items-center justify-between",children:[e.jsxs("div",{className:"flex items-center gap-2",children:[e.jsx(a,{className:"size-5 text-muted-foreground"}),e.jsxs("div",{children:[e.jsx(r,{children:"AGENTS.md (project: trace_weaver)"}),e.jsx(d,{children:"+12 / −0 · 7 conventions, 3 skills"})]})]}),e.jsxs(n,{variant:"success",className:"gap-1",children:[e.jsx(c,{className:"size-3"})," Tier-3 redaction passed"]})]}),e.jsxs(o,{children:[e.jsxs("div",{className:"grid grid-cols-2 gap-4",children:[e.jsx("pre",{className:"max-h-[480px] overflow-auto rounded-md border bg-muted/30 p-3 font-mono text-xs leading-5",children:`<!-- tw-managed: do not edit by hand -->
## Conventions

- We use uv for all Python venv management.
- Daemon binds 127.0.0.1:7777 only.
- Redaction Tier 0 + Tier 1 run before any DB write.

## Skills

- traceweaver-output-regression: dry-run all 7 + snapshot.
- fastapi-websocket-debugging: diagnose disconnect cycles.
`}),e.jsx("pre",{className:"max-h-[480px] overflow-auto rounded-md border bg-success/5 p-3 font-mono text-xs leading-5 text-success",children:`<!-- tw-managed: do not edit by hand -->
## Conventions

- We use uv for all Python venv management.        # evidence ×6 · 78%
- Daemon binds 127.0.0.1:7777 only.                # evidence ×4 · 81%
- Redaction Tier 0 + Tier 1 run before any DB write. # evidence ×7 · 92%
+ - Pytest is the canonical test runner.            # evidence ×5 · 73%

## Skills

- traceweaver-output-regression: dry-run all 7 + snapshot.
- fastapi-websocket-debugging: diagnose disconnect cycles.
+ - agent-context-review: audit AGENTS.md / GEMINI.md drift.
`})]}),e.jsxs("p",{className:"mt-3 text-xs text-muted-foreground",children:["Real ",e.jsx("code",{children:"react-diff-view"})," integration arrives with B4-4 — this snapshot is populated from the daemon's ",e.jsx("code",{children:"POST /api/v1/apply?dry_run=true"})," response once that wiring is complete."]})]})]})]})}export{x as component};
//# sourceMappingURL=diff-CXLWjhRj.js.map

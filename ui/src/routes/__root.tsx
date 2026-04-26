import { Outlet, createRootRouteWithContext } from "@tanstack/react-router";
import type { QueryClient } from "@tanstack/react-query";
import { Sidebar } from "@/components/layout/Sidebar";
import { Header } from "@/components/layout/Header";
import { CommandPalette } from "@/components/layout/CommandPalette";

interface RouterContext {
  queryClient: QueryClient;
}

export const Route = createRootRouteWithContext<RouterContext>()({
  component: RootLayout,
});

function RootLayout() {
  return (
    <div className="grid h-screen grid-cols-[14rem_1fr] grid-rows-[3.5rem_1fr]">
      <div className="row-span-2">
        <Sidebar />
      </div>
      <Header />
      <main className="overflow-y-auto bg-muted/30 px-8 py-6">
        <Outlet />
      </main>
      <CommandPalette />
    </div>
  );
}

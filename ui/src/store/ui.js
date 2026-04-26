import { create } from "zustand";
export const useUi = create((set) => ({
    commandPaletteOpen: false,
    setCommandPaletteOpen: (open) => set({ commandPaletteOpen: open }),
    toggleCommandPalette: () => set((s) => ({ commandPaletteOpen: !s.commandPaletteOpen })),
    theme: "system",
    setTheme: (theme) => {
        const root = document.documentElement;
        if (theme === "dark" || (theme === "system" && window.matchMedia("(prefers-color-scheme: dark)").matches)) {
            root.classList.add("dark");
        }
        else {
            root.classList.remove("dark");
        }
        try {
            localStorage.setItem("tw-theme", theme);
        }
        catch {
            /* ignore — private mode */
        }
        set({ theme });
    },
}));

import { clsx } from "clsx";
import { twMerge } from "tailwind-merge";
export function cn(...inputs) {
    return twMerge(clsx(inputs));
}
export function formatDuration(ms) {
    if (ms < 1000)
        return `${ms} ms`;
    if (ms < 60_000)
        return `${(ms / 1000).toFixed(1)} s`;
    if (ms < 3_600_000)
        return `${Math.floor(ms / 60_000)}m ${Math.floor((ms % 60_000) / 1000)}s`;
    return `${Math.floor(ms / 3_600_000)}h ${Math.floor((ms % 3_600_000) / 60_000)}m`;
}
export function formatBytes(bytes) {
    if (bytes < 1024)
        return `${bytes} B`;
    if (bytes < 1024 * 1024)
        return `${(bytes / 1024).toFixed(1)} KB`;
    if (bytes < 1024 * 1024 * 1024)
        return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
    return `${(bytes / (1024 * 1024 * 1024)).toFixed(2)} GB`;
}
export function formatRelativeTime(tsNs, now = Date.now()) {
    const diffMs = now - tsNs / 1_000_000;
    if (diffMs < 60_000)
        return "just now";
    if (diffMs < 3_600_000)
        return `${Math.floor(diffMs / 60_000)}m ago`;
    if (diffMs < 86_400_000)
        return `${Math.floor(diffMs / 3_600_000)}h ago`;
    return `${Math.floor(diffMs / 86_400_000)}d ago`;
}

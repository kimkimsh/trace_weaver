import { jsx as _jsx, jsxs as _jsxs } from "react/jsx-runtime";
import * as React from "react";
import * as ScrollAreaPrimitive from "@radix-ui/react-scroll-area";
import { cn } from "@/lib/utils";
export const ScrollArea = React.forwardRef(({ className, children, ...props }, ref) => (_jsxs(ScrollAreaPrimitive.Root, { ref: ref, className: cn("relative overflow-hidden", className), ...props, children: [_jsx(ScrollAreaPrimitive.Viewport, { className: "h-full w-full rounded-[inherit]", children: children }), _jsx(ScrollAreaPrimitive.Scrollbar, { orientation: "vertical", className: "flex h-full w-2 touch-none select-none border-l border-l-transparent p-px transition-colors", children: _jsx(ScrollAreaPrimitive.Thumb, { className: "relative flex-1 rounded-full bg-border" }) }), _jsx(ScrollAreaPrimitive.Corner, {})] })));
ScrollArea.displayName = "ScrollArea";

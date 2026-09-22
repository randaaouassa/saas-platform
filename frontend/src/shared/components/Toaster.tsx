import type { ToastKind } from "../stores/toast";
import { useToastStore } from "../stores/toast";

const ICONS: Record<ToastKind, string> = {
    success: "✓",
    error: "✕",
    info: "i",
};

const COLORS: Record<ToastKind, { fg: string; bg: string; border: string }> = {
    success: {
        fg: "#86efac",
        bg: "rgba(52, 211, 153, 0.12)",
        border: "rgba(52, 211, 153, 0.3)",
    },
    error: {
        fg: "#fca5a5",
        bg: "rgba(248, 113, 113, 0.12)",
        border: "rgba(248, 113, 113, 0.3)",
    },
    info: {
        fg: "#93c5fd",
        bg: "rgba(96, 165, 250, 0.12)",
        border: "rgba(96, 165, 250, 0.3)",
    },
};

export default function Toaster() {
    const toasts = useToastStore((s) => s.toasts);
    const dismiss = useToastStore((s) => s.dismiss);

    return (
        <div className="fixed top-4 right-4 z-[200] flex flex-col gap-2 w-80 max-w-[calc(100vw-2rem)]">
            {toasts.map((t) => {
                const c = COLORS[t.kind];
                return (
                    <div
                        key={t.id}
                        className="toast-enter glass p-4 flex items-start gap-3 cursor-pointer"
                        style={{
                            background: c.bg,
                            border: `1px solid ${c.border}`,
                        }}
                        onClick={() => dismiss(t.id)}
                    >
                        <div
                            className="w-6 h-6 rounded-full flex items-center justify-center text-xs font-bold shrink-0"
                            style={{ color: c.fg, background: "rgba(0,0,0,0.25)" }}
                        >
                            {ICONS[t.kind]}
                        </div>
                        <div className="min-w-0 flex-1">
                            <div className="text-sm font-medium" style={{ color: c.fg }}>
                                {t.title}
                            </div>
                            {t.description && (
                                <div className="text-dim text-xs mt-0.5 break-words">
                                    {t.description}
                                </div>
                            )}
                        </div>
                    </div>
                );
            })}
        </div>
    );
}
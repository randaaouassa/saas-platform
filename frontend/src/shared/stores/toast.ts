import { create } from "zustand";

export type ToastKind = "success" | "error" | "info";

export interface Toast {
    id: string;
    kind: ToastKind;
    title: string;
    description?: string;
    duration: number;
}

interface ToastState {
    toasts: Toast[];
    push: (t: Omit<Toast, "id" | "duration"> & { duration?: number }) => void;
    dismiss: (id: string) => void;
}

export const useToastStore = create<ToastState>((set) => ({
    toasts: [],
    push: ({ kind, title, description, duration = 4000 }) => {
        const id = Math.random().toString(36).slice(2);
        set((s) => ({
            toasts: [...s.toasts, { id, kind, title, description, duration }],
        }));
        setTimeout(() => {
            set((s) => ({ toasts: s.toasts.filter((t) => t.id !== id) }));
        }, duration);
    },
    dismiss: (id) =>
        set((s) => ({ toasts: s.toasts.filter((t) => t.id !== id) })),
}));

export const toast = {
    success: (title: string, description?: string) =>
        useToastStore.getState().push({ kind: "success", title, description }),
    error: (title: string, description?: string) =>
        useToastStore.getState().push({ kind: "error", title, description }),
    info: (title: string, description?: string) =>
        useToastStore.getState().push({ kind: "info", title, description }),
};
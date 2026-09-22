import type { StatusKind } from "../lib/status";
import { humanize, statusKind } from "../lib/status";

interface Props {
    domain:
    | "order"
    | "delivery"
    | "driver"
    | "task"
    | "assignment"
    | "route"
    | "org"
    | "channel";
    value: string | null | undefined;
    className?: string;
}

const DOT: Record<StatusKind, string> = {
    neutral: "bg-zinc-400",
    success: "bg-emerald-400",
    warning: "bg-amber-400",
    danger: "bg-red-400",
    info: "bg-blue-400",
    accent: "bg-purple-400",
};

export default function StatusBadge({ domain, value, className = "" }: Props) {
    const kind = statusKind(domain, value);
    return (
        <span className={`status status-${kind} ${className}`}>
            <span
                className={`inline-block w-1.5 h-1.5 rounded-full ${DOT[kind]}`}
                style={{ boxShadow: "0 0 8px currentColor", opacity: 0.85 }}
            />
            {humanize(value)}
        </span>
    );
}
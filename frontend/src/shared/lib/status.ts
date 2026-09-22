export type StatusKind =
    | "neutral"
    | "success"
    | "warning"
    | "danger"
    | "info"
    | "accent";

const ORDER_STATUS: Record<string, StatusKind> = {
    draft: "neutral",
    confirmed: "info",
    reserved: "accent",
    picking: "accent",
    packed: "accent",
    ready_for_dispatch: "info",
    dispatched: "info",
    delivered: "success",
    cancelled: "danger",
    on_hold: "warning",
};

const DELIVERY_STATUS: Record<string, StatusKind> = {
    pending: "neutral",
    assigned: "info",
    picked_up: "accent",
    in_transit: "accent",
    delivered: "success",
    failed: "danger",
    rescheduled: "warning",
    returned: "warning",
    cancelled: "danger",
};

const DRIVER_STATUS: Record<string, StatusKind> = {
    offline: "neutral",
    available: "success",
    assigned: "info",
    on_delivery: "accent",
    on_break: "warning",
};

const TASK_STATUS: Record<string, StatusKind> = {
    pending: "neutral",
    in_progress: "accent",
    completed: "success",
    cancelled: "danger",
};

const ASSIGNMENT_STATUS: Record<string, StatusKind> = {
    offered: "info",
    accepted: "success",
    rejected: "danger",
    expired: "neutral",
    completed: "success",
};

const ROUTE_STATUS: Record<string, StatusKind> = {
    planned: "neutral",
    active: "accent",
    completed: "success",
    cancelled: "danger",
};

const ORG_STATUS: Record<string, StatusKind> = {
    active: "success",
    suspended: "danger",
};

const CHANNEL_KIND: Record<string, StatusKind> = {
    inapp: "neutral",
    email: "info",
    sms: "accent",
    push: "warning",
};

export const STATUS_MAPS = {
    order: ORDER_STATUS,
    delivery: DELIVERY_STATUS,
    driver: DRIVER_STATUS,
    task: TASK_STATUS,
    assignment: ASSIGNMENT_STATUS,
    route: ROUTE_STATUS,
    org: ORG_STATUS,
    channel: CHANNEL_KIND,
};

export function statusKind(
    domain: keyof typeof STATUS_MAPS,
    value: string | null | undefined,
): StatusKind {
    if (!value) return "neutral";
    return STATUS_MAPS[domain][value] ?? "neutral";
}

export function humanize(value: string | null | undefined): string {
    if (!value) return "";
    return value.replace(/_/g, " ");
}
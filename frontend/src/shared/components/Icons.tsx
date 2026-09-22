interface IconProps {
    className?: string;
}

const base = "w-6 h-6 stroke-current fill-none";

export function IconWarehouse({ className = "" }: IconProps) {
    return (
        <svg className={`${base} ${className}`} viewBox="0 0 24 24" strokeWidth="1.6" strokeLinecap="round" strokeLinejoin="round">
            <path d="M3 21V9l9-6 9 6v12" />
            <path d="M9 21v-6h6v6" />
        </svg>
    );
}

export function IconPackage({ className = "" }: IconProps) {
    return (
        <svg className={`${base} ${className}`} viewBox="0 0 24 24" strokeWidth="1.6" strokeLinecap="round" strokeLinejoin="round">
            <path d="M21 8l-9-5-9 5 9 5 9-5z" />
            <path d="M3 8v8l9 5 9-5V8" />
            <path d="M12 13v8" />
        </svg>
    );
}

export function IconCart({ className = "" }: IconProps) {
    return (
        <svg className={`${base} ${className}`} viewBox="0 0 24 24" strokeWidth="1.6" strokeLinecap="round" strokeLinejoin="round">
            <circle cx="9" cy="20" r="1.5" />
            <circle cx="18" cy="20" r="1.5" />
            <path d="M3 4h2l2.4 11.2a1 1 0 0 0 1 .8h10.4a1 1 0 0 0 1-.8L21 8H6" />
        </svg>
    );
}

export function IconTruck({ className = "" }: IconProps) {
    return (
        <svg className={`${base} ${className}`} viewBox="0 0 24 24" strokeWidth="1.6" strokeLinecap="round" strokeLinejoin="round">
            <path d="M3 6h11v10H3z" />
            <path d="M14 10h4l3 3v3h-7" />
            <circle cx="7" cy="18" r="1.6" />
            <circle cx="17" cy="18" r="1.6" />
        </svg>
    );
}

export function IconBrain({ className = "" }: IconProps) {
    return (
        <svg className={`${base} ${className}`} viewBox="0 0 24 24" strokeWidth="1.6" strokeLinecap="round" strokeLinejoin="round">
            <path d="M9 4a3 3 0 0 0-3 3v1a3 3 0 0 0-1 5 3 3 0 0 0 1 5v1a3 3 0 0 0 6 0V6a2 2 0 0 0-3-2z" />
            <path d="M15 4a3 3 0 0 1 3 3v1a3 3 0 0 1 1 5 3 3 0 0 1-1 5v1a3 3 0 0 1-6 0" />
        </svg>
    );
}

export function IconRoute({ className = "" }: IconProps) {
    return (
        <svg className={`${base} ${className}`} viewBox="0 0 24 24" strokeWidth="1.6" strokeLinecap="round" strokeLinejoin="round">
            <circle cx="6" cy="19" r="2.5" />
            <circle cx="18" cy="5" r="2.5" />
            <path d="M8.5 19h4a4 4 0 0 0 0-8h-1a4 4 0 0 1 0-8h4" />
        </svg>
    );
}

export function IconSignal({ className = "" }: IconProps) {
    return (
        <svg className={`${base} ${className}`} viewBox="0 0 24 24" strokeWidth="1.6" strokeLinecap="round" strokeLinejoin="round">
            <path d="M4 20a16 16 0 0 1 16 0" />
            <path d="M8 16a8 8 0 0 1 8 0" />
            <circle cx="12" cy="19.5" r="0.6" fill="currentColor" />
        </svg>
    );
}

export function IconChart({ className = "" }: IconProps) {
    return (
        <svg className={`${base} ${className}`} viewBox="0 0 24 24" strokeWidth="1.6" strokeLinecap="round" strokeLinejoin="round">
            <path d="M4 20V10" />
            <path d="M10 20V4" />
            <path d="M16 20v-7" />
            <path d="M22 20H2" />
        </svg>
    );
}

export function IconShield({ className = "" }: IconProps) {
    return (
        <svg className={`${base} ${className}`} viewBox="0 0 24 24" strokeWidth="1.6" strokeLinecap="round" strokeLinejoin="round">
            <path d="M12 3l8 3v6c0 5-3.5 8-8 9-4.5-1-8-4-8-9V6z" />
            <path d="M9 12l2 2 4-4" />
        </svg>
    );
}

export function IconDriver({ className = "" }: IconProps) {
    return (
        <svg className={`${base} ${className}`} viewBox="0 0 24 24" strokeWidth="1.6" strokeLinecap="round" strokeLinejoin="round">
            <circle cx="12" cy="7" r="3" />
            <path d="M5 21v-3a5 5 0 0 1 5-5h4a5 5 0 0 1 5 5v3" />
        </svg>
    );
}

export function IconDispatcher({ className = "" }: IconProps) {
    return (
        <svg className={`${base} ${className}`} viewBox="0 0 24 24" strokeWidth="1.6" strokeLinecap="round" strokeLinejoin="round">
            <circle cx="12" cy="12" r="9" />
            <path d="M12 3v3" />
            <path d="M12 18v3" />
            <path d="M3 12h3" />
            <path d="M18 12h3" />
            <circle cx="12" cy="12" r="3" />
        </svg>
    );
}

export function IconAdmin({ className = "" }: IconProps) {
    return (
        <svg className={`${base} ${className}`} viewBox="0 0 24 24" strokeWidth="1.6" strokeLinecap="round" strokeLinejoin="round">
            <circle cx="12" cy="12" r="9" />
            <path d="M3 12h18" />
            <path d="M12 3a15 15 0 0 1 0 18a15 15 0 0 1 0-18z" />
        </svg>
    );
}

export function IconBell({ className = "" }: IconProps) {
    return (
        <svg className={`${base} ${className}`} viewBox="0 0 24 24" strokeWidth="1.6" strokeLinecap="round" strokeLinejoin="round">
            <path d="M6 8a6 6 0 1 1 12 0c0 7 3 7 3 7H3s3 0 3-7z" />
            <path d="M10 20a2 2 0 0 0 4 0" />
        </svg>
    );
}

export function IconCheck({ className = "" }: IconProps) {
    return (
        <svg className={`${base} ${className}`} viewBox="0 0 24 24" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
            <path d="M5 12l5 5L20 7" />
        </svg>
    );
}

export function IconArrow({ className = "" }: IconProps) {
    return (
        <svg className={`${base} ${className}`} viewBox="0 0 24 24" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
            <path d="M5 12h14" />
            <path d="M13 5l7 7-7 7" />
        </svg>
    );
}

export function IconSparkle({ className = "" }: IconProps) {
    return (
        <svg className={`${base} ${className}`} viewBox="0 0 24 24" strokeWidth="1.6" strokeLinecap="round" strokeLinejoin="round">
            <path d="M12 3v6" />
            <path d="M12 15v6" />
            <path d="M3 12h6" />
            <path d="M15 12h6" />
            <path d="M6 6l3 3" />
            <path d="M15 15l3 3" />
            <path d="M6 18l3-3" />
            <path d="M15 9l3-3" />
        </svg>
    );
}

export function IconLock({ className = "" }: IconProps) {
    return (
        <svg className={`${base} ${className}`} viewBox="0 0 24 24" strokeWidth="1.6" strokeLinecap="round" strokeLinejoin="round">
            <rect x="4" y="11" width="16" height="10" rx="2" />
            <path d="M8 11V8a4 4 0 1 1 8 0v3" />
        </svg>
    );
}
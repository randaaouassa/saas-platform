interface BlockProps {
    className?: string;
    style?: React.CSSProperties;
}

export function SkeletonBlock({ className = "", style }: BlockProps) {
    return <div className={`skeleton ${className}`} style={style} />;
}

export function SkeletonText({ width = "100%" }: { width?: string }) {
    return <SkeletonBlock className="h-4" style={{ width }} />;
}

export function SkeletonHeading() {
    return <SkeletonBlock className="h-8 w-48" />;
}

export function SkeletonCard() {
    return (
        <div className="glass p-5 space-y-3">
            <SkeletonBlock className="h-4 w-24" />
            <SkeletonBlock className="h-8 w-32" />
        </div>
    );
}

export function SkeletonCards({ count = 3 }: { count?: number }) {
    return (
        <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
            {Array.from({ length: count }).map((_, i) => (
                <SkeletonCard key={i} />
            ))}
        </div>
    );
}

export function SkeletonTable({ rows = 5, cols = 4 }: { rows?: number; cols?: number }) {
    return (
        <div className="glass overflow-hidden">
            <div className="px-4 py-3 flex gap-4 border-b border-white/5">
                {Array.from({ length: cols }).map((_, i) => (
                    <SkeletonBlock key={i} className="h-3 flex-1" />
                ))}
            </div>
            {Array.from({ length: rows }).map((_, r) => (
                <div key={r} className="px-4 py-4 flex gap-4 border-b border-white/5 last:border-0">
                    {Array.from({ length: cols }).map((_, c) => (
                        <SkeletonBlock key={c} className="h-4 flex-1" />
                    ))}
                </div>
            ))}
        </div>
    );
}

export function SkeletonPageHeader() {
    return (
        <div className="flex items-center justify-between mb-6">
            <SkeletonHeading />
            <SkeletonBlock className="h-9 w-32 rounded-full" />
        </div>
    );
}
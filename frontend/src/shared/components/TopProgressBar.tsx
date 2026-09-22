import { useIsFetching, useIsMutating } from "@tanstack/react-query";
import { useEffect, useState } from "react";
import { useLocation } from "react-router-dom";

export default function TopProgressBar() {
    const isFetching = useIsFetching();
    const isMutating = useIsMutating();
    const location = useLocation();

    const active = isFetching > 0 || isMutating > 0;

    const [visible, setVisible] = useState(false);
    const [progress, setProgress] = useState(0);

    // Route change: quick fill
    useEffect(() => {
        setVisible(true);
        setProgress(20);
        const t1 = setTimeout(() => setProgress(60), 80);
        const t2 = setTimeout(() => setProgress(85), 250);
        const t3 = setTimeout(() => {
            setProgress(100);
            const t4 = setTimeout(() => {
                setVisible(false);
                setProgress(0);
            }, 220);
            return () => clearTimeout(t4);
        }, 400);
        return () => {
            clearTimeout(t1);
            clearTimeout(t2);
            clearTimeout(t3);
        };
    }, [location.pathname]);

    // Data fetching: gentle top bar
    useEffect(() => {
        if (active) {
            setVisible(true);
            setProgress((p) => (p < 30 ? 30 : p));
            const t = setInterval(() => {
                setProgress((p) => (p < 85 ? p + (85 - p) * 0.15 : p));
            }, 250);
            return () => clearInterval(t);
        }
        if (visible) {
            setProgress(100);
            const t = setTimeout(() => {
                setVisible(false);
                setProgress(0);
            }, 250);
            return () => clearTimeout(t);
        }
    }, [active]);

    if (!visible && progress === 0) return null;

    return (
        <div
            className="fixed top-0 left-0 right-0 z-[100] h-[2px] pointer-events-none"
            style={{ opacity: visible ? 1 : 0, transition: "opacity 200ms" }}
        >
            <div
                className="h-full"
                style={{
                    width: `${progress}%`,
                    background:
                        "linear-gradient(90deg, #7c3aed 0%, #a855f7 60%, #d8b4fe 100%)",
                    boxShadow: "0 0 12px rgba(168,85,247,0.7)",
                    transition: "width 250ms ease",
                }}
            />
        </div>
    );
}
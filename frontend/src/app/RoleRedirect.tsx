import { Navigate } from "react-router-dom";

import { homePathForRoles, useAuthStore } from "../shared/stores/auth";

export default function RoleRedirect() {
    const roles = useAuthStore((s) => s.user?.roles ?? null);
    return <Navigate to={homePathForRoles(roles)} replace />;
}
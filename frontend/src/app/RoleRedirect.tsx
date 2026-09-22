import { Navigate } from "react-router-dom";

import { homePathForRole, useRole } from "../shared/stores/auth";

export default function RoleRedirect() {
    const role = useRole();
    return <Navigate to={homePathForRole(role)} replace />;
}
import { Navigate, Route, Routes } from "react-router-dom";

import Layout from "./app/Layout";
import ProtectedRoute from "./app/ProtectedRoute";
import DashboardPage from "./features/analytics/DashboardPage";
import LoginPage from "./features/auth/LoginPage";
import RegisterPage from "./features/auth/RegisterPage";
import DeliveriesPage from "./features/deliveries/DeliveriesPage";
import DispatchPage from "./features/dispatch/DispatchPage";
import DriversPage from "./features/drivers/DriversPage";
import InventoryPage from "./features/inventory/InventoryPage";
import LandingPage from "./features/landing/LandingPage";
import NotificationsPage from "./features/notifications/NotificationsPage";
import OrdersPage from "./features/orders/OrdersPage";
import RoutingPage from "./features/routing/RoutingPage";
import TrackingPage from "./features/tracking/TrackingPage";
import WarehousesPage from "./features/warehouses/WarehousesPage";

export default function App() {
  return (
    <Routes>
      <Route path="/" element={<LandingPage />} />
      <Route path="/login" element={<LoginPage />} />
      <Route path="/register" element={<RegisterPage />} />
      <Route path="/track/:id" element={<TrackingPage />} />
      <Route
        element={
          <ProtectedRoute>
            <Layout />
          </ProtectedRoute>
        }
      >
        <Route path="/dashboard" element={<DashboardPage />} />
        <Route path="/warehouses" element={<WarehousesPage />} />
        <Route path="/inventory" element={<InventoryPage />} />
        <Route path="/orders" element={<OrdersPage />} />
        <Route path="/deliveries" element={<DeliveriesPage />} />
        <Route path="/drivers" element={<DriversPage />} />
        <Route path="/dispatch" element={<DispatchPage />} />
        <Route path="/routing" element={<RoutingPage />} />
        <Route path="/notifications" element={<NotificationsPage />} />
      </Route>
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  );
}
import { Navigate, Route, Routes } from "react-router-dom";

import AppLayout from "./app/AppLayout";
import DispatcherLayout from "./app/DispatcherLayout";
import DriverLayout from "./app/DriverLayout";
import ProtectedRoute from "./app/ProtectedRoute";
import RoleRedirect from "./app/RoleRedirect";
import WarehouseLayout from "./app/WarehouseLayout";
import AnalyticsPage from "./features/analytics/AnalyticsPage";
import DashboardPage from "./features/analytics/DashboardPage";
import AcceptInvitePage from "./features/auth/AcceptInvitePage";
import LoginPage from "./features/auth/LoginPage";
import RegisterPage from "./features/auth/RegisterPage";
import DeliveriesPage from "./features/deliveries/DeliveriesPage";
import DeliveryDetailPage from "./features/deliveries/DeliveryDetailPage";
import DispatchPage from "./features/dispatch/DispatchPage";
import DispatcherHome from "./features/dispatcher/DispatcherHome";
import DriverHome from "./features/driver/DriverHome";
import DriverDetailPage from "./features/drivers/DriverDetailPage";
import DriversPage from "./features/drivers/DriversPage";
import InventoryPage from "./features/inventory/InventoryPage";
import LandingPage from "./features/landing/LandingPage";
import NotificationsPage from "./features/notifications/NotificationsPage";
import OrderDetailPage from "./features/orders/OrderDetailPage";
import OrdersPage from "./features/orders/OrdersPage";
import RoutingPage from "./features/routing/RoutingPage";
import SettingsPage from "./features/settings/SettingsPage";
import TrackingPage from "./features/tracking/TrackingPage";
import UsersPage from "./features/users/UsersPage";
import WarehouseHome from "./features/warehouse/WarehouseHome";
import WarehousesPage from "./features/warehouses/WarehousesPage";

export default function App() {
  return (
    <Routes>
      <Route path="/" element={<LandingPage />} />
      <Route path="/login" element={<LoginPage />} />
      <Route path="/register" element={<RegisterPage />} />
      <Route path="/invite" element={<AcceptInvitePage />} />
      <Route path="/track/:token" element={<TrackingPage />} />

      <Route
        element={
          <ProtectedRoute>
            <AppLayout />
          </ProtectedRoute>
        }
      >
        <Route path="/dashboard" element={<DashboardPage />} />
        <Route path="/analytics" element={<AnalyticsPage />} />
        <Route path="/warehouses" element={<WarehousesPage />} />
        <Route path="/inventory" element={<InventoryPage />} />
        <Route path="/orders" element={<OrdersPage />} />
        <Route path="/orders/:id" element={<OrderDetailPage />} />
        <Route path="/deliveries" element={<DeliveriesPage />} />
        <Route path="/deliveries/:id" element={<DeliveryDetailPage />} />
        <Route path="/drivers" element={<DriversPage />} />
        <Route path="/drivers/:id" element={<DriverDetailPage />} />
        <Route path="/dispatch" element={<DispatchPage />} />
        <Route path="/routing" element={<RoutingPage />} />
        <Route path="/notifications" element={<NotificationsPage />} />
        <Route path="/users" element={<UsersPage />} />
        <Route path="/settings" element={<SettingsPage />} />
      </Route>

      <Route
        element={
          <ProtectedRoute>
            <DispatcherLayout />
          </ProtectedRoute>
        }
      >
        <Route path="/dispatcher" element={<DispatcherHome />} />
        <Route path="/dispatcher/dispatch" element={<DispatchPage />} />
        <Route path="/dispatcher/routing" element={<RoutingPage />} />
        <Route path="/dispatcher/drivers" element={<DriversPage />} />
        <Route path="/dispatcher/drivers/:id" element={<DriverDetailPage />} />
        <Route path="/dispatcher/deliveries" element={<DeliveriesPage />} />
        <Route path="/dispatcher/deliveries/:id" element={<DeliveryDetailPage />} />
        <Route path="/dispatcher/notifications" element={<NotificationsPage />} />
      </Route>

      <Route
        element={
          <ProtectedRoute>
            <DriverLayout />
          </ProtectedRoute>
        }
      >
        <Route path="/driver" element={<DriverHome />} />
        <Route path="/driver/deliveries/:id" element={<DeliveryDetailPage />} />
        <Route path="/driver/notifications" element={<NotificationsPage />} />
      </Route>

      <Route
        element={
          <ProtectedRoute>
            <WarehouseLayout />
          </ProtectedRoute>
        }
      >
        <Route path="/warehouse" element={<WarehouseHome />} />
        <Route path="/warehouse/warehouses" element={<WarehousesPage />} />
        <Route path="/warehouse/inventory" element={<InventoryPage />} />
        <Route path="/warehouse/orders" element={<OrdersPage />} />
        <Route path="/warehouse/orders/:id" element={<OrderDetailPage />} />
        <Route path="/warehouse/deliveries" element={<DeliveriesPage />} />
        <Route path="/warehouse/deliveries/:id" element={<DeliveryDetailPage />} />
        <Route path="/warehouse/notifications" element={<NotificationsPage />} />
      </Route>

      <Route path="/home" element={<RoleRedirect />} />
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  );
}
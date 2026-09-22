import { Navigate, Route, Routes } from "react-router-dom";

import AppLayout from "./app/AppLayout";
import DispatcherLayout from "./app/DispatcherLayout";
import DriverLayout from "./app/DriverLayout";
import ProtectedRoute from "./app/ProtectedRoute";
import RoleRedirect from "./app/RoleRedirect";
import WarehouseLayout from "./app/WarehouseLayout";
import DashboardPage from "./features/analytics/DashboardPage";
import LoginPage from "./features/auth/LoginPage";
import RegisterPage from "./features/auth/RegisterPage";
import DeliveriesPage from "./features/deliveries/DeliveriesPage";
import DispatchPage from "./features/dispatch/DispatchPage";
import DispatcherHome from "./features/dispatcher/DispatcherHome";
import DriverHome from "./features/driver/DriverHome";
import DriversPage from "./features/drivers/DriversPage";
import InventoryPage from "./features/inventory/InventoryPage";
import LandingPage from "./features/landing/LandingPage";
import NotificationsPage from "./features/notifications/NotificationsPage";
import OrdersPage from "./features/orders/OrdersPage";
import RoutingPage from "./features/routing/RoutingPage";
import TrackingPage from "./features/tracking/TrackingPage";
import WarehouseHome from "./features/warehouse/WarehouseHome";
import WarehousesPage from "./features/warehouses/WarehousesPage";

export default function App() {
  return (
    <Routes>
      <Route path="/" element={<LandingPage />} />
      <Route path="/login" element={<LoginPage />} />
      <Route path="/register" element={<RegisterPage />} />
      <Route path="/track/:token" element={<TrackingPage />} />

      {/* Admin */}
      <Route
        element={
          <ProtectedRoute>
            <AppLayout />
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

      {/* Dispatcher */}
      <Route
        element={
          <ProtectedRoute>
            <DispatcherLayout />
          </ProtectedRoute>
        }
      >
        <Route path="/dispatcher" element={<DispatcherHome />} />
        <Route path="/dispatcher/dispatch" element={<DispatchPage />} />
      </Route>

      {/* Driver */}
      <Route
        element={
          <ProtectedRoute>
            <DriverLayout />
          </ProtectedRoute>
        }
      >
        <Route path="/driver" element={<DriverHome />} />
        <Route path="/driver/notifications" element={<NotificationsPage />} />
      </Route>

      {/* Warehouse */}
      <Route
        element={
          <ProtectedRoute>
            <WarehouseLayout />
          </ProtectedRoute>
        }
      >
        <Route path="/warehouse" element={<WarehouseHome />} />
        <Route path="/warehouse/inventory" element={<InventoryPage />} />
        <Route path="/warehouse/orders" element={<OrdersPage />} />
        <Route path="/warehouse/deliveries" element={<DeliveriesPage />} />
      </Route>

      <Route path="/home" element={<RoleRedirect />} />
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  );
}
import { Navigate, Outlet } from "react-router-dom";
import { getRole, isAuthenticated } from "../utils/auth";

export function ProtectedRoute() {
  return isAuthenticated() ? <Outlet /> : <Navigate to="/login" replace />;
}

export function AdminRoute() {
  return getRole() === "admin" ? <Outlet /> : <Navigate to="/" replace />;
}

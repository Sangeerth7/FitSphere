import { BrowserRouter, Navigate, Route, Routes } from "react-router-dom";
import DashboardLayout from "./layout/DashboardLayout";
import { AdminRoute, ProtectedRoute } from "./routes/routeGuards";
import Login from "./pages/Login";
import Dashboard from "./pages/Dashboard";
import Members from "./pages/Members";
import Trainers from "./pages/Trainers";
import Plans from "./pages/Plans";
import Enrollments from "./pages/Enrollments";
import Payments from "./pages/Payments";
import Attendance from "./pages/Attendance";
import Workouts from "./pages/Workouts";
import DietPlans from "./pages/DietPlans";

export default function App() {
  return <BrowserRouter><Routes><Route path="/login" element={<Login />} /><Route element={<ProtectedRoute />}><Route element={<DashboardLayout />}><Route index element={<Dashboard />} /><Route path="members" element={<Members />} /><Route path="trainers" element={<Trainers />} /><Route path="plans" element={<AdminRoute />}><Route index element={<Plans />} /></Route><Route path="enrollments" element={<Enrollments />} /><Route path="payments" element={<Payments />} /><Route path="attendance" element={<Attendance />} /><Route path="workouts" element={<Workouts />} /><Route path="diets" element={<DietPlans />} /></Route></Route><Route path="*" element={<Navigate to="/" replace />} /></Routes></BrowserRouter>;
}
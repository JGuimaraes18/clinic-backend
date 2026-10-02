import { Routes, Route } from "react-router-dom";
import AppLayout from "@/components/layout/AppLayout";
import PrivateRoute from "@/components/auth/PrivateRoute";
import Login from "@/pages/Login";
import Home from "@/pages/Home";
import Professionals from "@/pages/Professionals";
import Patients from "@/pages/Patients";
import Appointments from "@/pages/Appointments";
import NotFound from "@/pages/NotFound";
import Attendance from "@/pages/Attendance";
import AppointmentsCalendar from "@/pages/AppointmentsCalendar";
import Users from "@/pages/Users";
import Clinics from "@/pages/Clinics";
import ForgotPassword from "@/pages/ForgotPassword";
import ResetPassword from "@/pages/ResetPassword";
import Settings from "@/pages/Settings";
import AuditLogs from "@/pages/AuditLogs";
import ForcePasswordChange from "@/pages/ForcePasswordChange";


export default function AppRoutes() {
  return (
    <Routes>
      <Route path="/login" element={<Login />} />
      <Route path="/forgot-password" element={<ForgotPassword />} />
      <Route path="/reset-password" element={<ResetPassword />} />

      <Route element={<PrivateRoute />}>
        <Route path="/force-password-change" element={<ForcePasswordChange />} />
        <Route element={<AppLayout />}>
          <Route index element={<Home />} />
          <Route path="agendamentos" element={<Appointments />} />
          <Route path="calendar" element={<AppointmentsCalendar />} />
          <Route path="pacientes" element={<Patients />} />
          <Route path="profissionais" element={<Professionals />} />
          <Route path="atendimento/:id" element={<Attendance />} />
          <Route path="usuarios" element={<Users />} />
          <Route path="clinicas" element={<Clinics />} />
          <Route path="settings" element={<Settings />} />
          <Route path="audit-logs" element={<AuditLogs />} />
        </Route>
      </Route>

      <Route path="*" element={<NotFound />} />
    </Routes>
  );
}
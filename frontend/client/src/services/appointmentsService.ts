import api from "./api";
import { Appointment, AppointmentForm, StartAttendanceResponse } from "@/types/appointment";

export async function getAppointments(): Promise<Appointment[]> {
  const response = await api.get("/api/appointments/");
  return response.data;
}

export async function createAppointment(data: any): Promise<Appointment> {
  const response = await api.post("/api/appointments/", data);
  return response.data;
}

export async function updateAppointment(
  id: number,
  data: AppointmentForm
): Promise<Appointment> {
  const response = await api.put(`/api/appointments/${id}/`, data);
  return response.data;
}

export async function getAppointmentById(
  id: number
): Promise<Appointment> {
  const response = await api.get(`/api/appointments/${id}/`);
  return response.data;
}

export async function startAppointmentAttendance(
  id: number
): Promise<StartAttendanceResponse> {
  const response = await api.post(
    `/api/appointments/${id}/start_attendance/`
  );

  return response.data;
}
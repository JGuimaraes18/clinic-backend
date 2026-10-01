import api from "./api";
import { Clinic, ClinicForm } from "@/types/clinic";

// ==============================
// GET ALL
// ==============================
export async function getClinics(): Promise<Clinic[]> {
  const response = await api.get("/api/clinics/");
  return response.data;
}

// ==============================
// GET ONE
// ==============================
export async function getClinic(id: number): Promise<Clinic> {
  const response = await api.get(`/api/clinics/${id}/`);
  return response.data;
}

// ==============================
// CREATE
// ==============================
export async function createClinic(
  data: ClinicForm
): Promise<Clinic> {
  const response = await api.post("/api/clinics/", data);
  return response.data;
}

// ==============================
// UPDATE
// ==============================
export async function updateClinic(
  id: number,
  data: Partial<ClinicForm & { is_active: boolean }>
): Promise<Clinic> {
  const response = await api.patch(`/api/clinics/${id}/`, data);
  return response.data;
}

// ==============================
// DELETE
// ==============================
export async function deleteClinic(id: number): Promise<void> {
  await api.delete(`/api/clinics/${id}/`);
}

// ==============================
// TOGGLE ACTIVE
// ==============================
export async function toggleClinicActive(
  id: number,
  is_active: boolean
): Promise<Clinic> {
  const response = await api.patch(`/api/clinics/${id}/`, { is_active });
  return response.data;
}

// ==============================
// RESET ADMIN PASSWORD
// ==============================
export async function resetClinicAdminPassword(
  id: number
): Promise<{ detail: string; temporary_password: string; admin_email: string }> {
  const response = await api.post(`/api/clinics/${id}/reset-admin-password/`);
  return response.data;
}
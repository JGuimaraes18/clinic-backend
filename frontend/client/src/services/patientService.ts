import api from "./api";
import { Patient, PatientForm } from "@/types/patient";


export async function getPatients(): Promise<Patient[]> {
  const response = await api.get("/api/patients/");
  return response.data;
}

export async function createPatient(data: any): Promise<Patient> {
  const response = await api.post("/api/patients/", data);
  return response.data;
}

export async function updatePatient(
  id: number,
  data: PatientForm
): Promise<Patient> {
  const response = await api.put(`/api/patients/${id}/`, data);
  return response.data;
}
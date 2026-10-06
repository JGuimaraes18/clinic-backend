import api from "./api";
import { Professional, ProfessionalForm } from "@/types/professional";

export async function getProfessionals(): Promise<Professional[]> {
  const response = await api.get("/api/professionals/");
  return response.data;
}

export async function createProfessional(
  data: ProfessionalForm
): Promise<Professional> {
  const response = await api.post("/api/professionals/", data);
  return response.data;
}

export async function updateProfessional(
  id: number,
  data: ProfessionalForm
): Promise<Professional> {
  const response = await api.patch(`/api/professionals/${id}/`, data);
  return response.data;
}
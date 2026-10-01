import api from "./api";
import { Professional } from "@/types/professional";

export async function getProfessionals(): Promise<Professional[]> {
  const response = await api.get("/api/professionals/");
  console.log("Response from getProfessionals:", response);
  return response.data;
}

export async function createProfessional(data: any): Promise<Professional> {
  const response = await api.post("/api/professionals/", data);
  return response.data;
}

export async function updateProfessional(id: number, data: any) {
  const response = await api.patch(`/api/professionals/${id}/`, data);
  return response.data;
}
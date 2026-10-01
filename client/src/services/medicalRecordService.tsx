import api from "./api";

export interface MedicalRecord {
  id: number;
  hash_integridade: string | null;
  conteudo: string;
  status: "RASCUNHO" | "FECHADO";
  criado_em: string;
  finalizado_em: string | null;
  atendimento: number;
  finalizado_por: number | null;
}

export interface MedicalRecordCreate {
  conteudo: string;
  atendimento: number;
}

export async function getMedicalRecords() {
  const response = await api.get<MedicalRecord[]>("/api/medical-records/");
  return response.data;
}

export async function getMedicalRecordById(id: number) {
  const response = await api.get<MedicalRecord>(
    `/api/medical-records/${id}/`
  );
  return response.data;
}

export async function createMedicalRecord(data: MedicalRecordCreate) {
  const response = await api.post<MedicalRecord>(
    "/api/medical-records/",
    data
  );
  return response.data;
}

export async function getMedicalRecordsHistory(
  pacienteId: number,
  profissionalId: number
) {
  const response = await api.get<MedicalRecord[]>(
    `/api/medical-records/?paciente=${pacienteId}&profissional=${profissionalId}`
  );
  return response.data;
}

export async function updateMedicalRecord(
  id: number,
  data: Partial<MedicalRecordCreate>
) {
  const response = await api.patch<MedicalRecord>(
    `/api/medical-records/${id}/`,
    data
  );
  return response.data;
}

export async function closeMedicalRecord(id: number) {
  const response = await api.post(
    `/api/medical-records/${id}/fechar/`
  );
  return response.data;
}

export async function getMedicalHistory(id: number) {
  const response = await api.get(`/api/medical-records/${id}/historico/`);
  return response.data;
}

export async function getMedicalRecordByAppointment(
  appointmentId: number
) {
  const response = await api.get(
    `/api/medical-records/by-appointment/${appointmentId}/`
  );
  return response.data;
}
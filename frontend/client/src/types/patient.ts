import { BaseModel } from "./baseModel";

export interface Patient extends BaseModel {
  full_name: string;
  cpf: string;
  cpf_hash: string;
  document: string | null;
  phone: string;
  email: string;
  birth_date: string;
  clinic: number;
}

export interface PatientForm {
  full_name: string;
  cpf: string;
  email: string;
  phone: string;
  birth_date: string;
}
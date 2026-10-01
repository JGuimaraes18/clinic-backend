import { BaseModel } from "./baseModel";

export interface Clinic extends BaseModel {
  id: number;
  name: string;
  slug: string;
  document: string;
  phone: string;
  email: string;
  is_active?: boolean;
  admin_email?: string;
  user_count?: number;
  created_at?: string;
  logo?: string | null;
  banner?: string | null;
  theme?: string;
  primary_color?: string;
  secondary_color?: string;
}

export interface ClinicForm {
  name: string;
  slug: string;
  document: string;
  phone: string;
  email: string;
  logo?: string | File | null;
  banner?: string | File | null;
  theme?: string;
  primary_color?: string;
  secondary_color?: string;
}
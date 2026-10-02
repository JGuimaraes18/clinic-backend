export interface Clinic {
  id: number;
  name: string;
  slug: string;
  document: string;
  phone: string;
  email: string;
  created_at: string;
  is_active?: boolean;
  admin_email?: string;
  user_count?: number;
  logo?: string | null;
  banner?: string | null;
  theme?: string;
  primary_color?: string;
  secondary_color?: string;
}

export interface ClinicCreateResponse extends Clinic {
  temporary_password?: string;
}

export interface ClinicResetPasswordResponse {
  detail: string;
  temporary_password: string;
  admin_email: string;
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
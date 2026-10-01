import { BaseModel } from "./baseModel";

export interface Professional extends BaseModel {
  user: number;
  full_name: string;
  email: string;

  registration_type: string;
  registration_number: string;
  specialty: string;

  is_active: boolean;
}

export interface ProfessionalForm {
  user: number | null;
  registration_type: string;
  registration_number: string;
  specialty: string;
  is_active: boolean;
}
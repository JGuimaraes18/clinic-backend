export type UserRole = "ADMIN" | "PROFESSIONAL" | "ATTENDANT" | "SUPERUSER";

export interface Membership {
  role: UserRole;
  clinic: {
    id: number;
    name: string;
    slug: string;
    is_active?: boolean;
  };
}

export interface UserSettings {
  theme: "light" | "dark" | "system";
  primary_color: string | null;
  density: "comfortable" | "compact";
  font_size?: "small" | "medium" | "large";
  extra_preferences?: Record<string, any>;
}

export interface User {
  id: number;
  email: string;
  first_name: string;
  last_name: string;
  full_name: string;
  is_superuser: boolean;
  force_password_change?: boolean;
  memberships: Membership[];
  settings?: UserSettings;
}

export interface UserForm {
  email: string;
  first_name: string;
  last_name: string;
  role: UserRole;
  clinic_id: number | null;
  password?: string;
}

export interface UserErrors {
  email?: string;
  first_name?: string;
  last_name?: string;
  clinic?: string;
  password?: string;
  role?: string;
}
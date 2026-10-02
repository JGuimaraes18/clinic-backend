import api from "./api";
import { User, UserForm } from "@/types/users";

export async function login(
  clinic_slug: string,
  email: string,
  password: string
) {
  const response = await api.post("/api/auth/login/", {
    clinic_slug,
    email,
    password,
  });

  localStorage.setItem("access_token", response.data.access);
  localStorage.setItem("refresh_token", response.data.refresh);

  return response.data;
}

export async function getCurrentUser(): Promise<User> {
  const response = await api.get("/api/auth/me/");
  return response.data;
}

export async function getUsers(): Promise<User[]> {
  const { data } = await api.get("/api/auth/users/");
  return data;
}

export async function createUser(payload: UserForm): Promise<User> {
  const { data } = await api.post("/api/auth/users/", payload);
  return data;
}

export async function updateUser(
  id: number,
  payload: Partial<UserForm>
): Promise<User> {
  const { data } = await api.patch(`/api/auth/users/${id}/`, payload);
  return data;
}

export async function deleteUser(id: number): Promise<void> {
  await api.delete(`/api/auth/users/${id}/`);
}

import { UserSettings } from "@/types/users";

export async function updateUserSettings(settings: Partial<UserSettings>): Promise<any> {
  const { data } = await api.post("/api/auth/me/settings/", settings);
  return data;
}
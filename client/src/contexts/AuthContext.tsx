import { createContext, useContext, useEffect, useMemo, useState } from "react";
import { getCurrentUser, login as loginService, updateUserSettings } from "@/services/authService";
import { User, UserRole, UserSettings } from "@/types/users";

// Decodifica o payload do JWT sem dependência externa
function decodeToken(token: string): Record<string, any> | null {
  try {
    const payload = token.split(".")[1];
    return JSON.parse(atob(payload));
  } catch {
    return null;
  }
}

type AuthContextType = {
  user: User | null;
  role: UserRole | null;
  clinicId: number | null;
  loading: boolean;
  login: (clinic: string, email: string, password: string) => Promise<void>;
  logout: () => void;
  isAdmin: boolean;
  isProfessional: boolean;
  isAttendant: boolean;
  isSuperadmin: boolean;
  updateSettings: (settings: Partial<UserSettings>) => Promise<void>;
};

const AuthContext = createContext<AuthContextType>({
  user: null,
  role: null,
  clinicId: null,
  loading: true,
  login: async () => {},
  logout: () => {},
  isAdmin: false,
  isProfessional: false,
  isAttendant: false,
  isSuperadmin: false,
  updateSettings: async () => {},
});

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [role, setRole] = useState<UserRole | null>(null);
  const [clinicId, setClinicId] = useState<number | null>(null);
  const [loading, setLoading] = useState(true);

  // =============================
  // EXTRAIR ROLE E CLINIC DO TOKEN
  // =============================
  function loadTokenData() {
    const token = localStorage.getItem("access_token");
    if (!token) return;

    const payload = decodeToken(token);
    if (!payload) return;

    setRole(payload.role ?? null);
    setClinicId(payload.clinic_id ?? null);
  }

  // =============================
  // LOGIN
  // =============================
  const login = async (
    clinic_slug: string,
    email: string,
    password: string
  ) => {
    try {
      await loginService(clinic_slug, email, password);
      loadTokenData();

      const data = await getCurrentUser();
      setUser(data);
    } catch (error) {
      logout();
      throw error;
    }
  };

  // =============================
  // LOGOUT
  // =============================
  const logout = () => {
    setUser(null);
    setRole(null);
    setClinicId(null);
    localStorage.removeItem("access_token");
    localStorage.removeItem("refresh_token");
  };

  // =============================
  // AUTO LOAD (refresh de página)
  // =============================
  useEffect(() => {
    async function load() {
      const token = localStorage.getItem("access_token");

      if (!token) {
        setLoading(false);
        return;
      }

      loadTokenData();

      try {
        const data = await getCurrentUser();
        setUser(data);
      } catch {
        logout();
      } finally {
        setLoading(false);
      }
    }

    load();
  }, []);

  const updateSettings = async (newSettings: Partial<UserSettings>) => {
    if (!user) return;
    await updateUserSettings(newSettings);
    setUser(prev => prev ? {
      ...prev,
      settings: {
        ...prev.settings,
        ...newSettings
      } as UserSettings
    } : null);
  };


  const isAdmin = useMemo(() => role === "ADMIN", [role]);
  const isProfessional = useMemo(() => role === "PROFESSIONAL", [role]);
  const isAttendant = useMemo(() => role === "ATTENDANT", [role]);
  const isSuperadmin = useMemo(
    () => role === "SUPERUSER" || user?.is_superuser === true,
    [role, user?.is_superuser]
  );

  return (
    <AuthContext.Provider
      value={{
        user,
        role,
        clinicId,
        loading,
        login,
        logout,
        isAdmin,
        isProfessional,
        isAttendant,
        isSuperadmin,
        updateSettings,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  return useContext(AuthContext);
}
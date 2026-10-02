import { useEffect, useState } from "react";
import { NavLink, Outlet, useNavigate } from "react-router-dom";
import { Activity, Calendar, Users, Stethoscope, Menu, X, LogOut, Settings, FileText } from "lucide-react";
import { toast } from "sonner";
import { useAuth } from "@/contexts/AuthContext";

import { useIsMobile } from "@/hooks/useMobile";
import { getClinic } from "@/services/clinicService";
import { Clinic } from "@/types/clinic";
import { getApiErrorMessage } from "@/utils/apiError";

export default function AppLayout() {
    const navigate = useNavigate();
  const { user, logout, isProfessional, isSuperadmin, clinicId } = useAuth();
  const isMobile = useIsMobile();
  
  const [clinicConfig, setClinicConfig] = useState<Clinic | null>(null);

  useEffect(() => {
    if (user?.settings) {
      const { theme, primary_color, density, font_size } = user.settings;
      
      // Theme Accent Color
      if (primary_color) {
        document.documentElement.style.setProperty('--primary', primary_color);
      }
      
      // Theme Dark Mode
      if (theme === 'dark' || (theme === 'system' && window.matchMedia('(prefers-color-scheme: dark)').matches)) {
        document.documentElement.classList.add('dark');
      } else {
        document.documentElement.classList.remove('dark');
      }
      
      // Density
      document.documentElement.classList.remove('density-compact', 'density-comfortable');
      if (density) {
        document.documentElement.classList.add(`density-${density}`);
      } else {
        document.documentElement.classList.add('density-comfortable');
      }
      
      // Font Size
      document.documentElement.classList.remove('font-size-small', 'font-size-medium', 'font-size-large');
      if (font_size) {
        document.documentElement.classList.add(`font-size-${font_size}`);
      } else {
        document.documentElement.classList.add('font-size-medium');
      }
    } else if (clinicId) {
      getClinic(clinicId).then(config => {
        setClinicConfig(config);
        
        // Apply theme colors globally as fallback
        if (config.primary_color) {
          document.documentElement.style.setProperty('--primary', config.primary_color);
        }
        if (config.secondary_color) {
          document.documentElement.style.setProperty('--secondary', config.secondary_color);
        }
      }).catch((err) => {
        toast.error(
          getApiErrorMessage(err, "Erro ao carregar a identidade visual da clínica.")
        );
      });
    }
  }, [clinicId, user?.settings]);

  const [sidebarOpen, setSidebarOpen] = useState(false);

  // colapso desktop
  const [sidebarCollapsed, setSidebarCollapsed] = useState(false);

  const clinicalMenu = [
    { path: "/", label: "Dashboard", icon: Activity },
    { path: "/agendamentos", label: "Agendamentos", icon: Calendar },
    { path: "/calendar", label: "Calendário", icon: Calendar },
    { path: "/pacientes", label: "Pacientes", icon: Users },
    ...(!isProfessional
      ? [{ path: "/profissionais", label: "Profissionais", icon: Stethoscope }]
      : []),
    { path: "/settings", label: "Configurações", icon: Settings },
  ];

  const platformMenu = [
    { path: "/plataforma", label: "Dashboard da Plataforma", icon: Activity },
    { path: "/clinicas", label: "Clínicas", icon: Stethoscope },
    { path: "/usuarios", label: "Administradores", icon: Users },
    { path: "/audit-logs", label: "Logs de Auditoria", icon: FileText },
    { path: "/settings", label: "Configurações", icon: Settings },
  ];

  const menu = isSuperadmin ? platformMenu : clinicalMenu;

  function handleLogout() {
    logout();
    navigate("/login", { replace: true });
  }

  return (
    <div className="flex h-screen bg-white overflow-hidden">

      {/* OVERLAY MOBILE */}
      {isMobile && sidebarOpen && (
        <div
          className="fixed inset-0 bg-black/40 z-40"
          onClick={() => setSidebarOpen(false)}
        />
      )}

      {/* SIDEBAR / DRAWER */}
      <div
        className={`
          fixed md:relative z-50 h-full bg-white border-r border-gray-100
          flex flex-col transition-all duration-300 shadow-xl shadow-gray-200/20
          ${isMobile
            ? sidebarOpen
              ? "left-0 w-64"
              : "-left-64 w-64"
            : sidebarCollapsed
              ? "w-20"
              : "w-64"
          }
        `}
      >
        {/* HEADER */}
        <div className="p-6 flex items-center justify-between">
          {!sidebarCollapsed && !isMobile && (
            <div className="flex items-center gap-3 animate-in fade-in zoom-in duration-300">
              {clinicConfig?.logo ? (
                <img src={clinicConfig.logo} alt="Logo" className="w-10 h-10 object-contain rounded-xl" />
              ) : (
                <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-primary to-green-600 flex items-center justify-center shadow-lg shadow-primary/30 text-white">
                  <Activity size={20} strokeWidth={2.5} />
                </div>
              )}
              <h1 className="text-xl font-bold bg-gradient-to-r from-gray-800 to-gray-500 bg-clip-text text-transparent tracking-tight truncate max-w-[150px]">
                {clinicConfig?.name || "Clinify"}
              </h1>
            </div>
          )}

          <button
            onClick={() =>
              isMobile
                ? setSidebarOpen(!sidebarOpen)
                : setSidebarCollapsed(!sidebarCollapsed)
            }
            className="hover:bg-gray-100 p-2 rounded-xl transition-colors text-gray-500 hover:text-gray-900"
          >
            {isMobile
              ? (sidebarOpen ? <X size={20} /> : <Menu size={20} />)
              : (sidebarCollapsed ? <Menu size={20} /> : <X size={20} />)
            }
          </button>
        </div>

        {/* MENU */}
        <nav className="flex-1 px-4 py-6 space-y-2 overflow-y-auto custom-scrollbar">
          {menu.map(({ path, label, icon: Icon }) => (
            <NavLink
              end={path === "/"}
              key={path}
              to={path}
              onClick={() => {
                if (isMobile) setSidebarOpen(false);
              }}
              className={({ isActive }) =>
                `w-full flex items-center gap-3 px-3 py-3 rounded-xl transition-all duration-200 group ${
                  isActive
                    ? "bg-gradient-to-r from-primary/10 to-primary/5 text-primary font-semibold shadow-sm"
                    : "text-gray-500 hover:bg-gray-50 hover:text-gray-900"
                }`
              }
            >
              {({ isActive }) => (
                <>
                  <Icon
                    size={20}
                    className={`transition-transform duration-200 ${
                      isActive ? "scale-110" : "group-hover:scale-110"
                    }`}
                    strokeWidth={isActive ? 2.5 : 2}
                  />
                  {(!sidebarCollapsed || isMobile) && (
                    <span className="text-sm">{label}</span>
                  )}
                </>
              )}
            </NavLink>
          ))}
        </nav>
        {/* LOGOUT */}
        <div className="p-4 border-t border-gray-100">
          <button
            onClick={handleLogout}
            className="w-full flex items-center gap-3 px-3 py-3 text-red-500 hover:bg-red-50 hover:text-red-600 rounded-xl transition-colors group"
          >
            <LogOut size={20} className="group-hover:scale-110 transition-transform duration-200" />
            {(!sidebarCollapsed || isMobile) && (
              <span className="text-sm font-medium">Sair da conta</span>
            )}
          </button>
        </div>
      </div>

      {/* CONTEÚDO */}
      <div className="flex-1 flex flex-col overflow-hidden">

        {/* TOPBAR MOBILE */}
        {isMobile && (
          <div className="px-4 py-3 border-b border-gray-100 flex items-center bg-white/80 backdrop-blur-md sticky top-0 z-30">
            <button 
              onClick={() => setSidebarOpen(true)}
              className="p-2 -ml-2 rounded-xl text-gray-600 hover:bg-gray-100"
            >
              <Menu size={20} />
            </button>
            <div className="flex items-center gap-2 ml-2">
              <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-primary to-green-600 flex items-center justify-center shadow-md text-white">
                <Activity size={16} strokeWidth={2.5} />
              </div>
              <h1 className="text-lg font-bold bg-gradient-to-r from-gray-800 to-gray-500 bg-clip-text text-transparent">
                Clinify
              </h1>
            </div>
          </div>
        )}

        {/* MAIN */}
        <main className="flex-1 overflow-auto p-4 md:p-8 bg-gray-50/50">
          <div className="max-w-7xl mx-auto animate-in fade-in duration-500">
            <Outlet />
          </div>
        </main>
      </div>
    </div>
  );
}
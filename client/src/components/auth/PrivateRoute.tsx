import { Navigate, Outlet, useLocation } from "react-router-dom";
import { useAuth } from "@/contexts/AuthContext";

interface PrivateRouteProps {
  allowedRoles?: string[];
}

export default function PrivateRoute({ allowedRoles }: PrivateRouteProps) {
  const { user, loading } = useAuth();
  const location = useLocation();

  // 🔄 Enquanto valida token
  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <span className="text-sm text-muted-foreground">
          Carregando...
        </span>
      </div>
    );
  }

  // 🚪 Não autenticado
  if (!user) {
    return <Navigate to="/login" state={{ from: location }} replace />;
  }

  // 🔒 Redirecionar para alteração de senha obrigatória
  if (user.force_password_change && location.pathname !== "/force-password-change") {
    return <Navigate to="/force-password-change" replace />;
  }

  // 🔐 Restrição por role (opcional)
  if (allowedRoles && !allowedRoles.includes(user.role)) {
    return <Navigate to="/" replace />;
  }

  return <Outlet />;
}
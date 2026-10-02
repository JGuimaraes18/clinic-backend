import { useState } from "react";
import { Link, useNavigate, useSearchParams } from "react-router-dom";
import api from "@/services/api";
import { Activity } from "lucide-react";
import { toast } from "sonner";
import { Button } from "@/components/ui/button";

export default function ResetPassword() {
  const [searchParams] = useSearchParams();
  const token = searchParams.get("token");
  const navigate = useNavigate();

  const [password, setPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [loading, setLoading] = useState(false);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!password || !confirmPassword) {
      toast.error("Preencha todos os campos.");
      return;
    }
    
    if (password !== confirmPassword) {
      toast.error("As senhas não coincidem.");
      return;
    }

    if (password.length < 8) {
      toast.error("A senha deve ter pelo menos 8 caracteres.");
      return;
    }

    if (!token) {
      toast.error("Token de recuperação ausente ou inválido.");
      return;
    }

    try {
      setLoading(true);
      await api.post("/api/accounts/password-reset/confirm/", { token, password });
      toast.success("Senha redefinida com sucesso!");
      navigate("/login");
    } catch (err: any) {
      toast.error(err.response?.data?.detail || "Erro ao redefinir a senha.");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-50/50 p-4">
      <div className="w-full max-w-md space-y-8">
        <div className="flex flex-col items-center justify-center animate-in fade-in zoom-in duration-300">
          <div className="w-14 h-14 rounded-2xl bg-gradient-to-br from-primary to-green-600 flex items-center justify-center shadow-lg shadow-primary/30 text-white mb-4">
            <Activity size={28} strokeWidth={2.5} />
          </div>
          <h2 className="text-3xl font-bold bg-gradient-to-r from-gray-800 to-gray-500 bg-clip-text text-transparent tracking-tight">
            Nova Senha
          </h2>
          <p className="mt-2 text-sm text-gray-500 font-medium">
            Defina sua nova senha de acesso
          </p>
        </div>

        <div className="bg-white p-8 rounded-3xl shadow-xl shadow-gray-200/50 border border-gray-100">
          {!token ? (
             <div className="text-center space-y-4">
               <div className="bg-red-50 text-red-700 p-4 rounded-xl text-sm font-medium">
                 Token inválido ou ausente. Por favor, solicite a recuperação novamente.
               </div>
               <Button variant="outline" className="w-full" asChild>
                 <Link to="/forgot-password">Solicitar Recuperação</Link>
               </Button>
             </div>
          ) : (
            <form onSubmit={handleSubmit} className="space-y-6">
              <div className="space-y-4">
                <div className="space-y-2">
                  <label htmlFor="password" className="block text-sm font-semibold text-gray-700">
                    Nova Senha
                  </label>
                  <input
                    id="password"
                    type="password"
                    value={password}
                    onChange={(e) => setPassword(e.target.value)}
                    className="w-full px-4 py-3 bg-gray-50/50 border border-gray-200 rounded-xl focus:ring-2 focus:ring-primary/20 focus:border-primary outline-none transition-all duration-200 text-sm font-medium"
                    placeholder="Mínimo 8 caracteres"
                  />
                </div>
                <div className="space-y-2">
                  <label htmlFor="confirmPassword" className="block text-sm font-semibold text-gray-700">
                    Confirmar Nova Senha
                  </label>
                  <input
                    id="confirmPassword"
                    type="password"
                    value={confirmPassword}
                    onChange={(e) => setConfirmPassword(e.target.value)}
                    className="w-full px-4 py-3 bg-gray-50/50 border border-gray-200 rounded-xl focus:ring-2 focus:ring-primary/20 focus:border-primary outline-none transition-all duration-200 text-sm font-medium"
                    placeholder="Digite novamente"
                  />
                </div>
              </div>

              <Button
                type="submit"
                disabled={loading}
                className="w-full py-6 bg-primary hover:bg-primary/90 text-white rounded-xl text-base font-semibold transition-all duration-300 shadow-lg shadow-primary/25 hover:shadow-xl hover:shadow-primary/30 hover:-translate-y-0.5"
              >
                {loading ? "Salvando..." : "Redefinir Senha"}
              </Button>
            </form>
          )}
        </div>
      </div>
    </div>
  );
}

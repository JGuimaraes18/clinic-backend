import { useState } from "react";
import { useAuth } from "@/contexts/AuthContext";
import { useNavigate } from "react-router-dom";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { KeyRound, CheckCircle2 } from "lucide-react";
import api from "@/services/api";
import { toast } from "sonner";

export default function ForcePasswordChange() {
  const [password, setPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [loading, setLoading] = useState(false);
  const navigate = useNavigate();
  const { user } = useAuth();

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (password !== confirmPassword) {
      toast.error("As senhas não coincidem.");
      return;
    }
    if (password.length < 8) {
      toast.error("A senha deve ter no mínimo 8 caracteres.");
      return;
    }

    setLoading(true);
    try {
      await api.post("/api/auth/change-password/", { new_password: password });
      toast.success("Senha alterada com sucesso!");
      // Força um reload para o AuthContext recarregar o usuário sem o flag
      window.location.href = "/";
    } catch (err: any) {
      toast.error(err.response?.data?.detail || "Erro ao alterar a senha.");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="min-h-screen bg-gray-50 flex flex-col justify-center py-12 sm:px-6 lg:px-8">
      <div className="sm:mx-auto sm:w-full sm:max-w-md">
        <div className="flex justify-center">
          <div className="w-16 h-16 rounded-full bg-primary/10 flex items-center justify-center">
            <KeyRound className="w-8 h-8 text-primary" />
          </div>
        </div>
        <h2 className="mt-6 text-center text-3xl font-extrabold text-gray-900">
          Troca de Senha Obrigatória
        </h2>
        <p className="mt-2 text-center text-sm text-gray-600">
          Olá, {user?.first_name}. Por questões de segurança, você precisa definir uma nova senha antes de acessar o sistema.
        </p>
      </div>

      <div className="mt-8 sm:mx-auto sm:w-full sm:max-w-md">
        <Card>
          <CardContent className="pt-6">
            <form onSubmit={handleSubmit} className="space-y-6">
              <div>
                <label className="block text-sm font-medium text-gray-700">Nova Senha</label>
                <div className="mt-1">
                  <Input
                    type="password"
                    value={password}
                    onChange={(e) => setPassword(e.target.value)}
                    required
                    minLength={8}
                    className="w-full"
                    placeholder="Mínimo de 8 caracteres"
                  />
                </div>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700">Confirmar Nova Senha</label>
                <div className="mt-1">
                  <Input
                    type="password"
                    value={confirmPassword}
                    onChange={(e) => setConfirmPassword(e.target.value)}
                    required
                    className="w-full"
                    placeholder="Digite novamente"
                  />
                </div>
              </div>

              <Button type="submit" className="w-full flex items-center gap-2" disabled={loading}>
                {loading ? "Alterando..." : (
                  <>
                    <CheckCircle2 size={18} />
                    Confirmar Alteração
                  </>
                )}
              </Button>
            </form>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}

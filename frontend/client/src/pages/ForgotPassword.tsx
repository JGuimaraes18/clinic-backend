import { useState } from "react";
import { Link } from "react-router-dom";
import api from "@/services/api";
import { Activity } from "lucide-react";
import { toast } from "sonner";
import { Button } from "@/components/ui/button";

export default function ForgotPassword() {
  const [email, setEmail] = useState("");
  const [loading, setLoading] = useState(false);
  const [success, setSuccess] = useState(false);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!email) {
      toast.error("Informe seu e-mail.");
      return;
    }

    try {
      setLoading(true);
      await api.post("/api/accounts/password-reset/request/", { email });
      setSuccess(true);
      toast.success("Se o e-mail existir, um link de recuperação foi enviado.");
    } catch (err: any) {
      toast.error(err.response?.data?.detail || "Erro ao solicitar recuperação.");
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
            Recuperar Senha
          </h2>
          <p className="mt-2 text-sm text-gray-500 font-medium">
            Informe seu e-mail para receber as instruções
          </p>
        </div>

        <div className="bg-white p-8 rounded-3xl shadow-xl shadow-gray-200/50 border border-gray-100">
          {success ? (
             <div className="text-center space-y-4">
               <div className="bg-green-50 text-green-700 p-4 rounded-xl text-sm font-medium">
                 E-mail enviado! Verifique sua caixa de entrada e spam para redefinir sua senha.
               </div>
               <Button variant="outline" className="w-full" asChild>
                 <Link to="/login">Voltar ao Login</Link>
               </Button>
             </div>
          ) : (
            <form onSubmit={handleSubmit} className="space-y-6">
              <div className="space-y-2">
                <label htmlFor="email" className="block text-sm font-semibold text-gray-700">
                  E-mail cadastrado
                </label>
                <div className="relative">
                  <input
                    id="email"
                    type="email"
                    value={email}
                    onChange={(e) => setEmail(e.target.value)}
                    className="w-full px-4 py-3 bg-gray-50/50 border border-gray-200 rounded-xl focus:ring-2 focus:ring-primary/20 focus:border-primary outline-none transition-all duration-200 text-sm font-medium"
                    placeholder="voce@exemplo.com"
                  />
                </div>
              </div>

              <Button
                type="submit"
                disabled={loading}
                className="w-full py-6 bg-primary hover:bg-primary/90 text-white rounded-xl text-base font-semibold transition-all duration-300 shadow-lg shadow-primary/25 hover:shadow-xl hover:shadow-primary/30 hover:-translate-y-0.5"
              >
                {loading ? "Enviando..." : "Enviar instruções"}
              </Button>

              <div className="text-center pt-2">
                <Link to="/login" className="text-sm font-semibold text-primary hover:text-primary/80 transition-colors">
                  Lembrou a senha? Voltar ao login
                </Link>
              </div>
            </form>
          )}
        </div>
      </div>
    </div>
  );
}

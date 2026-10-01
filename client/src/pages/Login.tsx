import { useState } from "react";
import { useNavigate, Link } from "react-router-dom";
import { Activity, Lock, Mail, Hospital } from "lucide-react";
import { useForm } from "react-hook-form";
import { useAuth } from "@/contexts/AuthContext";

type LoginFormValues = {
  clinicSlug: string;
  email: string;
  password: string;
};

export default function Login() {
  const navigate = useNavigate();
  const { login } = useAuth();
  const [error, setError] = useState<string | null>(null);

  const {
    register,
    handleSubmit,
    formState: { errors, isSubmitting },
  } = useForm<LoginFormValues>({
    defaultValues: {
      clinicSlug: "",
      email: "",
      password: "",
    },
  });

  async function handleLogin({ clinicSlug, email, password }: LoginFormValues) {
    setError(null);

    try {
      await login(clinicSlug, email, password);
      navigate("/", { replace: true });
    } catch (err: any) {
      const msg =
        err?.response?.data?.non_field_errors?.[0] ||
        err?.response?.data?.detail ||
        "Usuário, senha ou clínica inválidos.";
      setError(msg);
    }
  }

  return (
    <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-primary/5 to-accent/5 p-6">
      <div className="w-full max-w-md bg-white border border-border rounded-2xl shadow-lg p-8 space-y-8">

        {/* Logo */}
        <div className="flex flex-col items-center text-center">
          <div className="w-14 h-14 bg-primary/10 rounded-xl flex items-center justify-center mb-4">
            <Activity className="text-primary" size={28} />
          </div>
          <h1 className="text-2xl font-bold text-foreground">Gestão Clínica</h1>
          <p className="text-sm text-muted-foreground mt-1">
            Acesse sua conta para continuar
          </p>
        </div>

        {/* Form */}
        <form onSubmit={handleSubmit(handleLogin)} className="space-y-5">

          {/* Clínica */}
          <div className="space-y-2">
            <label htmlFor="clinic-slug" className="text-sm font-semibold text-foreground">
              Clínica
            </label>
            <div className="relative">
              <Hospital
                size={18}
                className="absolute left-3 top-1/2 -translate-y-1/2 text-muted-foreground"
              />
              <input
                id="clinic-slug"
                type="text"
                {...register("clinicSlug", {
                  required: "Clínica é obrigatória.",
                })}
                aria-invalid={errors.clinicSlug ? "true" : "false"}
                aria-describedby={errors.clinicSlug ? "clinic-slug-error" : undefined}
                className="w-full border border-border rounded-lg pl-10 pr-4 py-3 focus:outline-none focus:ring-2 focus:ring-primary/40 transition"
                placeholder="slug-da-clinica"
                autoComplete="organization"
              />
            </div>
            {errors.clinicSlug && (
              <p id="clinic-slug-error" className="text-xs text-destructive">
                {errors.clinicSlug.message}
              </p>
            )}
            <p className="text-xs text-muted-foreground">
              Informe o identificador único da sua clínica
            </p>
          </div>

          {/* Email */}
          <div className="space-y-2">
            <label htmlFor="email" className="text-sm font-semibold text-foreground">
              E-mail
            </label>
            <div className="relative">
              <Mail
                size={18}
                className="absolute left-3 top-1/2 -translate-y-1/2 text-muted-foreground"
              />
              <input
                id="email"
                type="email"
                {...register("email", {
                  required: "E-mail é obrigatório.",
                  pattern: {
                    value: /^[^\s@]+@[^\s@]+\.[^\s@]+$/,
                    message: "Use um e-mail válido.",
                  },
                })}
                aria-invalid={errors.email ? "true" : "false"}
                aria-describedby={errors.email ? "email-error" : undefined}
                className="w-full border border-border rounded-lg pl-10 pr-4 py-3 focus:outline-none focus:ring-2 focus:ring-primary/40 transition"
                placeholder="seu@email.com"
                autoComplete="email"
              />
            </div>
            {errors.email && (
              <p id="email-error" className="text-xs text-destructive">
                {errors.email.message}
              </p>
            )}
          </div>

          {/* Senha */}
          <div className="space-y-2">
            <label htmlFor="password" className="text-sm font-semibold text-foreground">
              Senha
            </label>
            <div className="relative">
              <Lock
                size={18}
                className="absolute left-3 top-1/2 -translate-y-1/2 text-muted-foreground"
              />
              <input
                id="password"
                type="password"
                {...register("password", {
                  required: "Senha é obrigatória.",
                })}
                aria-invalid={errors.password ? "true" : "false"}
                aria-describedby={errors.password ? "password-error" : undefined}
                className="w-full border border-border rounded-lg pl-10 pr-4 py-3 focus:outline-none focus:ring-2 focus:ring-primary/40 transition"
                placeholder="••••••••"
                autoComplete="current-password"
              />
            </div>
            {errors.password && (
              <p id="password-error" className="text-xs text-destructive">
                {errors.password.message}
              </p>
            )}
          </div>

          {/* Erro */}
          {error && (
            <div className="text-sm text-red-600 bg-red-50 border border-red-200 rounded-lg px-4 py-3">
              {error}
            </div>
          )}

          {/* Botão */}
          <button
            id="login-submit"
            type="submit"
            disabled={isSubmitting}
            className="w-full bg-primary text-white py-3 rounded-lg font-semibold hover:bg-primary/90 transition disabled:opacity-50"
          >
            {isSubmitting ? "Entrando..." : "Entrar"}
          </button>
          
          <div className="text-center pt-2">
            <Link to="/forgot-password" className="text-sm font-semibold text-primary hover:text-primary/80 transition-colors">
              Esqueceu sua senha?
            </Link>
          </div>
        </form>

        {/* Footer */}
        <div className="text-center text-xs text-muted-foreground">
          © {new Date().getFullYear()} JG. Todos os direitos reservados.
        </div>
      </div>
    </div>
  );
}
import { Component, type ErrorInfo, type ReactNode } from "react";
import { Button } from "@/components/ui/button";

interface ErrorBoundaryProps {
  children: ReactNode;
}

interface ErrorBoundaryState {
  hasError: boolean;
}

export class ErrorBoundary extends Component<
  ErrorBoundaryProps,
  ErrorBoundaryState
> {
  state: ErrorBoundaryState = { hasError: false };

  static getDerivedStateFromError(): ErrorBoundaryState {
    return { hasError: true };
  }

  componentDidCatch(error: Error, errorInfo: ErrorInfo) {
    console.error(
      "Erro de renderização não tratado:",
      error,
      errorInfo.componentStack
    );
  }

  render() {
    if (!this.state.hasError) {
      return this.props.children;
    }

    return (
      <div className="flex min-h-screen items-center justify-center bg-muted p-6">
        <div className="w-full max-w-md space-y-4 rounded-xl border bg-card p-8 text-center shadow-sm">
          <h1 className="text-xl font-semibold text-card-foreground">
            Algo deu errado
          </h1>

          <p className="text-sm leading-relaxed text-muted-foreground">
            Ocorreu um erro inesperado ao exibir esta tela. Nenhum dado foi
            apagado. Tente recarregar o aplicativo; se o problema continuar,
            informe o suporte técnico.
          </p>

          <Button
            className="w-full"
            onClick={() => window.location.reload()}
          >
            Recarregar aplicativo
          </Button>
        </div>
      </div>
    );
  }
}

import { useEffect, useState } from "react";
import { useParams, useNavigate } from "react-router-dom";
import {
  getMedicalRecordById,
  updateMedicalRecord,
  closeMedicalRecord,
  MedicalRecord,
} from "@/services/medicalRecordService";
import { 
  Card, 
  CardContent, 
  CardHeader, 
  CardTitle,
  CardFooter
} from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";
import { 
  Save, 
  CheckCircle, 
  ArrowLeft,
  FileText,
  Clock
} from "lucide-react";
import { useAuth } from "@/contexts/AuthContext";
import { toast } from "sonner"; // Assuming sonner is used for toasts, if not, I can just use alert. Wait, package.json has sonner.

export default function MedicalRecordPage() {
  const { id } = useParams();
  const navigate = useNavigate();
  const { isProfessional, user } = useAuth();
  
  const [record, setRecord] = useState<MedicalRecord | null>(null);
  const [conteudo, setConteudo] = useState("");
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    async function load() {
      if (!id) return;

      try {
        setLoading(true);
        const data = await getMedicalRecordById(Number(id));
        setRecord(data);
        setConteudo(data.conteudo);
      } catch (error) {
        toast.error("Erro ao carregar prontuário.");
      } finally {
        setLoading(false);
      }
    }

    load();
  }, [id]);

  async function handleSave() {
    if (!record) return;

    try {
      setSaving(true);
      const updated = await updateMedicalRecord(record.id, {
        conteudo,
      });

      setRecord(updated);
      toast.success("Rascunho salvo com sucesso.");
    } catch (error) {
      toast.error("Erro ao salvar rascunho.");
    } finally {
      setSaving(false);
    }
  }

  async function handleClose() {
    if (!record) return;

    if (!conteudo.trim() || conteudo === "Acesso restrito (Informação Sensível)") {
      toast.error("Não é possível fechar prontuário vazio ou restrito.");
      return;
    }

    try {
      setSaving(true);
      await closeMedicalRecord(record.id);
      toast.success("Prontuário fechado com sucesso!");

      const updated = await getMedicalRecordById(record.id);
      setRecord(updated);
    } catch (error) {
      toast.error("Erro ao fechar prontuário.");
    } finally {
      setSaving(false);
    }
  }

  if (loading) {
    return (
      <div className="p-6 max-w-5xl mx-auto space-y-6">
        <Skeleton className="h-10 w-[200px]" />
        <Card>
          <CardHeader>
            <Skeleton className="h-8 w-[150px]" />
          </CardHeader>
          <CardContent className="space-y-4">
            <Skeleton className="h-[300px] w-full" />
          </CardContent>
        </Card>
      </div>
    );
  }

  if (!record) {
    return (
      <div className="p-6 max-w-5xl mx-auto flex flex-col items-center justify-center py-20 text-muted-foreground">
        <FileText className="w-16 h-16 mb-4 opacity-20" />
        <h2 className="text-xl font-semibold">Prontuário não encontrado</h2>
        <Button variant="link" onClick={() => navigate("/agendamentos")}>
          Voltar para agendamentos
        </Button>
      </div>
    );
  }

  const isClosed = record.status === "FECHADO";
  const isRestricted = conteudo === "Acesso restrito (Informação Sensível)";
  
  // Se não é o profissional que está acessando e o conteúdo for restrito, ele não pode editar
  const canEdit = !isClosed && !isRestricted && isProfessional;

  return (
    <div className="p-6 max-w-5xl mx-auto space-y-6">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-4">
          <Button 
            variant="ghost" 
            size="icon" 
            onClick={() => navigate("/agendamentos")}
            className="rounded-full hover:bg-muted"
          >
            <ArrowLeft className="w-5 h-5" />
          </Button>
          <div>
            <h1 className="text-2xl font-bold tracking-tight flex items-center gap-3">
              Atendimento #{record.id}
              <Badge variant={isClosed ? "secondary" : "default"} className={isClosed ? "bg-green-100 text-green-800" : "bg-blue-100 text-blue-800"}>
                {isClosed ? "Finalizado" : "Em Andamento"}
              </Badge>
            </h1>
            <p className="text-sm text-muted-foreground mt-1">
              Registre abaixo a evolução clínica do paciente.
            </p>
          </div>
        </div>
      </div>

      <Card className="border-none shadow-md overflow-hidden bg-white/50 backdrop-blur-sm">
        <CardHeader className="bg-muted/30 border-b pb-4">
          <CardTitle className="text-lg flex items-center gap-2">
            <FileText className="w-5 h-5 text-primary" />
            Evolução Clínica
          </CardTitle>
        </CardHeader>
        <CardContent className="p-0">
          <div className="p-6">
            <Textarea
              value={conteudo}
              onChange={(e) => setConteudo(e.target.value)}
              disabled={!canEdit}
              placeholder={canEdit ? "Descreva os achados clínicos, diagnóstico e conduta..." : ""}
              className="min-h-[400px] text-base resize-y border-gray-200 focus:border-primary focus:ring-primary shadow-sm bg-white"
            />
          </div>
          
          {isClosed && record.finalizado_em && (
            <div className="px-6 pb-6 flex items-center gap-2 text-sm text-green-700 font-medium">
              <Clock className="w-4 h-4" />
              Prontuário fechado definitivamente em {new Date(record.finalizado_em).toLocaleString("pt-BR")}
            </div>
          )}
          
          {isRestricted && (
            <div className="px-6 pb-6 flex items-center gap-2 text-sm text-red-600 font-medium">
               Acesso ao conteúdo bloqueado por regras de privacidade.
            </div>
          )}
        </CardContent>
        
        {canEdit && (
          <CardFooter className="bg-muted/10 border-t p-4 flex justify-end gap-3">
            <Button
              variant="outline"
              onClick={handleSave}
              disabled={saving}
              className="border-gray-200 hover:bg-gray-50"
            >
              <Save className="w-4 h-4 mr-2" />
              {saving ? "Salvando..." : "Salvar Rascunho"}
            </Button>

            <Button
              onClick={handleClose}
              disabled={saving || !conteudo.trim()}
              className="bg-primary hover:bg-primary/90 text-primary-foreground shadow-md transition-all hover:-translate-y-0.5"
            >
              <CheckCircle className="w-4 h-4 mr-2" />
              Finalizar Atendimento
            </Button>
          </CardFooter>
        )}
      </Card>
    </div>
  );
}
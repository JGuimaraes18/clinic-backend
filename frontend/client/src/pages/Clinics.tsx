import { useState, useEffect } from "react";
import { getClinics, createClinic, updateClinic, toggleClinicActive, resetClinicAdminPassword } from "@/services/clinicService";
import { Clinic, ClinicForm } from "@/types/clinic";
import { formatCNPJ, formatPhone } from "@/utils/format";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { Building2, Search, Plus, CheckCircle2, XCircle, Users, KeyRound, Pencil, Power } from "lucide-react";
import { toast } from "sonner";
import Modal from "@/components/modal/Modal";
import { motion } from "framer-motion";

const emptyForm: ClinicForm = { name: "", slug: "", document: "", phone: "", email: "" };

export default function Clinics() {
  const [clinics, setClinics] = useState<Clinic[]>([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState("");
  const [isOpen, setIsOpen] = useState(false);
  const [editingId, setEditingId] = useState<number | null>(null);
  const [form, setForm] = useState<ClinicForm>(emptyForm);
  const [errors, setErrors] = useState<Partial<ClinicForm>>({});
  const [detailClinic, setDetailClinic] = useState<Clinic | null>(null);
  const [credentialsModal, setCredentialsModal] = useState<{
    isOpen: boolean;
    adminEmail: string;
    tempPassword: string;
    title: string;
  }>({
    isOpen: false,
    adminEmail: "",
    tempPassword: "",
    title: "",
  });


  useEffect(() => {
    loadClinics();
  }, []);

  async function loadClinics() {
    try {
      const data = await getClinics();
      setClinics(data);
    } catch { toast.error("Erro ao carregar clínicas."); }
    finally { setLoading(false); }
  }

  function handleClose() {
    setIsOpen(false);
    setEditingId(null);
    setErrors({});
    setForm(emptyForm);
  }

  function validate() {
    const e: Partial<ClinicForm> = {};
    if (!form.name.trim()) e.name = "Obrigatório";
    if (!form.email.trim()) e.email = "Obrigatório";
    else if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(form.email)) e.email = "Email inválido";
    if (!form.phone.trim()) e.phone = "Obrigatório";
    setErrors(e);
    return Object.keys(e).length === 0;
  }

  async function handleSave() {
    if (!validate()) return;
    try {
      if (editingId) {
        const updated = await updateClinic(editingId, form);
        setClinics((prev) => prev.map((c) => (c.id === editingId ? updated : c)));
        toast.success("Clínica atualizada!");
        handleClose();
      } else {
        const created = await createClinic(form);
        setClinics((prev) => [...prev, created]);
        handleClose();
        setCredentialsModal({
          isOpen: true,
          adminEmail: created.admin_email || "",
          tempPassword: created.temporary_password || "",
          title: "Clínica Criada com Sucesso!",
        });
      }
    } catch (err: any) {
      const data = err?.response?.data;
      if (data && typeof data === 'object' && !data.detail) {
        const firstKey = Object.keys(data)[0];
        const errorMsg = Array.isArray(data[firstKey]) ? data[firstKey][0] : data[firstKey];
        toast.error(`Erro no campo ${firstKey}: ${errorMsg}`);
      } else {
        toast.error(data?.detail || "Erro ao salvar.");
      }
    }
  }

  function handleEdit(clinic: Clinic) {
    setEditingId(clinic.id);
    setForm({ name: clinic.name, slug: clinic.slug, document: clinic.document, phone: clinic.phone, email: clinic.email });
    setIsOpen(true);
  }

  async function handleToggleActive(clinic: Clinic) {
    const newStatus = !clinic.is_active;
    try {
      const updated = await toggleClinicActive(clinic.id, newStatus);
      setClinics((prev) => prev.map((c) => (c.id === clinic.id ? updated : c)));
      toast.success(`Clínica ${newStatus ? "ativada" : "desativada"} com sucesso.`);
      if (detailClinic?.id === clinic.id) setDetailClinic(updated);
    } catch { toast.error("Erro ao alterar status."); }
  }

  async function handleResetPassword(clinic: Clinic) {
    if (!confirm(`Redefinir a senha do administrador de "${clinic.name}"?`)) return;
    try {
      const res = await resetClinicAdminPassword(clinic.id);
      setCredentialsModal({
        isOpen: true,
        adminEmail: res.admin_email || "",
        tempPassword: res.temporary_password || "",
        title: "Senha do Administrador Redefinida!",
      });
    } catch (err: any) {
      toast.error(err?.response?.data?.detail || "Erro ao redefinir senha.");
    }
  }


  const filtered = clinics
    .filter((c) => {
      const q = search.toLowerCase();
      return c.name.toLowerCase().includes(q) || c.slug.toLowerCase().includes(q) || c.email.toLowerCase().includes(q) || c.document.includes(q);
    })
    .sort((a, b) => a.name.localeCompare(b.name, "pt-BR"));

  return (
    <motion.div className="space-y-6" initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.4 }}>
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div className="flex items-center gap-3">
          <div className="p-2.5 rounded-xl bg-primary/10"><Building2 className="w-6 h-6 text-primary" /></div>
          <div>
            <h1 className="text-2xl font-bold tracking-tight">Gerenciamento de Clínicas</h1>
            <p className="text-sm text-muted-foreground">{clinics.length} clínica{clinics.length !== 1 ? "s" : ""} cadastrada{clinics.length !== 1 ? "s" : ""}</p>
          </div>
        </div>
        <Button onClick={() => setIsOpen(true)} className="gap-2"><Plus className="w-4 h-4" /> Nova Clínica</Button>
      </div>

      {/* Search */}
      <div className="relative max-w-md">
        <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-muted-foreground" />
        <Input placeholder="Pesquisar clínicas..." className="pl-10" value={search} onChange={(e) => setSearch(e.target.value)} />
      </div>

      {/* Table */}
      <Card className="border-none shadow-md overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b bg-muted/30">
                <th className="text-left px-4 py-3 font-medium text-muted-foreground">Clínica</th>
                <th className="text-left px-4 py-3 font-medium text-muted-foreground hidden md:table-cell">Administrador</th>
                <th className="text-center px-4 py-3 font-medium text-muted-foreground hidden sm:table-cell">Usuários</th>
                <th className="text-center px-4 py-3 font-medium text-muted-foreground">Status</th>
                <th className="text-center px-4 py-3 font-medium text-muted-foreground hidden lg:table-cell">Criada em</th>
                <th className="text-right px-4 py-3 font-medium text-muted-foreground">Ações</th>
              </tr>
            </thead>
            <tbody>
              {loading ? (
                <tr><td colSpan={6} className="text-center py-12 text-muted-foreground">Carregando...</td></tr>
              ) : filtered.length === 0 ? (
                <tr><td colSpan={6} className="text-center py-12 text-muted-foreground">Nenhuma clínica encontrada.</td></tr>
              ) : (
                filtered.map((clinic) => (
                  <tr key={clinic.id} className="border-b last:border-0 hover:bg-muted/20 transition-colors">
                    <td className="px-4 py-3">
                      <div className="flex items-center gap-3">
                        <div className="w-9 h-9 rounded-lg bg-primary/10 flex items-center justify-center shrink-0">
                          <Building2 className="w-4 h-4 text-primary" />
                        </div>
                        <div>
                          <p className="font-semibold">{clinic.name}</p>
                          <p className="text-xs text-muted-foreground">{clinic.slug}</p>
                        </div>
                      </div>
                    </td>
                    <td className="px-4 py-3 hidden md:table-cell text-muted-foreground">{clinic.admin_email || "—"}</td>
                    <td className="px-4 py-3 text-center hidden sm:table-cell">
                      <span className="inline-flex items-center gap-1 text-muted-foreground"><Users className="w-3.5 h-3.5" /> {clinic.user_count || 0}</span>
                    </td>
                    <td className="px-4 py-3 text-center">
                      {clinic.is_active !== false ? (
                        <span className="inline-flex items-center gap-1 px-2 py-0.5 text-xs font-medium bg-emerald-50 text-emerald-700 rounded-full"><CheckCircle2 className="w-3 h-3" /> Ativa</span>
                      ) : (
                        <span className="inline-flex items-center gap-1 px-2 py-0.5 text-xs font-medium bg-red-50 text-red-700 rounded-full"><XCircle className="w-3 h-3" /> Inativa</span>
                      )}
                    </td>
                    <td className="px-4 py-3 text-center text-muted-foreground text-xs hidden lg:table-cell">
                      {clinic.created_at ? new Date(clinic.created_at).toLocaleDateString("pt-BR") : "—"}
                    </td>
                    <td className="px-4 py-3">
                      <div className="flex items-center justify-end gap-1">
                        <Button variant="ghost" size="icon" className="h-8 w-8" title="Editar" onClick={() => handleEdit(clinic)}><Pencil className="w-4 h-4" /></Button>
                        <Button variant="ghost" size="icon" className="h-8 w-8" title={clinic.is_active !== false ? "Desativar" : "Ativar"} onClick={() => handleToggleActive(clinic)}>
                          <Power className={`w-4 h-4 ${clinic.is_active !== false ? "text-emerald-600" : "text-red-500"}`} />
                        </Button>
                        <Button variant="ghost" size="icon" className="h-8 w-8" title="Resetar senha do admin" onClick={() => handleResetPassword(clinic)}><KeyRound className="w-4 h-4 text-amber-600" /></Button>
                      </div>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </Card>

      {/* Modal Create/Edit */}
      <Modal isOpen={isOpen} onClose={handleClose} title={editingId ? "Editar Clínica" : "Nova Clínica"}>
        <div className="space-y-4">
          <div>
            <label className="text-sm font-medium text-foreground">Nome *</label>
            <Input className={errors.name ? "border-red-500" : ""} value={form.name} onChange={(e) => setForm({ ...form, name: e.target.value })} placeholder="Nome da clínica" />
            {errors.name && <p className="text-xs text-red-500 mt-1">{errors.name}</p>}
          </div>
          {!editingId && (
            <div>
              <label className="text-sm font-medium text-foreground">Identificador (slug)</label>
              <Input className={errors.slug ? "border-red-500" : ""} value={form.slug} onChange={(e) => setForm({ ...form, slug: e.target.value.toLowerCase().replace(/[^a-z0-9-]/g, "").replace(/--+/g, "-") })} placeholder="slug-da-clinica" />
              <p className="text-xs text-muted-foreground mt-1">Deixe vazio para gerar automaticamente</p>
            </div>
          )}
          <div>
            <label className="text-sm font-medium text-foreground">CNPJ</label>
            <Input value={form.document} onChange={(e) => setForm({ ...form, document: formatCNPJ(e.target.value) })} placeholder="00.000.000/0001-00" />
          </div>
          <div>
            <label className="text-sm font-medium text-foreground">Telefone *</label>
            <Input className={errors.phone ? "border-red-500" : ""} value={form.phone} onChange={(e) => setForm({ ...form, phone: formatPhone(e.target.value) })} placeholder="(00) 00000-0000" />
            {errors.phone && <p className="text-xs text-red-500 mt-1">{errors.phone}</p>}
          </div>
          <div>
            <label className="text-sm font-medium text-foreground">Email *</label>
            <Input type="email" className={errors.email ? "border-red-500" : ""} value={form.email} onChange={(e) => setForm({ ...form, email: e.target.value })} placeholder="contato@clinica.com" />
            {errors.email && <p className="text-xs text-red-500 mt-1">{errors.email}</p>}
          </div>
          <Button onClick={handleSave} className="w-full">{editingId ? "Salvar Alterações" : "Criar Clínica"}</Button>
        </div>
      </Modal>

      {/* Modal de Credenciais */}
      <Modal
        isOpen={credentialsModal.isOpen}
        onClose={() => setCredentialsModal(prev => ({ ...prev, isOpen: false }))}
        title={credentialsModal.title}
      >
        <div className="space-y-6 py-2">
          <p className="text-sm text-gray-500 dark:text-gray-400">
            Guarde as credenciais de acesso inicial do administrador. Por motivos de segurança, a senha temporária é exibida apenas uma vez.
          </p>
          
          <div className="bg-gray-50 dark:bg-gray-900 p-5 rounded-2xl border border-gray-100 dark:border-gray-800 space-y-4 font-mono text-sm relative">
            <div>
              <span className="text-xs text-gray-400 block font-sans">E-mail do Administrador:</span>
              <span className="text-gray-900 dark:text-white font-bold select-all break-all">{credentialsModal.adminEmail}</span>
            </div>
            
            <div>
              <span className="text-xs text-gray-400 block font-sans">Senha Temporária:</span>
              <span className="text-gray-900 dark:text-white font-bold select-all">{credentialsModal.tempPassword}</span>
            </div>
          </div>
          
          <Button
            onClick={() => {
              navigator.clipboard.writeText(
                `E-mail: ${credentialsModal.adminEmail}\nSenha Temporária: ${credentialsModal.tempPassword}`
              );
              toast.success("Credenciais copiadas para a área de transferência!");
            }}
            className="w-full"
          >
            Copiar Credenciais
          </Button>
        </div>
      </Modal>
    </motion.div>
  );
}
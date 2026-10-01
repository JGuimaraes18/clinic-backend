import { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import { useFetch } from "@/hooks/useFetch";
import { getAppointments, createAppointment, updateAppointment, startAppointmentAttendance } from "@/services/appointmentsService";
import Modal from "@/components/modal/Modal";
import { getMedicalRecordByAppointment } from "@/services/medicalRecordService";
import { getPatients } from "@/services/patientService";
import { getProfessionals } from "@/services/professionalService";
import { Appointment, AppointmentForm } from "@/types/appointment";
import { useAuth } from "@/contexts/AuthContext";
import { Calendar, Stethoscope } from "lucide-react";

function formatDate(dateString: string) {
  const date = new Date(dateString);
  return date.toLocaleString("pt-BR");
}

function getNowForInput() {
  const now = new Date();
  now.setMinutes(now.getMinutes() - now.getTimezoneOffset());
  return now.toISOString().slice(0, 16);
}

function getStatusStyle(status: string) {
  switch (status) {
    case "AGENDADO":
      return "bg-blue-50 text-blue-600 border border-blue-200/60 shadow-sm shadow-blue-100";      
    case "REALIZADO":
      return "bg-green-50 text-green-600 border border-green-200/60 shadow-sm shadow-green-100";
    case "CANCELADO":
      return "bg-red-50 text-red-600 border border-red-200/60 shadow-sm shadow-red-100";
    case "EM_ATENDIMENTO":
      return "bg-yellow-50 text-yellow-700 border border-yellow-200/60 shadow-sm shadow-yellow-100";
    default:
      return "bg-gray-50 text-gray-600 border border-gray-200";
  }
}

function getStatusLabel(status: string) {
  switch (status) {
    case "AGENDADO":
      return "Agendado";      
    case "REALIZADO":
      return "Realizado";
    case "CANCELADO":
      return "Cancelado";
    case "EM_ATENDIMENTO":
      return "Em Atendimento";
    default:
      return status;
  }
}

export default function Appointments() {
  const { data, loading, error } =
    useFetch<Appointment[]>(getAppointments);

  const { data: patientsData } = useFetch(getPatients);
  const { data: professionalsData } = useFetch(getProfessionals);

  const patients = patientsData ?? [];
  const professionals = professionalsData ?? [];

  const [appointments, setAppointments] = useState<Appointment[]>([]);
  const [openModal, setOpenModal] = useState(false);
  const [editing, setEditing] = useState<Appointment | null>(null);
  const [statusFilter, setStatusFilter] = useState<string>("TODOS");
  const [dateFilter, setDateFilter] = useState<string>("");
  const [patientFilter, setPatientFilter] = useState<string>("TODOS");
  const [professionalFilter, setProfessionalFilter] = useState<string>("TODOS");
  const [submitted, setSubmitted] = useState(false);
  const [successMessage, setSuccessMessage] = useState<string | null>(null);
  const [cancelId, setCancelId] = useState<number | null>(null);
  const [saving, setSaving] = useState(false);

  const navigate = useNavigate();

  // AUTH GLOBAL CORRETO
  const { user: currentUser, isProfessional } = useAuth();

  const [form, setForm] = useState<AppointmentForm>({
    data_hora: "",
    status: "AGENDADO",
    observacoes: "",
    paciente: "",
    profissional: "",
  });

  const today = new Date();
  today.setHours(0, 0, 0, 0);

  const filteredAppointments = appointments.filter((a) => {
    const appointmentDate = new Date(a.data_hora);

    if (isNaN(appointmentDate.getTime())) {
      return false;
    }

    appointmentDate.setHours(0, 0, 0, 0);

    const matchStatus =
      statusFilter === "TODOS" || a.status === statusFilter;

    const matchPatient =
      patientFilter === "TODOS" ||
      String(a.paciente) === patientFilter;

    const matchProfessional =
      professionalFilter === "TODOS" ||
      String(a.profissional) === professionalFilter;

    const matchDate = dateFilter
      ? appointmentDate.toISOString().slice(0, 10) === dateFilter
      : appointmentDate.getTime() >= today.getTime();

    return matchStatus && matchDate && matchPatient && matchProfessional;
  });
    
  function handleClearFilters() {
    setPatientFilter("TODOS");
    setProfessionalFilter("TODOS");
    setDateFilter("");
  }

  useEffect(() => {
    if (data) {
      const sorted = [...data].sort(
        (a, b) =>
          new Date(a.data_hora).getTime() -
          new Date(b.data_hora).getTime()
      );

      setAppointments(sorted);
    }
  }, [data]);

  const isAdminOfClinic = currentUser?.memberships?.some(
    (m) => m.role === "ADMIN" || m.role === "PROFESSIONAL"
  );

  // -----------------------------
  // PERMISSÃO 
  // -----------------------------
  function canStart() {
    if (!currentUser) return false;

    if (currentUser.is_superuser) return true;

    if (isAdminOfClinic || isProfessional) return true;

    return false;
  }

  // -----------------------------
  // MODAL
  // -----------------------------
  function openNewModal() {
    setEditing(null);
    setSubmitted(false);
    setForm({
      data_hora: "",
      status: "AGENDADO",
      observacoes: "",
      paciente: "",
      profissional: "",
    });
    setOpenModal(true);
  }

  function openEditModal(appointment: Appointment) {
    if (appointment.status !== "AGENDADO") return;

    setEditing(appointment);
    setSubmitted(false);
    setForm({
      data_hora: appointment.data_hora.slice(0, 16),
      status: appointment.status,
      observacoes: appointment.observacoes,
      paciente: appointment.paciente,
      profissional: appointment.profissional,
    });
    setOpenModal(true);
  }

  function handleClose() {
    setOpenModal(false);
    setEditing(null);
    
  }

  function sortByDate(list: Appointment[]) {
    return [...list].sort(
      (a, b) =>
        new Date(a.data_hora).getTime() -
        new Date(b.data_hora).getTime()
    );
  }

  // -----------------------------
  // SAVE
  // -----------------------------
  async function handleSave() {
    if (saving) return;

    setSubmitted(true);

    if (!form.data_hora || !form.paciente || !form.profissional) {
      return;
    }

    try {
      setSaving(true);
      if (editing) {
        const updated = await updateAppointment(editing.id, form);

        setAppointments((prev) =>
          sortByDate(prev.map((a) => (a.id === editing.id ? updated : a)))  
        );

        setSuccessMessage("Agendamento atualizado com sucesso!");
      } else {
        const newAppointment = await createAppointment(form);

        setAppointments((prev) => sortByDate([...prev, newAppointment]));

        setSuccessMessage("Agendamento criado com sucesso!");
      }

      setTimeout(() => {
        setSuccessMessage(null);
      }, 2000);

      handleClose();
    } catch (err) {
      console.error(err);
    } finally {
      setSaving(false);
      setSubmitted(false);
    }
  }

  // -----------------------------
  // CANCEL (FIXED PATCH ISSUE)
  // -----------------------------

  async function handleCancel(id: number) {
    setCancelId(id);
  }

  async function confirmCancel() {
    if (!cancelId) return;

    const appointment = appointments.find((a) => a.id === cancelId);
    if (!appointment) return;

    const updated = await updateAppointment(cancelId, {
      ...appointment,
      status: "CANCELADO",
    });

    setAppointments((prev) => sortByDate(prev.map((a) => (a.id === cancelId ? updated : a))));

    setCancelId(null);
  }

  // -----------------------------
  // START APPOINTMENT
  // -----------------------------

  async function handleStart(appointmentId: number) {
    try {
      const res = await startAppointmentAttendance(appointmentId);

      navigate(`/atendimento/${res.prontuario_id}`);
    } catch (err) {
      console.error(err);
    }
  }

  async function handleAttendance(appointmentId: number) {
    try {
      const record = await getMedicalRecordByAppointment(appointmentId);
      navigate(`/atendimento/${record.id}`);
    } catch (err) {
      console.error(err);
    }
  }

  // -----------------------------
  // UI
  // -----------------------------
  return (
    <>
      <div className="p-6">
        {successMessage && (
          <div className="fixed top-6 right-6 z-50">
            <div className="bg-green-600 text-white px-4 py-3 rounded-lg shadow-lg text-sm">
              {successMessage}
            </div>
          </div>
        )}
        
        <div className="flex flex-col md:flex-row md:items-end justify-between mb-8 gap-4">
          <div className="space-y-1">
            <h1 className="text-3xl font-bold tracking-tight text-gray-900">
              Agendamentos
            </h1>
            <p className="text-sm text-gray-500 font-medium">
              Gerencie as consultas e atendimentos da clínica
            </p>
          </div>

          {!isProfessional && (
            <button
              onClick={openNewModal}
              className="bg-primary hover:bg-primary/90 text-white px-5 py-2.5 rounded-xl font-medium shadow-lg shadow-primary/25 transition-all transform hover:-translate-y-0.5"
            >
              + Novo Agendamento
            </button>
          )}
        </div>

        <div className="bg-white p-4 rounded-2xl shadow-sm border border-gray-100 mb-8 space-y-4">
          <div className="flex flex-wrap gap-2">
            {[
              { value: "AGENDADO", label: "Agendado" },
              { value: "EM_ATENDIMENTO", label: "Em Atendimento" },
              { value: "REALIZADO", label: "Realizado" },
              { value: "CANCELADO", label: "Cancelado" },
              { value: "TODOS", label: "Todos" },
            ].map((item) => (
              <button
                key={item.value}
                onClick={() => setStatusFilter(item.value)}
                className={`px-4 py-2 rounded-xl text-sm font-medium transition-all duration-200
                  ${
                    statusFilter === item.value
                      ? "bg-gray-900 text-white shadow-md shadow-gray-900/20"
                      : "bg-gray-50 text-gray-600 hover:bg-gray-100 hover:text-gray-900 border border-gray-200/60"
                  }`}
              >
                {item.label}
              </button>
            ))}
          </div>

          <div className="flex flex-wrap items-center gap-3">
            <input
              type="date"
              value={dateFilter}
              onChange={(e) => setDateFilter(e.target.value)}
              className="border border-gray-200 rounded-xl px-4 py-2 text-sm bg-gray-50 focus:bg-white focus:ring-2 focus:ring-primary/20 focus:border-primary outline-none transition-all"
            />

            <select
              value={patientFilter}
              onChange={(e) => setPatientFilter(e.target.value)}
              className="border border-gray-200 rounded-xl px-4 py-2 text-sm bg-gray-50 focus:bg-white focus:ring-2 focus:ring-primary/20 focus:border-primary outline-none transition-all"
            >
              <option value="TODOS">Todos os pacientes</option>
              {patients.map((p: any) => (
                <option key={p.id} value={p.id}>
                  {p.full_name}
                </option>
              ))}
            </select>

            <select
              value={professionalFilter}
              onChange={(e) => setProfessionalFilter(e.target.value)}
              className="border border-gray-200 rounded-xl px-4 py-2 text-sm bg-gray-50 focus:bg-white focus:ring-2 focus:ring-primary/20 focus:border-primary outline-none transition-all"
            >
              <option value="TODOS">Todos os profissionais</option>
              {professionals.map((p: any) => (
                <option key={p.id} value={p.id}>
                  {p.full_name}
                </option>
              ))}
            </select>

            <button
              onClick={handleClearFilters}
              className="text-gray-500 hover:text-gray-900 text-sm font-medium px-4 py-2 transition-colors ml-auto"
            >
              Limpar Filtros
            </button>
          </div>
        </div>

        <div className="grid gap-6 md:grid-cols-2 xl:grid-cols-3">
        {loading && <div className="col-span-full py-12 flex justify-center text-gray-400 font-medium">Carregando agendamentos...</div>}
        {error && <div className="col-span-full py-12 text-center text-red-500 font-medium">{error}</div>}
        {!loading && !error && filteredAppointments.length === 0 && (
          <div className="col-span-full py-16 flex flex-col items-center justify-center text-gray-400 bg-gray-50/50 rounded-3xl border border-dashed border-gray-200">
             <Calendar className="w-12 h-12 mb-3 text-gray-300" />
             <p className="font-medium">Nenhum agendamento encontrado.</p>
          </div>
        )}

          {filteredAppointments.map((a) => (
            <div 
              key={a.id} 
              className="bg-white border border-gray-100 rounded-3xl p-6 shadow-[0_2px_10px_-3px_rgba(6,81,237,0.05)] hover:shadow-[0_8px_30px_-4px_rgba(6,81,237,0.1)] transition-all duration-300 group flex flex-col" 
            >
              <div className="flex justify-between items-start mb-4">
                <div className="space-y-1">
                  <h4 className="text-2xl font-bold text-gray-900 tracking-tight">
                    {new Date(a.data_hora).toLocaleTimeString("pt-BR", { hour: '2-digit', minute: '2-digit' })}
                  </h4>
                  <p className="text-xs font-medium text-gray-400 uppercase tracking-wider">
                    {new Date(a.data_hora).toLocaleDateString("pt-BR")}
                  </p>
                </div>

                <span
                  className={`px-3 py-1.5 text-xs font-bold rounded-full transition-colors ${getStatusStyle(
                    a.status
                  )}`}
                >
                  {getStatusLabel(a.status)}
                </span>
              </div>

              <div className="flex-1 space-y-3 mb-6 bg-gray-50/50 p-4 rounded-2xl border border-gray-100/50">
                <div>
                  <p className="text-xs text-gray-400 uppercase tracking-wider font-semibold mb-1">Paciente</p>
                  <p className="font-semibold text-gray-800">{a.paciente_nome}</p>
                </div>
                <div>
                  <p className="text-xs text-gray-400 uppercase tracking-wider font-semibold mb-1">Profissional</p>
                  <p className="font-medium text-gray-600 flex items-center gap-2">
                    <Stethoscope size={14} className="text-primary" />
                    Dr(a). {a.profissional_nome}
                  </p>
                </div>
              </div>

              <div className="mt-auto">
                {a.status === "AGENDADO" && (
                  <div className="flex gap-2">
                    {canStart() && (
                      <button
                        onClick={() => handleStart(a.id)}
                        className="flex-1 bg-gray-900 hover:bg-black text-white px-4 py-2.5 rounded-xl text-sm font-medium transition-all shadow-md shadow-gray-900/20 hover:-translate-y-0.5"
                      >
                        Iniciar Consulta
                      </button>
                    )}

                        <button
                          onClick={() => openEditModal(a)}
                          className="px-4 py-2.5 rounded-xl text-sm font-medium bg-gray-100 text-gray-700 hover:bg-gray-200 transition-colors"
                        >
                          Editar
                        </button>

                        <button
                          onClick={() => handleCancel(a.id)}
                          className="px-4 py-2.5 rounded-xl text-sm font-medium bg-red-50 text-red-600 hover:bg-red-100 transition-colors"
                        >
                          Cancelar
                        </button>
                  </div>
                )}

                {a.status === "EM_ATENDIMENTO" && (
                  <div className="flex gap-2">
                    {canStart() && (
                      <button
                        onClick={() => handleAttendance(a.id)}
                        className="flex-1 bg-yellow-500 hover:bg-yellow-600 text-white px-4 py-2.5 rounded-xl text-sm font-medium transition-all shadow-md shadow-yellow-500/20 hover:-translate-y-0.5"
                      >
                        Continuar Consulta
                      </button>
                    )}
                  </div>
                )}
              </div>
            </div>
          ))}
        </div>
        {cancelId && (
          <div className="fixed inset-0 flex items-center justify-center bg-black/30">
            <div className="bg-white rounded-xl shadow-lg p-6 w-80">
              <h3 className="text-lg font-semibold mb-2">
                Cancelar agendamento
              </h3>

              <p className="text-sm text-gray-600 mb-6">
                Deseja realmente cancelar este agendamento?
              </p>

              <div className="flex justify-end gap-3">
                <button
                  onClick={() => setCancelId(null)}
                  className="px-4 py-2 text-sm rounded-lg border"
                >
                  Voltar
                </button>

                <button
                  onClick={confirmCancel}
                  className="px-4 py-2 text-sm rounded-lg bg-red-500 text-white hover:bg-red-600"
                >
                  Confirmar
                </button>
              </div>
            </div>
          </div>
        )}
      </div>

  
      {/* MODAL */}
      <Modal
        isOpen={openModal}
        onClose={handleClose}
        title={editing ? "Editar Agendamento" : "Novo Agendamento"}
      >
        <div className="space-y-3">
          <input
            type="datetime-local"
            min={getNowForInput()}
            value={form.data_hora}
            onChange={(e) =>
              setForm({ ...form, data_hora: e.target.value })
            }
            className={`w-full rounded p-2 border ${
              submitted && !form.data_hora ? "border-red-500" : "border-gray-300"
            }`}
          />

          <select
            value={form.paciente}
            onChange={(e) =>
              setForm({
                ...form,
                paciente: Number(e.target.value),
              })
            }
            className={`w-full rounded p-2 border ${
              submitted && !form.paciente ? "border-red-500" : "border-gray-300"
            }`}
          >
            <option value="">Selecione o paciente</option>
            {patients.map((p: any) => (
              <option key={p.id} value={p.id}>
                {p.full_name}
              </option>
            ))}
          </select>

          <select
            value={form.profissional}
            disabled={isProfessional}
            onChange={(e) =>
              setForm({
                ...form,
                profissional: Number(e.target.value),
              })
            }
            className={`w-full rounded p-2 border ${
              submitted && !form.profissional ? "border-red-500" : "border-gray-300"
            } ${isProfessional ? "bg-gray-100 cursor-not-allowed" : ""}`}
          >
            <option value="">Selecione o profissional</option>
            {professionals.map((p: any) => (
              <option key={p.id} value={p.id}>
                {p.full_name}
              </option>
            ))}
          </select>

          <div className="flex justify-end gap-3">
            <button
              onClick={handleClose}
              className="border px-4 py-1 rounded-lg"
            >
              Cancelar
            </button>

            <button
              onClick={handleSave}
              disabled={saving}
              className={`px-4 py-1 rounded-lg text-white ${
                saving
                  ? "bg-blue-400 cursor-not-allowed"
                  : "bg-blue-600 hover:bg-blue-700"
              }`}
            >
              {saving ? "Salvando..." : "Salvar"}
            </button>
          </div>
        </div>
      </Modal>
    </>
  );
}
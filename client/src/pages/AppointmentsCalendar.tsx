import { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import { useFetch } from "@/hooks/useFetch";

import {
  getAppointments,
  createAppointment,
  updateAppointment,
  startAppointmentAttendance,
} from "@/services/appointmentsService";

import Modal from "@/components/modal/Modal";

import { getMedicalRecordByAppointment } from "@/services/medicalRecordService";
import { getPatients } from "@/services/patientService";
import { getProfessionals } from "@/services/professionalService";

import { Appointment, AppointmentForm } from "@/types/appointment";
import { useAuth } from "@/contexts/AuthContext";

function getNowForInput() {
  const now = new Date();
  now.setMinutes(now.getMinutes() - now.getTimezoneOffset());
  return now.toISOString().slice(0, 16);
}

function getStatusStyle(status: string) {
  switch (status) {
    case "AGENDADO":
      return {
        card: "bg-blue-50 border-blue-200",
        badge: "bg-blue-100 text-blue-700",
      };

    case "EM_ATENDIMENTO":
      return {
        card: "bg-yellow-50 border-yellow-200",
        badge: "bg-yellow-100 text-yellow-700",
      };

    case "REALIZADO":
      return {
        card: "bg-green-50 border-green-200",
        badge: "bg-green-100 text-green-700",
      };

    case "CANCELADO":
      return {
        card: "bg-red-50 border-red-200 opacity-70",
        badge: "bg-red-100 text-red-700",
      };

    default:
      return {
        card: "bg-gray-50 border-gray-200",
        badge: "bg-gray-100 text-gray-700",
      };
  }
}

function getStatusLabel(status: string) {
  switch (status) {
    case "AGENDADO":
      return "Agendado";

    case "EM_ATENDIMENTO":
      return "Em Atendimento";

    case "REALIZADO":
      return "Realizado";

    case "CANCELADO":
      return "Cancelado";

    default:
      return "Desconhecido";
  }
}

export default function AppointmentsCalendar() {
  const { data } =
    useFetch<Appointment[]>(getAppointments);

  const { data: patientsData } = useFetch(getPatients);
  const { data: professionalsData } = useFetch(getProfessionals);

  const patients = patientsData ?? [];
  const professionals = professionalsData ?? [];

  const [appointments, setAppointments] = useState<Appointment[]>([]);
  const [openModal, setOpenModal] = useState(false);
  const [editing, setEditing] = useState<Appointment | null>(null);

  const [statusFilter, setStatusFilter] = useState<string>("TODOS");
  const [dateFilter, setDateFilter] = useState<string>(() => {
    const today = new Date();
    return today.toISOString().split("T")[0];
  });

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

  const filteredAppointments = appointments.filter((a) => {
    const appointmentDate = a.data_hora.split("T")[0];

    const matchStatus =
      statusFilter === "TODOS" || a.status === statusFilter;

    const matchDate =
      !dateFilter || appointmentDate === dateFilter;

    const matchPatient =
      patientFilter === "TODOS" ||
      String(a.paciente) === patientFilter;

    const matchProfessional =
      professionalFilter === "TODOS" ||
      String(a.profissional) === professionalFilter;

    return matchStatus && matchDate && matchPatient && matchProfessional;
  });
    
  const appointmentsOfDay = filteredAppointments.filter((a) => {
    const d = new Date(a.data_hora);
    return d.toISOString().slice(0, 10) === dateFilter;
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

  function generateHours() {
    const hours = [];
    for (let h = 0; h < 24; h++) {
      hours.push(`${h.toString().padStart(2, "0")}:00`);
    }
    return hours;
  }

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
        
        <div className="flex justify-between items-center mb-6 flex-wrap gap-4">
          <div>
            <h1 className="text-2xl font-bold">
              Agendamentos
            </h1>
            <p className="text-sm text-gray-500">
              Lista de agendamentos cadastrados
            </p>
          </div>

          {!isProfessional && (
            <button
              onClick={openNewModal}
              className="bg-blue-600 text-white px-4 py-1 rounded-lg"
            >
              + Novo
            </button>
          )}
        </div>

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
              className={`px-3 py-1 rounded-full text-sm transition mb-4
                ${
                  statusFilter === item.value
                    ? "bg-blue-600 text-white"
                    : "bg-gray-100 text-gray-600 hover:bg-gray-200"
                }`}
            >
              {item.label}
            </button>
          ))}
        </div>

        <div className="flex flex-wrap gap-3 mb-6">
          <input
            type="date"
            value={dateFilter}
            onChange={(e) => setDateFilter(e.target.value)}
            className="border rounded-lg px-3 py-1 text-xs"
          />

          <select
            value={patientFilter}
            onChange={(e) => setPatientFilter(e.target.value)}
            className="border rounded-lg px-3 py-1 text-xs"
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
            className="border rounded-lg px-3 py-1 text-xs"
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
            className="border rounded-lg px-3 py-1 text-xs"
          >
            Limpar Filtros
          </button>
        </div>

        <div className="bg-white rounded-xl border shadow-sm overflow-hidden">
          {generateHours().map((hour) => {
            const hourAppointments = appointmentsOfDay.filter((a) => {
              const d = new Date(a.data_hora);
              const appointmentHour = d
                .getHours()
                .toString()
                .padStart(2, "0") + ":00";
              return appointmentHour === hour;
            });

            return (
              <div
                key={hour}
                className="flex border-b last:border-b-0 min-h-[40px]"
              >
                {/* Coluna horário */}
                <div className="w-14 bg-gray-50 text-sm text-gray-500 flex items-start justify-center pt-3 border-r text-xs">
                  {hour}
                </div>

                {/* Coluna compromissos */}
                <div className="flex-1 p-3 space-y-2">
                  {hourAppointments.map((a) => {
                    const styles = getStatusStyle(a.status);

                    return (
                      <div
                        key={a.id}
                        className={`border rounded-lg p-1 text-xs shadow-sm transition ${styles.card}`}
                      >
                        <div className="text-xs font-bold mb-1">
                          {new Date(a.data_hora).toLocaleTimeString("pt-BR", {
                            hour: "2-digit",
                            minute: "2-digit",
                          })}
                        </div>

                        <div className="flex justify-between items-start">
                          <div className="font-semibold">
                            Paciente: {a.paciente_nome}
                          </div>

                          <div
                            className={`text-xs font-medium px-1 py-1 rounded-full ${styles.badge}`}
                          >
                            {getStatusLabel(a.status)}
                          </div>
                        </div>

                        <div className="text-xs text-gray-600 mt-1">
                          Dr(a). {a.profissional_nome}
                        </div>

                        {a.status === "AGENDADO" && (
                          <div className="flex flex-wrap gap-1 mt-2">
                            {canStart() && (
                              <button
                                onClick={() => handleStart(a.id)}
                                className="bg-green-600 text-white px-2 py-1 rounded-lg"
                              >
                                Iniciar
                              </button>
                            )}

                            {!isProfessional && (
                              <>
                                <button
                                  onClick={() => openEditModal(a)}
                                  className="bg-gray-500 text-white px-2 py-1 rounded-lg text-xs"
                                >
                                  Editar
                                </button>

                                <button
                                  onClick={() => handleCancel(a.id)}
                                  className="bg-red-500 text-white px-2 py-1 rounded-lg text-xs"
                                >
                                  Cancelar
                                </button>
                              </>
                            )}
                          </div>
                        )}

                        {a.status === "EM_ATENDIMENTO" && canStart() && (
                          <button
                            onClick={() => handleAttendance(a.id)}
                            className="mt-3 bg-yellow-600 text-white px-2 py-1 rounded-lg text-xs"
                          >
                            Continuar
                          </button>
                        )}
                      </div>
                    );
                  })}
                </div>
              </div>
            );
          })}
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
            onChange={(e) =>
              setForm({
                ...form,
                profissional: Number(e.target.value),
              })
            }
            className={`w-full rounded p-2 border ${
              submitted && !form.profissional ? "border-red-500" : "border-gray-300"
            }`}
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
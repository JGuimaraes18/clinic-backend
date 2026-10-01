import { useState, useEffect } from "react";
import Modal from "@/components/modal/Modal";
import { useFetch } from "@/hooks/useFetch";
import { useAuth } from "@/contexts/AuthContext";
import { getProfessionals, createProfessional, updateProfessional } from "@/services/professionalService";
import { getUsers } from "@/services/authService";
import { Professional, ProfessionalForm } from "@/types/professional";
import { User } from "@/types/users";

export default function Professionals() {
  const { user } = useAuth();
  const { data, loading, error } = useFetch<Professional[]>(getProfessionals);

  const [professionals, setProfessionals] = useState<Professional[]>([]);
  const [users, setUsers] = useState<User[]>([]);

  const [isOpen, setIsOpen] = useState(false);
  const [editingId, setEditingId] = useState<number | null>(null);
  const [successMessage, setSuccessMessage] = useState<string | null>(null);

  const [form, setForm] = useState<ProfessionalForm>({
    user: null,
    registration_type: "",
    registration_number: "",
    specialty: "",
    is_active: true,
  });

  const [errors, setErrors] = useState<Partial<ProfessionalForm>>({});

  const clinicId = Number(localStorage.getItem("clinic_id"));

  const isAdminOfClinic = user?.memberships?.some(
    (m) => m.role === "ADMIN"
  );

  const canCreateProfessional = user?.is_superuser || isAdminOfClinic;

  useEffect(() => {
    if (data) setProfessionals(data);
  }, [data]);

  useEffect(() => {
    async function loadUsers() {
      try {
        const res = await getUsers();
        setUsers(res);
      } catch (err) {
        console.error("Erro ao carregar users", err);
      }
    }

    loadUsers();
  }, []);


  function validate() {
    const newErrors: Partial<ProfessionalForm> = {};

    if (!form.user)
      newErrors.user  = "Usuário é obrigatório";

    if (!form.registration_type.trim())
      newErrors.registration_type = "Tipo de registro obrigatório";

    if (!form.registration_number.trim())
      newErrors.registration_number = "Número obrigatório";

    if (!form.specialty.trim())
      newErrors.specialty = "Especialidade obrigatória";

    setErrors(newErrors);

    return Object.keys(newErrors).length === 0;
  }

  function handleClose() {
    setIsOpen(false);
    setEditingId(null);

    setForm({
      user: null,
      registration_type: "",
      registration_number: "",
      specialty: "",
      is_active: true,
    });

    setErrors({});
  }

  async function handleSave() {
    if (!validate()) return;

    const payload = {
      user: form.user,
      registration_type: form.registration_type,
      registration_number: form.registration_number,
      specialty: form.specialty,
      is_active: form.is_active,
    };

    try {
      if (editingId) {
        const updated = await updateProfessional(editingId, payload as any);

        setProfessionals((prev) =>
          prev.map((p) => (p.id === editingId ? updated : p))
        );

        setSuccessMessage("Profissional atualizado com sucesso!");
      } else {
        const created = await createProfessional(payload);

        setProfessionals((prev) => [...prev, created]);
        setSuccessMessage("Profissional criado com sucesso!");
      }

      handleClose();

      setTimeout(() => setSuccessMessage(null), 3000);
    } catch (err) {
      console.error(err);
    }
  }

  function handleEdit(professional: Professional) {
    setEditingId(professional.id);

    setForm({
      user: professional.user,
      registration_type: professional.registration_type,
      registration_number: professional.registration_number,
      specialty: professional.specialty || "",
      is_active: professional.is_active,
    });

    setIsOpen(true);
  }

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

        {/* HEADER */}
        <div className="flex justify-between items-center mb-6">
          <div>
            <h1 className="text-2xl font-bold text-gray-800">
              Profissionais
            </h1>
            <p className="text-sm text-gray-500">
              Profissionais cadastrados no sistema
            </p>
          </div>

        {canCreateProfessional && (
          <button
            onClick={() => setIsOpen(true)}
            className="bg-blue-600 text-white px-4 py-1 rounded-lg"
          >
            + Novo
          </button>
        )}
        </div>

        {/* LIST */}
        {loading && (
          <div className="p-6 text-gray-500">
            Carregando profissionais...
          </div>
        )}

        {error && (
          <div className="p-6 text-red-500 font-medium">
            {error}
          </div>
        )}

        {!loading && professionals.length === 0 && (
          <div className="bg-white border rounded-xl p-6 text-center text-gray-500">
            Nenhum profissional cadastrado.
          </div>
        )}

        {!loading && professionals.length > 0 && (
          <div className="grid gap-6 md:grid-cols-2 xl:grid-cols-3">
            {[...professionals]
              .sort((a, b) =>
                a.full_name.localeCompare(b.full_name, "pt-BR", {
                  sensitivity: "base",
                })
              )
              .map((p) => (
                <div
                  key={p.id}
                  onClick={() => handleEdit(p)}
                  className="bg-white border rounded-xl p-5 shadow-sm hover:shadow-md transition cursor-pointer"
                >
                  <h3 className="text-sm font-semibold">
                    {p.full_name}
                  </h3>

                  <p className="text-xs text-gray-500">
                    {p.email}
                  </p>

                  <div className="mt-4 space-y-1 text-xs">
                    <p>
                      <span className="font-medium">
                        Registro:
                      </span>{" "}
                      {p.registration_type} -{" "}
                      {p.registration_number}
                    </p>

                    <p>
                      <span className="font-medium">
                        Especialidade:
                      </span>{" "}
                      {p.specialty || "-"}
                    </p>

                    <p>
                      <span className="font-medium">
                        Status:
                      </span>{" "}
                      <span
                        className={`font-semibold ${
                          p.is_active
                            ? "text-green-600"
                            : "text-red-600"
                        }`}
                      >
                        {p.is_active ? "Ativo" : "Inativo"}
                      </span>
                    </p>
                  </div>
                </div>
              ))}
          </div>
        )}
      </div>

      {/* MODAL */}
      <Modal
        isOpen={isOpen}
        onClose={handleClose}
        title={
          editingId
            ? "Editar Profissional"
            : "Novo Profissional"
        }
      >
        <div className="space-y-3">

          {/* USER SELECT */}
          <select
            value={form.user || ""}
            onChange={(e) =>
              setForm({
                ...form,
                user: Number(e.target.value),
              })
            }
            className={`w-full border p-3 rounded-lg ${
              errors.user ? "border-red-500" : "border-gray-300"
            }`}
          >
            <option value="">Selecione o usuário</option>
            {users
              .filter((u) =>
                u.memberships?.some((m) => m.role === "PROFESSIONAL")
              )
              .map((u) => (
                <option key={u.id} value={u.id}>
                  {u.first_name} {u.last_name} ({u.email})
                </option>
              ))}
          </select>

          <input
            type="text"
            placeholder="Tipo de registro (CRM, CRO...)"
            className="w-full border p-3 rounded-lg"
            value={form.registration_type}
            onChange={(e) =>
              setForm({
                ...form,
                registration_type: e.target.value,
              })
            }
          />

          <input
            type="text"
            placeholder="Número do registro"
            className="w-full border p-3 rounded-lg"
            value={form.registration_number}
            onChange={(e) =>
              setForm({
                ...form,
                registration_number: e.target.value,
              })
            }
          />

          <input
            type="text"
            placeholder="Especialidade"
            className="w-full border p-3 rounded-lg"
            value={form.specialty}
            onChange={(e) =>
              setForm({
                ...form,
                specialty: e.target.value,
              })
            }
          />

          <div className="flex items-center gap-2">
            <input
              type="checkbox"
              checked={form.is_active}
              onChange={(e) =>
                setForm({
                  ...form,
                  is_active: e.target.checked,
                })
              }
            />
            <span className="text-sm">Ativo</span>
          </div>

          <button
            onClick={handleSave}
            className="w-full bg-green-600 text-white py-3 rounded-lg hover:bg-green-700 transition"
          >
            {editingId
              ? "Salvar Alterações"
              : "Criar Profissional"}
          </button>
        </div>
      </Modal>
    </>
  );
}
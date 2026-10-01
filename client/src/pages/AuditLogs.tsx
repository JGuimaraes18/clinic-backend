import { useEffect, useState } from "react";
import api from "@/services/api";
import { Search, Filter, Calendar, Info, ShieldAlert } from "lucide-react";
import { toast } from "sonner";

interface AuditLog {
  id: number;
  severity: "LOW" | "MEDIUM" | "HIGH" | "CRITICAL";
  action: "CREATE" | "UPDATE" | "DELETE";
  model_name: string;
  object_id: string;
  before_data: Record<string, any> | null;
  after_data: Record<string, any> | null;
  ip_address: string | null;
  timestamp: string;
  user_detail: {
    id: number;
    email: string;
    full_name: string;
  } | null;
  clinic_name: string | null;
}

export default function AuditLogs() {
  const [logs, setLogs] = useState<AuditLog[]>([]);
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState("");
  const [selectedAction, setSelectedAction] = useState("");
  const [selectedLog, setSelectedLog] = useState<AuditLog | null>(null);

  useEffect(() => {
    async function loadLogs() {
      try {
        const { data } = await api.get("/api/audit-logs/");
        setLogs(data);
      } catch (err: any) {
        console.error(err);
        toast.error("Erro ao carregar logs de auditoria.");
      } finally {
        setLoading(false);
      }
    }
    loadLogs();
  }, []);

  const filteredLogs = logs.filter(log => {
    const matchesSearch =
      (log.user_detail?.email || "").toLowerCase().includes(searchTerm.toLowerCase()) ||
      (log.model_name || "").toLowerCase().includes(searchTerm.toLowerCase()) ||
      (log.clinic_name || "").toLowerCase().includes(searchTerm.toLowerCase());
    
    const matchesAction = selectedAction ? log.action === selectedAction : true;
    
    return matchesSearch && matchesAction;
  });

  return (
    <div className="max-w-7xl mx-auto py-8 px-4 space-y-6 animate-in fade-in duration-300">
      <div>
        <h2 className="text-3xl font-extrabold tracking-tight text-gray-900 dark:text-white">
          Auditoria & Logs
        </h2>
        <p className="mt-1 text-sm text-gray-500 dark:text-gray-400">
          Rastreabilidade completa de todas as ações de criação, modificação e deleção na plataforma.
        </p>
      </div>

      {/* FILTROS E BUSCA */}
      <div className="flex flex-col sm:flex-row gap-4 bg-white dark:bg-gray-800 p-4 rounded-2xl border border-gray-100 dark:border-gray-700/50 shadow-md">
        <div className="relative flex-1">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400" size={18} />
          <input
            type="text"
            placeholder="Buscar por usuário, clínica ou modelo..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="w-full pl-10 pr-4 py-2 border border-gray-200 dark:border-gray-700 rounded-xl bg-gray-50 dark:bg-gray-900/50 text-sm focus:outline-none focus:ring-2 focus:ring-primary/20 focus:border-primary text-gray-900 dark:text-white"
          />
        </div>
        <div className="flex items-center gap-3">
          <Filter className="text-gray-400" size={18} />
          <select
            value={selectedAction}
            onChange={(e) => setSelectedAction(e.target.value)}
            className="px-3 py-2 border border-gray-200 dark:border-gray-700 rounded-xl bg-gray-50 dark:bg-gray-900/50 text-sm focus:outline-none text-gray-900 dark:text-white"
          >
            <option value="">Todas as Ações</option>
            <option value="CREATE">Criação</option>
            <option value="UPDATE">Atualização</option>
            <option value="DELETE">Deleção</option>
          </select>
        </div>
      </div>

      {/* TABELA DE LOGS */}
      <div className="bg-white dark:bg-gray-800 rounded-2xl border border-gray-100 dark:border-gray-700/50 shadow-lg overflow-hidden">
        <div className="overflow-x-auto">
          {loading ? (
            <div className="py-20 text-center text-gray-500 dark:text-gray-400">
              Carregando registros de auditoria...
            </div>
          ) : filteredLogs.length === 0 ? (
            <div className="py-20 text-center text-gray-500 dark:text-gray-400 flex flex-col items-center gap-2">
              <ShieldAlert size={48} className="text-gray-300" />
              <span>Nenhum log encontrado.</span>
            </div>
          ) : (
            <table className="w-full border-collapse text-left text-sm text-gray-500 dark:text-gray-400">
              <thead className="bg-gray-50 dark:bg-gray-900/50 text-xs uppercase text-gray-700 dark:text-gray-300 font-semibold border-b border-gray-100 dark:border-gray-700">
                <tr>
                  <th scope="col" className="px-6 py-4">Data/Hora</th>
                  <th scope="col" className="px-6 py-4">Usuário</th>
                  <th scope="col" className="px-6 py-4">Clínica</th>
                  <th scope="col" className="px-6 py-4">Ação</th>
                  <th scope="col" className="px-6 py-4">Módulo/Tabela</th>
                  <th scope="col" className="px-6 py-4">ID Objeto</th>
                  <th scope="col" className="px-6 py-4">IP</th>
                  <th scope="col" className="px-6 py-4 text-center">Detalhes</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-100 dark:divide-gray-700/50">
                {filteredLogs.map((log) => {
                  const actionColors = {
                    CREATE: "bg-emerald-50 text-emerald-700 dark:bg-emerald-950/30 dark:text-emerald-400",
                    UPDATE: "bg-blue-50 text-blue-700 dark:bg-blue-950/30 dark:text-blue-400",
                    DELETE: "bg-rose-50 text-rose-700 dark:bg-rose-950/30 dark:text-rose-400",
                  };
                  const severityColors = {
                    LOW: "text-gray-400",
                    MEDIUM: "text-blue-500",
                    HIGH: "text-orange-500 font-semibold",
                    CRITICAL: "text-red-600 font-bold",
                  };

                  return (
                    <tr key={log.id} className="hover:bg-gray-50/50 dark:hover:bg-gray-700/20 transition-colors">
                      <td className="px-6 py-4 font-medium text-gray-900 dark:text-white whitespace-nowrap">
                        <div className="flex items-center gap-1.5">
                          <Calendar size={14} className="text-gray-400" />
                          {new Date(log.timestamp).toLocaleString("pt-BR")}
                        </div>
                      </td>
                      <td className="px-6 py-4">
                        <div className="font-semibold text-gray-800 dark:text-gray-200">
                          {log.user_detail?.full_name || "Sistema"}
                        </div>
                        <div className="text-xs text-gray-400">{log.user_detail?.email || "N/A"}</div>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <span className="font-medium text-gray-700 dark:text-gray-300">
                          {log.clinic_name || "Global / Plataforma"}
                        </span>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <span className={`px-2 py-1 rounded-lg text-xs font-semibold uppercase tracking-wider ${actionColors[log.action]}`}>
                          {log.action}
                        </span>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap font-mono text-xs text-gray-600 dark:text-gray-400">
                        {log.model_name}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-xs">
                        #{log.object_id}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-xs text-gray-400">
                        {log.ip_address || "127.0.0.1"}
                      </td>
                      <td className="px-6 py-4 text-center whitespace-nowrap">
                        <button
                          onClick={() => setSelectedLog(log)}
                          className="text-primary hover:text-primary/80 transition-colors p-1.5 hover:bg-primary/5 rounded-lg cursor-pointer inline-flex items-center"
                          title="Exibir dados salvos"
                        >
                          <Info size={16} />
                        </button>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          )}
        </div>
      </div>

      {/* DIALOG DE DETALHES (MODAL) */}
      {selectedLog && (
        <div className="fixed inset-0 bg-black/50 z-50 flex items-center justify-center p-4 backdrop-blur-sm animate-in fade-in duration-200">
          <div className="bg-white dark:bg-gray-800 rounded-3xl w-full max-w-4xl shadow-2xl border border-gray-100 dark:border-gray-700 overflow-hidden flex flex-col max-h-[85vh] animate-in zoom-in-95 duration-200">
            <div className="px-6 py-4 border-b border-gray-100 dark:border-gray-700 flex justify-between items-center bg-gray-50/50 dark:bg-gray-900/20">
              <div>
                <h3 className="text-lg font-bold text-gray-900 dark:text-white">
                  Detalhes do Log #{selectedLog.id}
                </h3>
                <p className="text-xs text-gray-400 mt-0.5">
                  Tabela: <span className="font-mono text-primary font-semibold">{selectedLog.model_name}</span> (ID: #{selectedLog.object_id})
                </p>
              </div>
              <button
                onClick={() => setSelectedLog(null)}
                className="text-gray-400 hover:text-gray-600 dark:hover:text-white p-2 hover:bg-gray-100 dark:hover:bg-gray-700 rounded-xl cursor-pointer"
              >
                Fechar
              </button>
            </div>
            
            <div className="p-6 overflow-y-auto space-y-6 flex-1 custom-scrollbar">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <div>
                  <h4 className="text-sm font-semibold text-gray-500 dark:text-gray-400 mb-2">Dados Anteriores (Before)</h4>
                  <pre className="p-4 bg-gray-50 dark:bg-gray-900 rounded-2xl text-xs font-mono overflow-auto border border-gray-100 dark:border-gray-800 max-h-[45vh] custom-scrollbar text-gray-800 dark:text-gray-300">
                    {selectedLog.before_data ? JSON.stringify(selectedLog.before_data, null, 2) : "Nenhum dado cadastrado."}
                  </pre>
                </div>
                <div>
                  <h4 className="text-sm font-semibold text-gray-500 dark:text-gray-400 mb-2">Novos Dados (After)</h4>
                  <pre className="p-4 bg-gray-50 dark:bg-gray-900 rounded-2xl text-xs font-mono overflow-auto border border-gray-100 dark:border-gray-800 max-h-[45vh] custom-scrollbar text-gray-800 dark:text-gray-300">
                    {selectedLog.after_data ? JSON.stringify(selectedLog.after_data, null, 2) : "Nenhum dado alterado."}
                  </pre>
                </div>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

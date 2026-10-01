import { useEffect, useState } from "react";
import { useAuth } from "@/contexts/AuthContext";
import { getClinics } from "@/services/clinicService";
import { Clinic } from "@/types/clinic";
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import {
  Building2,
  Users,
  Activity,
  ShieldCheck,
  CheckCircle2,
  XCircle,
} from "lucide-react";
import { motion } from "framer-motion";

export default function PlatformDashboard() {
  const { user } = useAuth();
  const [loading, setLoading] = useState(true);
  const [clinics, setClinics] = useState<Clinic[]>([]);

  useEffect(() => {
    async function loadData() {
      try {
        const data = await getClinics();
        setClinics(data);
      } catch (error) {
        console.error("Failed to load platform data", error);
      } finally {
        setLoading(false);
      }
    }
    loadData();
  }, []);

  const activeClinics = clinics.filter((c) => c.is_active !== false);
  const inactiveClinics = clinics.filter((c) => c.is_active === false);
  const totalUsers = clinics.reduce((sum, c) => sum + (c.user_count || 0), 0);

  const stats = [
    {
      title: "Total de Clínicas",
      value: clinics.length,
      icon: Building2,
      description: "Registradas na plataforma",
      color: "text-blue-600",
      bg: "bg-blue-50",
    },
    {
      title: "Clínicas Ativas",
      value: activeClinics.length,
      icon: CheckCircle2,
      description: `${inactiveClinics.length} inativa${inactiveClinics.length !== 1 ? "s" : ""}`,
      color: "text-emerald-600",
      bg: "bg-emerald-50",
    },
    {
      title: "Usuários na Plataforma",
      value: totalUsers,
      icon: Users,
      description: "Total de contas vinculadas",
      color: "text-purple-600",
      bg: "bg-purple-50",
    },
  ];

  const containerVariants = {
    hidden: { opacity: 0, y: 20 },
    visible: {
      opacity: 1,
      y: 0,
      transition: { duration: 0.4, staggerChildren: 0.1 },
    },
  };

  const itemVariants = {
    hidden: { opacity: 0, y: 20 },
    visible: { opacity: 1, y: 0 },
  };

  return (
    <motion.div
      className="space-y-8"
      initial="hidden"
      animate="visible"
      variants={containerVariants}
    >
      {/* Header */}
      <div className="flex flex-col gap-2">
        <div className="flex items-center gap-3">
          <div className="p-2.5 rounded-xl bg-primary/10">
            <ShieldCheck className="w-6 h-6 text-primary" />
          </div>
          <div>
            <h1 className="text-3xl font-bold tracking-tight text-foreground">
              Painel da Plataforma
            </h1>
            <p className="text-muted-foreground">
              Olá, {user?.first_name || "Administrador"}. Visão geral da plataforma SaaS.
            </p>
          </div>
        </div>
      </div>

      {/* Stats */}
      <div className="grid gap-6 md:grid-cols-3">
        {stats.map((stat, index) => {
          const Icon = stat.icon;
          return (
            <motion.div key={index} variants={itemVariants}>
              <Card className="border-none shadow-md bg-card/50 backdrop-blur-sm transition-all duration-200 hover:shadow-lg hover:-translate-y-1">
                <CardHeader className="flex flex-row items-center justify-between pb-2">
                  <CardTitle className="text-sm font-medium text-muted-foreground">
                    {stat.title}
                  </CardTitle>
                  <div className={`p-2 rounded-xl ${stat.bg}`}>
                    <Icon className={`w-5 h-5 ${stat.color}`} />
                  </div>
                </CardHeader>
                <CardContent>
                  {loading ? (
                    <Skeleton className="h-8 w-[100px] mt-1" />
                  ) : (
                    <>
                      <div className="text-3xl font-bold">{stat.value}</div>
                      <p className="text-xs text-muted-foreground mt-1">
                        {stat.description}
                      </p>
                    </>
                  )}
                </CardContent>
              </Card>
            </motion.div>
          );
        })}
      </div>

      {/* Recent Clinics */}
      <motion.div variants={itemVariants}>
        <Card className="border-none shadow-md bg-card/50 backdrop-blur-sm">
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Building2 className="w-5 h-5" />
              Clínicas Recentes
            </CardTitle>
            <p className="text-sm text-muted-foreground">
              Últimas clínicas cadastradas na plataforma
            </p>
          </CardHeader>
          <CardContent>
            {loading ? (
              <div className="space-y-4">
                {[1, 2, 3].map((i) => (
                  <div key={i} className="flex items-center gap-4">
                    <Skeleton className="h-10 w-10 rounded-xl" />
                    <div className="space-y-2 flex-1">
                      <Skeleton className="h-4 w-[200px]" />
                      <Skeleton className="h-3 w-[150px]" />
                    </div>
                  </div>
                ))}
              </div>
            ) : clinics.length > 0 ? (
              <div className="space-y-3">
                {[...clinics]
                  .sort((a, b) => {
                    const da = a.created_at ? new Date(a.created_at).getTime() : 0;
                    const db = b.created_at ? new Date(b.created_at).getTime() : 0;
                    return db - da;
                  })
                  .slice(0, 5)
                  .map((clinic) => (
                    <div
                      key={clinic.id}
                      className="flex items-center justify-between p-3 rounded-xl hover:bg-muted/50 transition-colors"
                    >
                      <div className="flex items-center gap-3">
                        <div className="w-10 h-10 rounded-xl bg-primary/10 flex items-center justify-center">
                          <Building2 className="w-5 h-5 text-primary" />
                        </div>
                        <div>
                          <p className="font-semibold text-sm">{clinic.name}</p>
                          <p className="text-xs text-muted-foreground">
                            {clinic.admin_email || "Sem administrador"} · {clinic.user_count || 0} usuário{(clinic.user_count || 0) !== 1 ? "s" : ""}
                          </p>
                        </div>
                      </div>
                      <div className="flex items-center gap-2">
                        {clinic.is_active !== false ? (
                          <span className="flex items-center gap-1 px-2.5 py-1 text-xs font-medium bg-emerald-50 text-emerald-700 rounded-full">
                            <CheckCircle2 className="w-3 h-3" /> Ativa
                          </span>
                        ) : (
                          <span className="flex items-center gap-1 px-2.5 py-1 text-xs font-medium bg-red-50 text-red-700 rounded-full">
                            <XCircle className="w-3 h-3" /> Inativa
                          </span>
                        )}
                      </div>
                    </div>
                  ))}
              </div>
            ) : (
              <div className="flex flex-col items-center justify-center py-12 text-center text-muted-foreground">
                <div className="bg-muted p-4 rounded-full mb-4">
                  <Building2 className="w-8 h-8 opacity-50" />
                </div>
                <p className="font-medium text-foreground">
                  Nenhuma clínica cadastrada
                </p>
                <p className="text-sm mt-1">
                  Crie a primeira clínica na aba "Clínicas".
                </p>
              </div>
            )}
          </CardContent>
        </Card>
      </motion.div>
    </motion.div>
  );
}

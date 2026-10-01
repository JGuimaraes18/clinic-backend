import { useEffect, useState } from "react";
import { useAuth } from "@/contexts/AuthContext";
import { getAppointments } from "@/services/appointmentsService";
import { getPatients } from "@/services/patientService";
import { getProfessionals } from "@/services/professionalService";
import { Appointment } from "@/types/appointment";
import { Patient } from "@/types/patient";
import { Professional } from "@/types/professional";
import { 
  Card, 
  CardContent, 
  CardHeader, 
  CardTitle,
} from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { 
  Calendar, 
  Users, 
  UserRound, 
  Activity,
  CalendarCheck2,
  Stethoscope,
  ArrowRight
} from "lucide-react";
import { Link } from "react-router-dom";
import { Button } from "@/components/ui/button";
import { motion } from "framer-motion";

export default function Home() {
  const { user } = useAuth();
  
  const [loading, setLoading] = useState(true);
  const [appointments, setAppointments] = useState<Appointment[]>([]);
  const [patients, setPatients] = useState<Patient[]>([]);
  const [professionals, setProfessionals] = useState<Professional[]>([]);

  useEffect(() => {
    async function loadData() {
      try {
        const [appts, pats, profs] = await Promise.all([
          getAppointments(),
          getPatients(),
          getProfessionals()
        ]);
        setAppointments(appts);
        setPatients(pats);
        setProfessionals(profs);
      } catch (error) {
        console.error("Failed to load dashboard data", error);
      } finally {
        setLoading(false);
      }
    }
    loadData();
  }, []);

  const today = new Date();
  today.setHours(0, 0, 0, 0);

  const tomorrow = new Date(today);
  tomorrow.setDate(tomorrow.getDate() + 1);

  const todayAppointments = appointments.filter(appt => {
    const apptDate = new Date(appt.data_hora);
    return apptDate >= today && apptDate < tomorrow;
  });

  const scheduledToday = todayAppointments.filter(appt => appt.status === "AGENDADO" || appt.status === "EM_ATENDIMENTO");
  
  const upcomingAppointments = scheduledToday.sort(
    (a, b) => new Date(a.data_hora).getTime() - new Date(b.data_hora).getTime()
  ).slice(0, 5); // Take top 5

  const stats = [
    {
      title: "Consultas Hoje",
      value: todayAppointments.length,
      icon: CalendarCheck2,
      description: `${scheduledToday.length} restantes`,
      color: "text-blue-600",
      bg: "bg-blue-100",
      darkColor: "dark:text-blue-400",
      darkBg: "dark:bg-blue-900/20"
    },
    {
      title: "Pacientes",
      value: patients.length,
      icon: Users,
      description: "Cadastrados no sistema",
      color: "text-emerald-600",
      bg: "bg-emerald-100",
      darkColor: "dark:text-emerald-400",
      darkBg: "dark:bg-emerald-900/20"
    },
    {
      title: "Profissionais",
      value: professionals.length,
      icon: Stethoscope,
      description: "Equipe ativa",
      color: "text-purple-600",
      bg: "bg-purple-100",
      darkColor: "dark:text-purple-400",
      darkBg: "dark:bg-purple-900/20"
    }
  ];

  const containerVariants = {
    hidden: { opacity: 0, y: 20 },
    visible: {
      opacity: 1,
      y: 0,
      transition: { duration: 0.4, staggerChildren: 0.1 }
    }
  };

  const itemVariants = {
    hidden: { opacity: 0, y: 20 },
    visible: { opacity: 1, y: 0 }
  };

  return (
    <motion.div 
      className="p-6 max-w-7xl mx-auto space-y-8"
      initial="hidden"
      animate="visible"
      variants={containerVariants}
    >
      <div className="flex flex-col gap-2">
        <h1 className="text-3xl font-bold tracking-tight text-foreground">
          Olá, {user?.first_name || "Usuário"} 👋
        </h1>
        <p className="text-muted-foreground">
          Bem-vindo ao seu painel. Aqui está o resumo de hoje.
        </p>
      </div>

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
                  <div className={`p-2 rounded-xl ${stat.bg} ${stat.darkBg}`}>
                    <Icon className={`w-5 h-5 ${stat.color} ${stat.darkColor}`} />
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

      <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-7">
        <motion.div variants={itemVariants} className="lg:col-span-4">
          <Card className="border-none shadow-md bg-card/50 backdrop-blur-sm h-full">
            <CardHeader className="flex flex-row items-center justify-between">
              <div>
                <CardTitle>Próximas Consultas</CardTitle>
                <p className="text-sm text-muted-foreground mt-1">
                  Seus agendamentos para hoje
                </p>
              </div>
              <Button variant="outline" size="sm" asChild>
                <Link to="/agendamentos" className="flex items-center gap-2">
                  Ver todas <ArrowRight className="w-4 h-4" />
                </Link>
              </Button>
            </CardHeader>
            <CardContent>
              {loading ? (
                <div className="space-y-4">
                  {[1, 2, 3].map(i => (
                    <div key={i} className="flex items-center gap-4">
                      <Skeleton className="h-12 w-12 rounded-full" />
                      <div className="space-y-2">
                        <Skeleton className="h-4 w-[200px]" />
                        <Skeleton className="h-3 w-[150px]" />
                      </div>
                    </div>
                  ))}
                </div>
              ) : upcomingAppointments.length > 0 ? (
                <div className="space-y-6">
                  {upcomingAppointments.map((appt) => {
                    const date = new Date(appt.data_hora);
                    return (
                      <div key={appt.id} className="flex items-center justify-between p-3 rounded-lg hover:bg-muted/50 transition-colors">
                        <div className="flex items-center gap-4">
                          <div className="flex flex-col items-center justify-center bg-primary/10 text-primary w-12 h-12 rounded-xl">
                            <span className="text-sm font-bold">
                              {date.toLocaleTimeString("pt-BR", { hour: "2-digit", minute: "2-digit" })}
                            </span>
                          </div>
                          <div>
                            <p className="font-semibold">{appt.paciente_nome}</p>
                            <p className="text-sm text-muted-foreground flex items-center gap-1">
                              <UserRound className="w-3 h-3" />
                              {appt.profissional_nome}
                            </p>
                          </div>
                        </div>
                        <div className="flex items-center">
                           <span className="px-2.5 py-1 text-xs font-medium bg-blue-100 text-blue-800 dark:bg-blue-900/30 dark:text-blue-300 rounded-full">
                            {appt.status}
                          </span>
                        </div>
                      </div>
                    );
                  })}
                </div>
              ) : (
                <div className="flex flex-col items-center justify-center py-12 text-center text-muted-foreground">
                  <div className="bg-muted p-4 rounded-full mb-4">
                    <Calendar className="w-8 h-8 opacity-50" />
                  </div>
                  <p className="font-medium text-foreground">Nenhuma consulta pendente</p>
                  <p className="text-sm mt-1">Você não tem mais consultas agendadas para hoje.</p>
                </div>
              )}
            </CardContent>
          </Card>
        </motion.div>

        <motion.div variants={itemVariants} className="lg:col-span-3">
          <Card className="border-none shadow-md bg-primary text-primary-foreground overflow-hidden relative h-full">
            <div className="absolute top-0 right-0 p-8 opacity-10">
              <Activity className="w-48 h-48" />
            </div>
            <CardHeader>
              <CardTitle className="text-2xl">Gestão Eficiente</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4 relative z-10">
              <p className="text-primary-foreground/90 leading-relaxed">
                Mantenha sua clínica organizada e ofereça o melhor atendimento aos seus pacientes. 
                Acesse facilmente prontuários, agendamentos e cadastros.
              </p>
              
              <div className="pt-4 grid grid-cols-2 gap-4">
                 <Button variant="secondary" className="w-full" asChild>
                    <Link to="/pacientes">Novo Paciente</Link>
                 </Button>
                 <Button variant="secondary" className="w-full bg-primary-foreground/20 hover:bg-primary-foreground/30 text-primary-foreground border-none" asChild>
                    <Link to="/agendamentos">Agendar</Link>
                 </Button>
              </div>
            </CardContent>
          </Card>
        </motion.div>
      </div>
    </motion.div>
  );
}
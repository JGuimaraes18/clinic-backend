from django.core.management.base import BaseCommand
from django.db import transaction
from django.contrib.auth import get_user_model
from apps.clinics.models import Clinic
from apps.accounts.models import Membership, PasswordResetToken
from apps.patients.models import Patient
from apps.professionals.models import Professional
from apps.appointments.models import Atendimento
from apps.medical_records.models import Prontuario, AdendoProntuario
from apps.audit.models import AuditLog

User = get_user_model()

class Command(BaseCommand):
    help = 'Limpa todos os dados de clínicas e tenants, preservando o SuperAdmin e configurações globais da plataforma.'

    def handle(self, *args, **kwargs):
        self.stdout.write(self.style.WARNING("ATENÇÃO: Este comando apagará TODOS os dados operacionais!"))
        
        # Em produção real poderíamos exigir uma flag extra --force,
        # mas como estamos em desenvolvimento para agilizar:
        
        with transaction.atomic():
            self.stdout.write("Excluindo prontuários e adendos...")
            AdendoProntuario.objects.all().delete()
            Prontuario.objects.all().delete()

            self.stdout.write("Excluindo atendimentos e agendas...")
            Atendimento.objects.all().delete()

            self.stdout.write("Excluindo pacientes...")
            Patient.objects.all().delete()

            self.stdout.write("Excluindo profissionais...")
            Professional.objects.all().delete()

            self.stdout.write("Excluindo tokens e auditoria das clínicas...")
            PasswordResetToken.objects.all().delete()
            AuditLog.objects.filter(clinic__isnull=False).delete()

            self.stdout.write("Excluindo configurações de usuários...")
            from apps.accounts.models import UserSettings
            UserSettings.objects.all().delete()

            self.stdout.write("Excluindo associações e usuários de clínicas...")
            Membership.objects.all().delete()
            
            # Deletar usuários que não são staff/superuser
            User.objects.filter(is_staff=False, is_superuser=False).delete()

            self.stdout.write("Excluindo clínicas...")
            Clinic.objects.all().delete()

            # Garantir que exista um SuperAdmin padrão
            if not User.objects.filter(is_superuser=True).exists():
                self.stdout.write("Nenhum SuperAdmin encontrado. Criando admin@clinify.com...")
                User.objects.create_superuser(
                    email="admin@clinify.com",
                    password="AdminPass123!",
                    first_name="Super",
                    last_name="Admin"
                )
            
            # Semeando dados iniciais
            self.stdout.write("Semeando dados de teste iniciais...")
            test_clinic = Clinic.objects.create(
                name="Clínica Exemplo",
                slug="clinica-exemplo",
                document="12.345.678/0001-90",
                phone="(11) 98765-4321",
                email="contato@clinicaexemplo.com",
                primary_color="#0651ED",
                secondary_color="#4F46E5"
            )
            
            test_admin = User.objects.create_user(
                email="admin@clinicaexemplo.com",
                password="ChangeMe123!",
                first_name="Admin",
                last_name="Exemplo",
                force_password_change=True
            )
            
            Membership.objects.create(
                user=test_admin,
                clinic=test_clinic,
                role="ADMIN"
            )
            
            self.stdout.write(self.style.SUCCESS("Ambiente reiniciado com sucesso! Todos os dados de tenants foram limpos. SuperAdmin preservado."))
            self.stdout.write(self.style.SUCCESS("Dados semeados para testes:"))
            self.stdout.write(self.style.SUCCESS("  - Clínica Exemplo (slug: clinica-exemplo)"))
            self.stdout.write(self.style.SUCCESS("  - Administrador: admin@clinicaexemplo.com / Senha: ChangeMe123!"))

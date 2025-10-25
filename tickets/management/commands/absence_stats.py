from django.core.management.base import BaseCommand
from tickets.models import AbsenceType, EmployeeAbsence
from django.contrib.auth.models import User
from django.utils import timezone
from datetime import timedelta


class Command(BaseCommand):
    help = 'Muestra estadísticas del sistema de ausencias'

    def handle(self, *args, **options):
        self.stdout.write('📊 Estadísticas del Sistema de Ausencias\n')

        # Estadísticas generales
        total_types = AbsenceType.objects.count()
        total_absences = EmployeeAbsence.objects.count()
        total_employees = User.objects.filter(is_active=True).count()

        self.stdout.write(f'📋 Resumen General:')
        self.stdout.write(f'   • Tipos de ausencias disponibles: {total_types}')
        self.stdout.write(f'   • Total de ausencias registradas: {total_absences}')
        self.stdout.write(f'   • Empleados activos: {total_employees}\n')

        # Estadísticas por estado
        pending = EmployeeAbsence.objects.filter(status='pending').count()
        approved = EmployeeAbsence.objects.filter(status='approved').count()
        rejected = EmployeeAbsence.objects.filter(status='rejected').count()

        self.stdout.write(f'📊 Por Estado:')
        self.stdout.write(f'   • Pendientes de aprobación: {pending}')
        self.stdout.write(f'   • Aprobadas: {approved}')
        self.stdout.write(f'   • Rechazadas: {rejected}\n')

        # Ausencias actuales
        today = timezone.now().date()
        current_absences = EmployeeAbsence.objects.filter(
            start_date__lte=today,
            end_date__gte=today,
            status='approved'
        )

        self.stdout.write(f'🏠 Ausencias Actuales ({len(current_absences)}):')
        if current_absences.exists():
            for absence in current_absences:
                self.stdout.write(
                    f'   • {absence.employee.get_full_name() or absence.employee.username} - '
                    f'{absence.absence_type.name} '
                    f'({absence.start_date} a {absence.end_date})'
                )
        else:
            self.stdout.write('   • No hay empleados ausentes hoy')
        self.stdout.write('')

        # Próximas ausencias
        future_absences = EmployeeAbsence.objects.filter(
            start_date__gt=today,
            start_date__lte=today + timedelta(days=7),
            status='approved'
        ).order_by('start_date')

        self.stdout.write(f'📅 Próximas Ausencias (7 días):')
        if future_absences.exists():
            for absence in future_absences:
                self.stdout.write(
                    f'   • {absence.start_date}: {absence.employee.get_full_name() or absence.employee.username} - '
                    f'{absence.absence_type.name}'
                )
        else:
            self.stdout.write('   • No hay ausencias programadas para los próximos 7 días')
        self.stdout.write('')

        # Estadísticas por tipo
        self.stdout.write(f'📊 Uso por Tipo de Ausencia:')
        for absence_type in AbsenceType.objects.all():
            count = absence_type.get_usage_count()
            self.stdout.write(
                f'   • {absence_type.name}: {count} uso{"s" if count != 1 else ""}'
            )
        self.stdout.write('')

        # Empleados con más ausencias
        from django.db.models import Count
        top_employees = User.objects.annotate(
            absence_count=Count('absences')
        ).filter(absence_count__gt=0).order_by('-absence_count')[:5]

        self.stdout.write(f'👥 Empleados con Más Ausencias:')
        for employee in top_employees:
            self.stdout.write(
                f'   • {employee.get_full_name() or employee.username}: '
                f'{employee.absence_count} ausencia{"s" if employee.absence_count != 1 else ""}'
            )
        self.stdout.write('')

        # Pendientes de aprobación
        pending_absences = EmployeeAbsence.objects.filter(status='pending').order_by('created_at')
        
        self.stdout.write(f'⏳ Solicitudes Pendientes de Aprobación ({len(pending_absences)}):')
        if pending_absences.exists():
            for absence in pending_absences:
                self.stdout.write(
                    f'   • {absence.employee.get_full_name() or absence.employee.username} - '
                    f'{absence.absence_type.name} '
                    f'({absence.start_date} a {absence.end_date}) '
                    f'- Solicitada: {absence.created_at.strftime("%d/%m/%Y")}'
                )
        else:
            self.stdout.write('   • No hay solicitudes pendientes')

        self.stdout.write('\n' + '='*60)
        self.stdout.write('🔗 Acceso al sistema:')
        self.stdout.write('   • Lista: http://localhost:8001/employee-absences/')
        self.stdout.write('   • Calendario: http://localhost:8001/employee-absences/calendar/')
        self.stdout.write('   • Menú: Empleado > Gestión de Ausencias')
        self.stdout.write('='*60)
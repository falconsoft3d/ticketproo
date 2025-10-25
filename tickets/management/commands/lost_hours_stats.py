from django.core.management.base import BaseCommand
from django.utils import timezone
from tickets.models import EmployeeAbsence, AbsenceType
from django.contrib.auth.models import User
from django.db.models import Sum, Avg, Count
from datetime import datetime, timedelta


class Command(BaseCommand):
    help = 'Muestra estadísticas de horas perdidas por ausencias'

    def add_arguments(self, parser):
        parser.add_argument(
            '--year',
            type=int,
            default=timezone.now().year,
            help='Año para las estadísticas (default: año actual)'
        )
        parser.add_argument(
            '--month',
            type=int,
            help='Mes específico (1-12, opcional)'
        )
        parser.add_argument(
            '--employee',
            type=str,
            help='Username del empleado específico (opcional)'
        )

    def handle(self, *args, **options):
        year = options['year']
        month = options.get('month')
        employee_username = options.get('employee')
        
        self.stdout.write(
            self.style.SUCCESS(f'\n📊 ESTADÍSTICAS DE HORAS PERDIDAS - {year}')
        )
        
        # Filtro base
        absences = EmployeeAbsence.objects.filter(
            start_date__year=year,
            status='approved'  # Solo ausencias aprobadas
        )
        
        # Filtro por mes si se especifica
        if month:
            absences = absences.filter(start_date__month=month)
            period = f"{self.get_month_name(month)} {year}"
        else:
            period = str(year)
        
        # Filtro por empleado si se especifica
        if employee_username:
            try:
                employee = User.objects.get(username=employee_username)
                absences = absences.filter(employee=employee)
                period += f" - {employee.get_full_name() or employee.username}"
            except User.DoesNotExist:
                self.stdout.write(
                    self.style.ERROR(f'❌ Empleado "{employee_username}" no encontrado')
                )
                return
        
        self.stdout.write(f'🗓️  Período: {period}\n')
        
        if not absences.exists():
            self.stdout.write(
                self.style.WARNING('⚠️  No se encontraron ausencias aprobadas para el período especificado')
            )
            return
        
        # Estadísticas generales
        total_absences = absences.count()
        total_days = sum(absence.get_duration_days() for absence in absences)
        total_hours = absences.aggregate(Sum('lost_hours'))['lost_hours__sum'] or 0
        avg_hours_per_absence = total_hours / total_absences if total_absences > 0 else 0
        
        self.stdout.write('📈 RESUMEN GENERAL:')
        self.stdout.write(f'   • Total de ausencias: {total_absences}')
        self.stdout.write(f'   • Total de días: {total_days}')
        self.stdout.write(f'   • Total de horas perdidas: {total_hours:.1f}')
        self.stdout.write(f'   • Promedio horas por ausencia: {avg_hours_per_absence:.1f}')
        
        # Estadísticas por tipo de ausencia
        self.stdout.write('\n📋 POR TIPO DE AUSENCIA:')
        types_stats = absences.values(
            'absence_type__name',
            'absence_type__color'
        ).annotate(
            count=Count('id'),
            total_hours=Sum('lost_hours'),
            avg_hours=Avg('lost_hours')
        ).order_by('-total_hours')
        
        for stat in types_stats:
            self.stdout.write(
                f'   • {stat["absence_type__name"]}: '
                f'{stat["count"]} ausencias, '
                f'{stat["total_hours"]:.1f} horas '
                f'(promedio: {stat["avg_hours"]:.1f}h)'
            )
        
        # Estadísticas por empleado (solo si no se filtró por empleado específico)
        if not employee_username and total_absences > 1:
            self.stdout.write('\n👥 POR EMPLEADO:')
            employee_stats = absences.values(
                'employee__username',
                'employee__first_name',
                'employee__last_name'
            ).annotate(
                count=Count('id'),
                total_hours=Sum('lost_hours'),
                avg_hours=Avg('lost_hours')
            ).order_by('-total_hours')[:10]  # Top 10
            
            for i, stat in enumerate(employee_stats, 1):
                full_name = f"{stat['employee__first_name']} {stat['employee__last_name']}".strip()
                name = full_name if full_name else stat['employee__username']
                self.stdout.write(
                    f'   {i:2d}. {name} ({stat["employee__username"]}): '
                    f'{stat["count"]} ausencias, '
                    f'{stat["total_hours"]:.1f} horas '
                    f'(promedio: {stat["avg_hours"]:.1f}h)'
                )
        
        # Estadísticas mensuales (solo si no se filtró por mes específico)
        if not month:
            self.stdout.write('\n📅 POR MES:')
            monthly_stats = absences.extra(
                select={'month': "strftime('%%m', start_date)"}
            ).values('month').annotate(
                count=Count('id'),
                total_hours=Sum('lost_hours')
            ).order_by('month')
            
            for stat in monthly_stats:
                month_name = self.get_month_name(int(stat['month']))
                self.stdout.write(
                    f'   • {month_name}: '
                    f'{stat["count"]} ausencias, '
                    f'{stat["total_hours"]:.1f} horas'
                )
        
        # Análisis de impacto
        self.stdout.write('\n💼 ANÁLISIS DE IMPACTO:')
        if total_hours > 0:
            # Suponiendo 8 horas laborales por día, 22 días laborales por mes
            lost_days_equivalent = total_hours / 8
            lost_months_equivalent = lost_days_equivalent / 22
            
            self.stdout.write(f'   • Equivalente a {lost_days_equivalent:.1f} días laborales completos')
            if lost_months_equivalent >= 1:
                self.stdout.write(f'   • Equivalente a {lost_months_equivalent:.1f} meses de trabajo')
            
            # Costo estimado (ejemplo con salario promedio)
            estimated_hourly_rate = 15000  # CLP por hora (ajustar según país/empresa)
            estimated_cost = total_hours * estimated_hourly_rate
            self.stdout.write(f'   • Costo estimado: ${estimated_cost:,.0f} CLP')
        
        self.stdout.write('\n✅ Análisis completado\n')
    
    def get_month_name(self, month_num):
        months = {
            1: 'Enero', 2: 'Febrero', 3: 'Marzo', 4: 'Abril',
            5: 'Mayo', 6: 'Junio', 7: 'Julio', 8: 'Agosto',
            9: 'Septiembre', 10: 'Octubre', 11: 'Noviembre', 12: 'Diciembre'
        }
        return months.get(month_num, f'Mes {month_num}')
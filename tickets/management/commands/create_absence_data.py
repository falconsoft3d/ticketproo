from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from tickets.models import AbsenceType, EmployeeAbsence
from datetime import datetime, timedelta
from django.utils import timezone


class Command(BaseCommand):
    help = 'Crea datos de prueba para el sistema de ausencias de empleados'

    def handle(self, *args, **options):
        self.stdout.write('🏢 Creando datos de prueba para el sistema de ausencias...\n')

        # Crear tipos de ausencias
        absence_types_data = [
            {
                'name': 'Vacaciones',
                'description': 'Días de vacaciones anuales del empleado',
                'requires_documentation': False,
                'is_paid': True,
                'max_days_per_year': 30,
                'color': '#28a745'  # Verde
            },
            {
                'name': 'Enfermedad',
                'description': 'Ausencia por enfermedad o problemas de salud',
                'requires_documentation': True,
                'is_paid': True,
                'max_days_per_year': None,
                'color': '#dc3545'  # Rojo
            },
            {
                'name': 'Permiso Personal',
                'description': 'Permiso por asuntos personales o familiares',
                'requires_documentation': False,
                'is_paid': True,
                'max_days_per_year': 5,
                'color': '#ffc107'  # Amarillo
            },
            {
                'name': 'Licencia por Maternidad/Paternidad',
                'description': 'Licencia por nacimiento o adopción de hijo',
                'requires_documentation': True,
                'is_paid': True,
                'max_days_per_year': None,
                'color': '#e83e8c'  # Rosa
            },
            {
                'name': 'Capacitación',
                'description': 'Ausencia por cursos, seminarios o capacitaciones',
                'requires_documentation': False,
                'is_paid': True,
                'max_days_per_year': 10,
                'color': '#6f42c1'  # Púrpura
            },
            {
                'name': 'Duelo',
                'description': 'Ausencia por fallecimiento de familiar',
                'requires_documentation': True,
                'is_paid': True,
                'max_days_per_year': 5,
                'color': '#6c757d'  # Gris
            },
            {
                'name': 'Sin Goce de Sueldo',
                'description': 'Permiso especial sin remuneración',
                'requires_documentation': False,
                'is_paid': False,
                'max_days_per_year': None,
                'color': '#fd7e14'  # Naranja
            }
        ]

        created_types = 0
        for type_data in absence_types_data:
            absence_type, created = AbsenceType.objects.get_or_create(
                name=type_data['name'],
                defaults=type_data
            )
            
            if created:
                created_types += 1
                self.stdout.write(
                    self.style.SUCCESS(f'✓ Creado tipo: {absence_type.name}')
                )
            else:
                self.stdout.write(
                    self.style.WARNING(f'- Ya existe tipo: {absence_type.name}')
                )

        # Obtener usuarios para crear ausencias de ejemplo
        users = User.objects.filter(is_active=True)[:5]  # Solo primeros 5 usuarios
        
        if not users.exists():
            self.stdout.write(
                self.style.ERROR('No hay usuarios en el sistema. Crea algunos usuarios primero.')
            )
            return

        # Crear ausencias de ejemplo
        absence_examples = []
        today = timezone.now().date()
        
        # Obtener tipos creados
        vacation_type = AbsenceType.objects.get(name='Vacaciones')
        sick_type = AbsenceType.objects.get(name='Enfermedad')
        personal_type = AbsenceType.objects.get(name='Permiso Personal')
        training_type = AbsenceType.objects.get(name='Capacitación')

        for i, user in enumerate(users):
            # Ausencia pasada (vacaciones)
            absence_examples.append({
                'employee': user,
                'absence_type': vacation_type,
                'start_date': today - timedelta(days=20 - i*2),
                'end_date': today - timedelta(days=15 - i*2),
                'reason': f'Vacaciones familiares planificadas. Viaje de descanso con la familia.',
                'status': 'approved'
            })
            
            # Ausencia futura (capacitación)
            if i < 3:  # Solo para algunos usuarios
                absence_examples.append({
                    'employee': user,
                    'absence_type': training_type,
                    'start_date': today + timedelta(days=10 + i*3),
                    'end_date': today + timedelta(days=12 + i*3),
                    'reason': f'Asistencia a seminario de capacitación técnica en nuevas tecnologías.',
                    'status': 'pending'
                })
            
            # Ausencia de enfermedad (reciente)
            if i == 0:  # Solo para el primer usuario
                absence_examples.append({
                    'employee': user,
                    'absence_type': sick_type,
                    'start_date': today - timedelta(days=5),
                    'end_date': today - timedelta(days=3),
                    'reason': 'Gripe estacional con fiebre. Certificado médico adjunto.',
                    'status': 'approved'
                })
            
            # Permiso personal pendiente
            if i == 1:  # Solo para el segundo usuario
                absence_examples.append({
                    'employee': user,
                    'absence_type': personal_type,
                    'start_date': today + timedelta(days=7),
                    'end_date': today + timedelta(days=7),  # Un solo día
                    'reason': 'Trámites bancarios y documentación personal que requieren presencia en horario laboral.',
                    'status': 'pending'
                })

        created_absences = 0
        for absence_data in absence_examples:
            # Verificar si ya existe una ausencia similar
            existing = EmployeeAbsence.objects.filter(
                employee=absence_data['employee'],
                absence_type=absence_data['absence_type'],
                start_date=absence_data['start_date']
            ).first()
            
            if not existing:
                absence = EmployeeAbsence.objects.create(**absence_data)
                created_absences += 1
                
                # Aprobar automáticamente las ausencias marcadas como aprobadas
                if absence_data['status'] == 'approved':
                    absence.approve(absence_data['employee'])  # Usar el mismo usuario como aprobador
                
                self.stdout.write(
                    self.style.SUCCESS(
                        f'✓ Creada ausencia: {absence.employee.username} - {absence.absence_type.name} '
                        f'({absence.start_date} a {absence.end_date})'
                    )
                )
            else:
                self.stdout.write(
                    self.style.WARNING(
                        f'- Ya existe ausencia similar para {absence_data["employee"].username}'
                    )
                )

        self.stdout.write(
            self.style.SUCCESS(f'\n🎉 Proceso completado!')
        )
        self.stdout.write(
            self.style.SUCCESS(f'📊 Estadísticas:')
        )
        self.stdout.write(
            self.style.SUCCESS(f'   • Tipos de ausencias creados: {created_types}')
        )
        self.stdout.write(
            self.style.SUCCESS(f'   • Ausencias de ejemplo creadas: {created_absences}')
        )
        self.stdout.write(
            self.style.SUCCESS(f'   • Total usuarios con ausencias: {len(users)}')
        )
        self.stdout.write(
            self.style.SUCCESS('\n🔗 Accede al sistema desde el menú: Empleado > Gestión de Ausencias')
        )
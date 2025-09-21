from django.core.management.base import BaseCommand
from tickets.models import Category


class Command(BaseCommand):
    help = 'Crea categorías de ejemplo para el sistema de tickets'

    def handle(self, *args, **options):
        categories = [
            {
                'name': 'Soporte Técnico',
                'description': 'Problemas técnicos, errores de software, configuración de sistemas',
                'color': '#dc3545',  # Rojo
            },
            {
                'name': 'Consultas Generales',
                'description': 'Preguntas generales, información sobre productos y servicios',
                'color': '#0dcaf0',  # Cyan
            },
            {
                'name': 'Solicitudes de Mejora',
                'description': 'Sugerencias de mejoras, nuevas funcionalidades',
                'color': '#198754',  # Verde
            },
            {
                'name': 'Problemas de Facturación',
                'description': 'Consultas sobre facturas, pagos, precios',
                'color': '#fd7e14',  # Naranja
            },
            {
                'name': 'Reportes de Bugs',
                'description': 'Errores de software, fallos del sistema',
                'color': '#6f42c1',  # Púrpura
            },
            {
                'name': 'Acceso y Permisos',
                'description': 'Problemas de acceso, permisos de usuario, credenciales',
                'color': '#6c757d',  # Gris
            },
        ]

        created_count = 0
        for category_data in categories:
            category, created = Category.objects.get_or_create(
                name=category_data['name'],
                defaults={
                    'description': category_data['description'],
                    'color': category_data['color'],
                    'is_active': True,
                }
            )
            if created:
                created_count += 1
                self.stdout.write(
                    self.style.SUCCESS(
                        f'✓ Categoría "{category.name}" creada exitosamente'
                    )
                )
            else:
                self.stdout.write(
                    self.style.WARNING(
                        f'⚠ Categoría "{category.name}" ya existe'
                    )
                )

        if created_count > 0:
            self.stdout.write(
                self.style.SUCCESS(
                    f'\n🎉 Se crearon {created_count} categorías nuevas'
                )
            )
        else:
            self.stdout.write(
                self.style.WARNING(
                    '\n✅ Todas las categorías ya existían en el sistema'
                )
            )
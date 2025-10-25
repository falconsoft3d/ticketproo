from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta
from tickets.models import License


class Command(BaseCommand):
    help = 'Reporta licencias próximas a vencer'

    def add_arguments(self, parser):
        parser.add_argument(
            '--days',
            type=int,
            default=30,
            help='Días de anticipación para el reporte (default: 30)'
        )
        parser.add_argument(
            '--format',
            choices=['table', 'csv', 'json'],
            default='table',
            help='Formato del reporte (default: table)'
        )

    def handle(self, *args, **options):
        days_ahead = options['days']
        output_format = options['format']
        
        # Calcular fecha límite
        end_date = timezone.now().date() + timedelta(days=days_ahead)
        
        # Obtener licencias próximas a vencer
        expiring_licenses = License.objects.filter(
            end_date__lte=end_date,
            end_date__gte=timezone.now().date(),
            status='active'
        ).order_by('end_date')
        
        if not expiring_licenses.exists():
            self.stdout.write(
                self.style.SUCCESS(
                    f'No hay licencias que venzan en los próximos {days_ahead} días.'
                )
            )
            return
        
        self.stdout.write(
            self.style.WARNING(
                f'Encontradas {expiring_licenses.count()} licencias que vencen en los próximos {days_ahead} días:'
            )
        )
        
        if output_format == 'table':
            self._output_table(expiring_licenses)
        elif output_format == 'csv':
            self._output_csv(expiring_licenses)
        elif output_format == 'json':
            self._output_json(expiring_licenses)

    def _output_table(self, licenses):
        # Header
        self.stdout.write('-' * 100)
        self.stdout.write(
            f"{'Clave':<15} {'Empresa':<25} {'Producto':<25} {'Vencimiento':<12} {'Días':<5}"
        )
        self.stdout.write('-' * 100)
        
        # Rows
        for license in licenses:
            days_left = license.days_until_expiry()
            color = self.style.ERROR if days_left <= 7 else self.style.WARNING
            
            self.stdout.write(
                color(
                    f"{license.license_key:<15} "
                    f"{license.company.name[:24]:<25} "
                    f"{license.product[:24]:<25} "
                    f"{license.end_date.strftime('%d/%m/%Y'):<12} "
                    f"{days_left:<5}"
                )
            )
        
        self.stdout.write('-' * 100)

    def _output_csv(self, licenses):
        import csv
        import sys
        
        writer = csv.writer(sys.stdout)
        writer.writerow(['Clave', 'Empresa', 'Producto', 'Vencimiento', 'Días Restantes'])
        
        for license in licenses:
            writer.writerow([
                license.license_key,
                license.company.name,
                license.product,
                license.end_date.strftime('%d/%m/%Y'),
                license.days_until_expiry()
            ])

    def _output_json(self, licenses):
        import json
        
        data = []
        for license in licenses:
            data.append({
                'license_key': license.license_key,
                'company': license.company.name,
                'product': license.product,
                'end_date': license.end_date.strftime('%Y-%m-%d'),
                'days_until_expiry': license.days_until_expiry(),
                'public_url': license.get_qr_data()
            })
        
        self.stdout.write(json.dumps(data, indent=2))
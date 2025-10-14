from django.core.management.base import BaseCommand
from django.utils import timezone
from tickets.models import FinancialAction
from decimal import Decimal


class Command(BaseCommand):
    help = 'Crear datos de ejemplo para acciones financieras'

    def add_arguments(self, parser):
        parser.add_argument(
            '--reset',
            action='store_true',
            help='Eliminar todas las acciones existentes antes de crear nuevas',
        )

    def handle(self, *args, **options):
        if options['reset']:
            FinancialAction.objects.all().delete()
            self.stdout.write(
                self.style.WARNING('Todas las acciones financieras han sido eliminadas.')
            )

        # Datos de ejemplo
        sample_actions = [
            {
                'symbol': 'EUR/USD',
                'name': 'Euro / Dólar Estadounidense',
                'current_price': Decimal('1.0856'),
                'previous_price': Decimal('1.0820'),
                'currency': 'USD',
                'order': 1,
            },
            {
                'symbol': 'GBP/USD',
                'name': 'Libra Esterlina / Dólar Estadounidense',
                'current_price': Decimal('1.2735'),
                'previous_price': Decimal('1.2698'),
                'currency': 'USD',
                'order': 2,
            },
            {
                'symbol': 'AAPL',
                'name': 'Apple Inc.',
                'current_price': Decimal('178.25'),
                'previous_price': Decimal('176.80'),
                'currency': 'USD',
                'order': 3,
            },
            {
                'symbol': 'GOOGL',
                'name': 'Alphabet Inc. (Google)',
                'current_price': Decimal('138.92'),
                'previous_price': Decimal('140.15'),
                'currency': 'USD',
                'order': 4,
            },
            {
                'symbol': 'MSFT',
                'name': 'Microsoft Corporation',
                'current_price': Decimal('420.55'),
                'previous_price': Decimal('418.20'),
                'currency': 'USD',
                'order': 5,
            },
            {
                'symbol': 'TSLA',
                'name': 'Tesla Inc.',
                'current_price': Decimal('242.65'),
                'previous_price': Decimal('248.10'),
                'currency': 'USD',
                'order': 6,
            },
            {
                'symbol': 'BTC/USD',
                'name': 'Bitcoin / Dólar Estadounidense',
                'current_price': Decimal('68250.75'),
                'previous_price': Decimal('67890.20'),
                'currency': 'USD',
                'order': 7,
            },
        ]

        created_count = 0
        updated_count = 0

        for action_data in sample_actions:
            action, created = FinancialAction.objects.get_or_create(
                symbol=action_data['symbol'],
                defaults=action_data
            )
            
            if created:
                created_count += 1
                self.stdout.write(
                    self.style.SUCCESS(f'✓ Creada: {action.symbol} - {action.name}')
                )
            else:
                # Actualizar datos existentes
                for key, value in action_data.items():
                    if key != 'symbol':  # No actualizar el símbolo que es la clave
                        setattr(action, key, value)
                action.save()
                updated_count += 1
                self.stdout.write(
                    self.style.WARNING(f'↻ Actualizada: {action.symbol} - {action.name}')
                )

        self.stdout.write('\n' + '='*50)
        self.stdout.write(
            self.style.SUCCESS(
                f'Proceso completado:\n'
                f'• {created_count} acciones creadas\n'
                f'• {updated_count} acciones actualizadas\n'
                f'• Total: {FinancialAction.objects.count()} acciones en el sistema'
            )
        )
        self.stdout.write('='*50)
        
        # Mostrar resumen
        active_actions = FinancialAction.objects.filter(is_active=True).count()
        self.stdout.write(
            self.style.SUCCESS(
                f'\n📊 Acciones activas en el ticker: {active_actions}'
            )
        )
        
        if active_actions > 0:
            self.stdout.write(
                self.style.SUCCESS(
                    '\n✅ El ticker del dashboard mostrará estas acciones automáticamente.'
                )
            )
        else:
            self.stdout.write(
                self.style.WARNING(
                    '\n⚠️  No hay acciones activas. Vaya a /financial-actions/ para activarlas.'
                )
            )
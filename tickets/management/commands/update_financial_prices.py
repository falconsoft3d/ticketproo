"""
Comando de Django para actualizar precios de acciones financieras
"""
from django.core.management.base import BaseCommand
from django.utils import timezone
from tickets.financial_api import update_all_financial_prices
import logging

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Actualiza los precios de todas las acciones financieras activas'

    def add_arguments(self, parser):
        parser.add_argument(
            '--symbol',
            type=str,
            help='Actualizar solo un símbolo específico',
        )
        parser.add_argument(
            '--force',
            action='store_true',
            help='Forzar actualización incluso si fue actualizado recientemente',
        )

    def handle(self, *args, **options):
        self.stdout.write(
            self.style.SUCCESS(f'[{timezone.now()}] Iniciando actualización de precios financieros...')
        )

        try:
            if options['symbol']:
                # Actualizar solo un símbolo específico
                from tickets.models import FinancialAction
                from tickets.financial_api import FinancialDataAPI
                
                try:
                    action = FinancialAction.objects.get(symbol=options['symbol'])
                    api = FinancialDataAPI()
                    
                    if api.update_price(action):
                        self.stdout.write(
                            self.style.SUCCESS(
                                f'✅ Precio actualizado: {action.symbol} = {action.current_price} {action.currency}'
                            )
                        )
                    else:
                        self.stdout.write(
                            self.style.ERROR(f'❌ No se pudo actualizar el precio de {action.symbol}')
                        )
                        
                except FinancialAction.DoesNotExist:
                    self.stdout.write(
                        self.style.ERROR(f'❌ No se encontró la acción con símbolo: {options["symbol"]}')
                    )
                    return
            else:
                # Actualizar todos los precios
                updated_count = update_all_financial_prices()
                
                self.stdout.write(
                    self.style.SUCCESS(
                        f'✅ Actualización completada: {updated_count} precios actualizados'
                    )
                )

        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'❌ Error durante la actualización: {str(e)}')
            )
            logger.error(f"Error en comando update_financial_prices: {e}")

        self.stdout.write(
            self.style.SUCCESS(f'[{timezone.now()}] Finalizada actualización de precios financieros')
        )
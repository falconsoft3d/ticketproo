from django.core.management.base import BaseCommand
from django.db import transaction
from django.db import models
from tickets.models import Ticket


class Command(BaseCommand):
    help = 'Genera números de ticket para tickets existentes que no los tengan'

    def handle(self, *args, **options):
        # Buscar tickets sin número asignado
        tickets_without_number = Ticket.objects.filter(ticket_number__in=['', None]).order_by('created_by', 'created_at')
        
        if not tickets_without_number.exists():
            self.stdout.write(
                self.style.SUCCESS('✅ Todos los tickets ya tienen números asignados')
            )
            return

        updated_count = 0
        error_count = 0

        # Agrupar tickets por usuario para generar secuencias ordenadas
        users_tickets = {}
        for ticket in tickets_without_number:
            user_id = ticket.created_by.id
            if user_id not in users_tickets:
                users_tickets[user_id] = []
            users_tickets[user_id].append(ticket)

        # Procesar tickets por usuario
        for user_id, user_tickets in users_tickets.items():
            self.stdout.write(f'📝 Procesando {len(user_tickets)} tickets del usuario ID {user_id}...')
            
            # Ordenar por fecha de creación para mantener secuencia cronológica
            user_tickets.sort(key=lambda t: t.created_at)
            
            for ticket in user_tickets:
                try:
                    with transaction.atomic():
                        # Generar número de ticket
                        old_number = ticket.ticket_number
                        ticket.save()  # Esto activará la generación automática del número
                        
                        if ticket.ticket_number != old_number:
                            updated_count += 1
                            self.stdout.write(
                                f'  ✓ Ticket #{ticket.id}: {old_number or "sin número"} → {ticket.ticket_number}'
                            )
                        else:
                            self.stdout.write(
                                f'  ⚠ Ticket #{ticket.id}: No se pudo generar número'
                            )
                            error_count += 1
                            
                except Exception as e:
                    error_count += 1
                    self.stdout.write(
                        self.style.ERROR(
                            f'  ❌ Error en ticket #{ticket.id}: {str(e)}'
                        )
                    )

        # Resumen final
        self.stdout.write('\n' + '='*50)
        self.stdout.write(
            self.style.SUCCESS(
                f'🎉 Proceso completado: {updated_count} tickets actualizados'
            )
        )
        
        if error_count > 0:
            self.stdout.write(
                self.style.WARNING(
                    f'⚠ {error_count} tickets tuvieron errores'
                )
            )
        
        # Verificar duplicados
        duplicates = Ticket.objects.exclude(ticket_number__in=['', None]).values('ticket_number').annotate(
            count=models.Count('ticket_number')
        ).filter(count__gt=1)
        
        if duplicates.exists():
            self.stdout.write(
                self.style.ERROR(
                    f'❌ Se encontraron {len(duplicates)} números duplicados'
                )
            )
            for dup in duplicates:
                self.stdout.write(f'  - {dup["ticket_number"]}: {dup["count"]} tickets')
        else:
            self.stdout.write(
                self.style.SUCCESS('✅ No se encontraron números duplicados')
            )
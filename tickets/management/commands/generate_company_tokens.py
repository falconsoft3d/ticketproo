from django.core.management.base import BaseCommand
from tickets.models import Company
import uuid


class Command(BaseCommand):
    help = 'Genera tokens públicos para empresas que no los tengan'

    def handle(self, *args, **options):
        companies_updated = 0
        
        for company in Company.objects.filter(public_token__isnull=True):
            company.public_token = uuid.uuid4()
            company.save()
            companies_updated += 1
            self.stdout.write(
                self.style.SUCCESS(f'Token generado para: {company.name} - {company.public_token}')
            )
        
        if companies_updated == 0:
            self.stdout.write(
                self.style.WARNING('Todas las empresas ya tienen token público.')
            )
        else:
            self.stdout.write(
                self.style.SUCCESS(f'Total empresas actualizadas: {companies_updated}')
            )
import logging
from django.core.management.base import BaseCommand
from django.db import transaction
from django_backend.apps.core.models import WindTurbine

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Populates the database with a list of common wind turbine models.'

    TURBINE_DATA = [
        {
            'name': 'Vestas V150-4.2 MW',
            'hub_height': 125,
            'rotor_diameter': 150.0,
            'nominal_power': 4200000,
        },
        {
            'name': 'Siemens Gamesa SG 5.0-145',
            'hub_height': 107.5,
            'rotor_diameter': 145.0,
            'nominal_power': 5000000,
        },
        {
            'name': 'GE 3.6-137',
            'hub_height': 131.4,
            'rotor_diameter': 137.0,
            'nominal_power': 3600000,
        },
        {
            'name': 'GE 3.8-130',
            'hub_height': 85.0,
            'rotor_diameter': 130.0,
            'nominal_power': 3800000,
        },
        {
            'name': 'Vestas V162-6.2 MW',
            'hub_height': 119,
            'rotor_diameter': 162.0,
            'nominal_power': 6200000,
        },
    ]

    @transaction.atomic
    def handle(self, *args, **options):
        self.stdout.write('Starting to populate wind turbines...')
        for turbine_data in self.TURBINE_DATA:
            turbine, created = WindTurbine.objects.get_or_create(
                name=turbine_data['name'],
                defaults=turbine_data
            )
            if created:
                self.stdout.write(self.style.SUCCESS(f'Successfully created {turbine.name}'))
            else:
                self.stdout.write(self.style.WARNING(f'{turbine.name} already exists. Skipping.'))
        self.stdout.write(self.style.SUCCESS('Finished populating wind turbines.'))

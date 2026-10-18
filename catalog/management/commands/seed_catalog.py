from django.core.management.base import BaseCommand

from catalog.seed import seed_catalog
from catalog.services.sync import sync_catalog_content


class Command(BaseCommand):
    help = 'Create default dance pricing tiers and 15 physiotherapy chapters, then map live videos.'

    def handle(self, *args, **options):
        seed_catalog(stdout=self.stdout)
        sync_catalog_content(stdout=self.stdout)
        self.stdout.write(self.style.SUCCESS('Catalog seed complete.'))

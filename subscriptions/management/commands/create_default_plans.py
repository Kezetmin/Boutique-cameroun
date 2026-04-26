from django.core.management.base import BaseCommand
from subscriptions.models import Plan


class Command(BaseCommand):
    help = 'Crée les plans Basic et Pro par défaut'

    def handle(self, *args, **options):
        basic, created = Plan.objects.get_or_create(
            name=Plan.BASIC,
            defaults={
                'monthly_price': 5000,
                'description': 'Pack simple pour petites boutiques.',
                'max_products': 50,
                'max_users': 1,
                'can_view_advanced_reports': False,
                'can_manage_customer_credits': False,
            }
        )

        pro, created = Plan.objects.get_or_create(
            name=Plan.PRO,
            defaults={
                'monthly_price': 10000,
                'description': 'Pack avancé pour boutiques plus actives.',
                'max_products': 500,
                'max_users': 3,
                'can_view_advanced_reports': True,
                'can_manage_customer_credits': True,
            }
        )

        self.stdout.write(self.style.SUCCESS('Plans Basic et Pro créés avec succès.'))
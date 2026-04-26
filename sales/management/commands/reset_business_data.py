from django.core.management.base import BaseCommand
from django.db import transaction

from sales.models import Sale
from products.models import StockMovement


class Command(BaseCommand):
    help = "Supprime les anciennes données métier de test : ventes, lignes de vente et mouvements de stock."

    def add_arguments(self, parser):
        parser.add_argument(
            "--with-stock-movements",
            action="store_true",
            help="Supprime aussi l'historique des mouvements de stock."
        )

    def handle(self, *args, **options):
        with transaction.atomic():
            sales_count = Sale.objects.count()

            # Supprime automatiquement les SaleItem grâce au CASCADE
            Sale.objects.all().delete()

            self.stdout.write(
                self.style.SUCCESS(
                    f"{sales_count} vente(s) supprimée(s). Les lignes de vente liées ont aussi été supprimées."
                )
            )

            if options["with_stock_movements"]:
                movements_count = StockMovement.objects.count()
                StockMovement.objects.all().delete()

                self.stdout.write(
                    self.style.SUCCESS(
                        f"{movements_count} mouvement(s) de stock supprimé(s)."
                    )
                )

        self.stdout.write(
            self.style.WARNING(
                "Utilisateurs, boutiques, produits, catégories et abonnements conservés."
            )
        )
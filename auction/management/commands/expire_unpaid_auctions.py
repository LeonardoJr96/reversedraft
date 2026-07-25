from django.core.management.base import BaseCommand
from auction.services import expire_unpaid_auctions


class Command(BaseCommand):
    help = "Marca como expirados os leilões com pagamento vencido."

    def handle(self, *args, **options):
        expire_unpaid_auctions()
        self.stdout.write(self.style.SUCCESS("Leilões vencidos marcados como expirados."))
import random
from datetime import date, timedelta
from decimal import Decimal

from django.contrib.auth.models import User
from django.core.management.base import BaseCommand

from metas.models import MetaEmpresa, MetaMensal, Venda, Vendedor

# nome, cargo, meta mensal, meta diária, fator de desempenho
DADOS = [("João Silva", "Vendedor", 20000, 1000, 1.15), ("Maria Souza", "Vendedora Sênior", 50000, 2500, 0.95),
         ("Carlos Lima", "Vendedor", 15000, 750, 1.30), ("Ana Costa", "Vendedora", 30000, 1500, 0.70),
         ("Pedro Rocha", "Vendedor", 25000, 1200, 0.85)]


class Command(BaseCommand):
    help = "Cria dados de teste (vendedores, metas e vendas)."

    def handle(self, *args, **opts):
        random.seed(7)
        hoje = date.today()
        meses = {(2026, 8), (2026, 9), (hoje.year, hoje.month)}
        for i, (nome, cargo, mm, md, fator) in enumerate(DADOS):
            v, _ = Vendedor.objects.get_or_create(nome=nome, defaults={
                "cargo": cargo, "email": f"{nome.split()[0].lower()}@empresa.com", "telefone": f"(85) 9000{i}-000{i}"})
            for ano, mes in meses:
                MetaMensal.objects.get_or_create(vendedor=v, ano=ano, mes=mes,
                                                 defaults={"valor_meta_mensal": mm, "valor_meta_diaria": md})
                dia = date(ano, mes, 1)
                while dia.month == mes and dia <= hoje:
                    if dia.weekday() < 6 and not Venda.objects.filter(vendedor=v, data=dia).exists():
                        total = Decimal(md * fator * random.uniform(0.55, 1.45)).quantize(Decimal("0.01"))
                        vista = (total * Decimal(random.uniform(0.6, 0.95))).quantize(Decimal("0.01"))
                        Venda.objects.create(vendedor=v, data=dia, valor_bruto=total, valor_a_vista=vista)
                    dia += timedelta(days=1)
        for ano, mes in meses:
            MetaEmpresa.objects.get_or_create(ano=ano, mes=mes, defaults={"valor_meta": 150000})
        if not User.objects.filter(username="admin").exists():
            User.objects.create_superuser("admin", "admin@empresa.com", "admin123")
            self.stdout.write("Usuário criado: admin / admin123")
        self.stdout.write("Dados de teste criados.")

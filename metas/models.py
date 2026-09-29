from datetime import date
from decimal import Decimal

from django.core.validators import MinValueValidator
from django.db import models

POS = [MinValueValidator(Decimal("0"))]
MESES = list(enumerate(
    ["Janeiro", "Fevereiro", "Março", "Abril", "Maio", "Junho", "Julho",
     "Agosto", "Setembro", "Outubro", "Novembro", "Dezembro"], 1))


def dinheiro(label):
    return models.DecimalField(label, max_digits=12, decimal_places=2, validators=POS)


class Vendedor(models.Model):
    nome = models.CharField(max_length=120)
    email = models.EmailField(blank=True)
    telefone = models.CharField(max_length=20, blank=True)
    cargo = models.CharField(max_length=80, blank=True)
    ativo = models.BooleanField(default=True)
    criado_em = models.DateTimeField("data de cadastro", auto_now_add=True)

    class Meta:
        ordering = ["nome"]
        verbose_name_plural = "vendedores"

    def __str__(self):
        return self.nome


class MetaMensal(models.Model):
    vendedor = models.ForeignKey(Vendedor, on_delete=models.CASCADE, related_name="metas")
    mes = models.PositiveSmallIntegerField(choices=MESES)
    ano = models.PositiveSmallIntegerField()
    valor_meta_mensal = dinheiro("meta mensal")
    valor_meta_diaria = dinheiro("meta diária")
    observacao = models.CharField("observação", max_length=200, blank=True)
    criado_em = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-ano", "-mes", "vendedor__nome"]
        unique_together = ("vendedor", "mes", "ano")
        verbose_name_plural = "metas mensais"

    def __str__(self):
        return f"{self.vendedor} {self.mes:02d}/{self.ano}"


class MetaEmpresa(models.Model):
    mes = models.PositiveSmallIntegerField(choices=MESES)
    ano = models.PositiveSmallIntegerField()
    valor_meta = dinheiro("meta da empresa")

    class Meta:
        ordering = ["-ano", "-mes"]
        unique_together = ("mes", "ano")
        verbose_name_plural = "metas da empresa"

    def __str__(self):
        return f"Empresa {self.mes:02d}/{self.ano}"


class Venda(models.Model):
    vendedor = models.ForeignKey(Vendedor, on_delete=models.CASCADE, related_name="vendas")
    data = models.DateField(default=date.today)
    valor_bruto = dinheiro("valor bruto")
    valor_a_vista = dinheiro("valor à vista")
    observacao = models.CharField("observação", max_length=200, blank=True)
    criado_em = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-data", "-id"]

    def __str__(self):
        return f"{self.vendedor} {self.data:%d/%m/%Y}"

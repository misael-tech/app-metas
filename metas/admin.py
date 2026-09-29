from django.contrib import admin

from .models import MetaEmpresa, MetaMensal, Vendedor, Venda


@admin.register(Vendedor)
class VendedorAdmin(admin.ModelAdmin):
    list_display = ("nome", "cargo", "email", "telefone", "ativo", "criado_em")
    search_fields = ("nome", "email", "cargo")
    list_filter = ("ativo",)
    ordering = ("nome",)


@admin.register(MetaMensal)
class MetaMensalAdmin(admin.ModelAdmin):
    list_display = ("vendedor", "mes", "ano", "valor_meta_mensal", "valor_meta_diaria")
    search_fields = ("vendedor__nome",)
    list_filter = ("ano", "mes", "vendedor")
    ordering = ("-ano", "-mes", "vendedor__nome")


@admin.register(MetaEmpresa)
class MetaEmpresaAdmin(admin.ModelAdmin):
    list_display = ("mes", "ano", "valor_meta")
    list_filter = ("ano", "mes")
    ordering = ("-ano", "-mes")


@admin.register(Venda)
class VendaAdmin(admin.ModelAdmin):
    list_display = ("data", "vendedor", "valor_bruto", "valor_a_vista", "observacao")
    search_fields = ("vendedor__nome", "observacao")
    list_filter = ("vendedor", "data")
    ordering = ("-data",)

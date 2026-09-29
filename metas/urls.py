from django.urls import path

from . import views as v

urlpatterns = [
    path("", v.dashboard, name="dashboard"),
    path("vendedores/", v.vendedores, name="vendedores"),
    path("vendedores/novo/", v.vendedor_form, name="vendedor_novo"),
    path("vendedores/<int:pk>/", v.vendedor_detalhe, name="vendedor_detalhe"),
    path("vendedores/<int:pk>/editar/", v.vendedor_form, name="vendedor_editar"),
    path("vendedores/<int:pk>/ativar/", v.vendedor_toggle, name="vendedor_toggle"),
    path("lancamentos/", v.lancamentos, name="lancamentos"),
    path("lancamentos/nova/", v.venda_form, name="venda_nova"),
    path("lancamentos/<int:pk>/editar/", v.venda_form, name="venda_editar"),
    path("lancamentos/<int:pk>/excluir/", v.venda_excluir, name="venda_excluir"),
    path("metas/", v.metas, name="metas"),
    path("historico/", v.historico, name="historico"),
    path("admin-acesso/", v.admin_acesso, name="admin_acesso"),
    path("relatorios/", v.relatorios, name="relatorios"),
]

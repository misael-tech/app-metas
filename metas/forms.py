from django import forms

from .models import Vendedor, Venda


class VendedorForm(forms.ModelForm):
    meta_mensal = forms.DecimalField(label="Meta mensal (mês atual)", min_value=0,
                                     max_digits=12, decimal_places=2, required=False)
    meta_diaria = forms.DecimalField(label="Meta diária (mês atual)", min_value=0,
                                     max_digits=12, decimal_places=2, required=False)

    class Meta:
        model = Vendedor
        fields = ["nome", "email", "telefone", "cargo", "ativo"]


class VendaForm(forms.ModelForm):
    class Meta:
        model = Venda
        fields = ["vendedor", "data", "valor_bruto", "valor_a_vista", "observacao"]
        widgets = {"data": forms.DateInput(attrs={"type": "date"}, format="%Y-%m-%d")}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["vendedor"].queryset = Vendedor.objects.filter(ativo=True)
        if self.instance.pk:  # permite manter vendedor inativo ao editar
            self.fields["vendedor"].queryset = Vendedor.objects.all()

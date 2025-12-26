from django import forms
from .models import Pedido, ItemPedido

class PedidoForm(forms.ModelForm):
    class Meta:
        model = Pedido
        fields = [
            'orgao',
            'numero_pregao',
            'numero_empenho',
            'data_pedido',
            'status',
        ]
        widgets = {
            'data_pedido': forms.DateInput(attrs={'type': 'date'}),
        }


class ItemPedidoForm(forms.ModelForm):
    class Meta:
        model = ItemPedido
        fields = [
            'descricao',
            'unidade',
            'quantidade',
            'marca',
            'valor_unitario',
        ]

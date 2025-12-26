# pedidos/models.py
from django.db import models
from decimal import Decimal

class Pedido(models.Model):
    STATUS_CHOICES = [
        ('aberto', 'Aberto'),
        ('atendido', 'Atendido'),
        ('cancelado', 'Cancelado'),
    ]

    orgao = models.CharField(max_length=255, verbose_name="Órgão Comprador")
    numero_pregao = models.CharField(max_length=50)
    numero_empenho = models.CharField(max_length=50, blank=True, null=True)
    data_pedido = models.DateField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='aberto')

    criado_em = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['data_pedido']

    def __str__(self):
        return f"{self.orgao} - Pregão {self.numero_pregao}"

    @property
    def total(self):
        return sum(item.valor_total for item in self.itens.all())
class ItemPedido(models.Model):
    pedido = models.ForeignKey(Pedido, on_delete=models.CASCADE, related_name='itens')

    numero_item = models.PositiveIntegerField()
    descricao = models.TextField()
    unidade = models.CharField(max_length=10)
    quantidade = models.DecimalField(max_digits=10, decimal_places=2)
    marca = models.CharField(max_length=100, blank=True)

    valor_unitario = models.DecimalField(max_digits=10, decimal_places=2)
    valor_total = models.DecimalField(max_digits=10, decimal_places=2, editable=False)
    observacoes = models.TextField(blank=True)

    class Meta:
        ordering = ['numero_item']
        unique_together = ['pedido', 'numero_item']

    def save(self, *args, **kwargs):
        self.valor_total = self.quantidade * self.valor_unitario

        if not self.numero_item:
            ultimo = ItemPedido.objects.filter(pedido=self.pedido).order_by('-numero_item').first()
            self.numero_item = (ultimo.numero_item + 1) if ultimo else 1

        super().save(*args, **kwargs)

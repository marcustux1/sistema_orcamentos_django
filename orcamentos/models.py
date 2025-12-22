from django.db import models
from django.core.validators import MinValueValidator
from decimal import Decimal

class Empresa(models.Model):
    nome = models.CharField(max_length=100)
    cnpj = models.CharField(max_length=18, verbose_name='CNPJ', null=True, blank=True)
    endereco = models.TextField(verbose_name='Endereço',blank=True, null=True)
    telefone = models.CharField(max_length=20,blank=True, null=True)
    email = models.EmailField(blank=True, null=True)
    logo = models.ImageField(upload_to='logos/', verbose_name='Logo da Empresa', blank=True, null=True)
    cor = models.CharField(max_length=7, default='#2563eb',blank=True, null=True)  # Cor em hexadecimal
    ativa = models.BooleanField(default=True)
    criado_em = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = 'Empresa'
        verbose_name_plural = 'Empresas'
        ordering = ['nome']
    
    def __str__(self):
        return self.nome


class UnidadeMedida(models.Model):
    """Model para gerenciar unidades de medida dinamicamente"""
    sigla = models.CharField(max_length=10, unique=True)
    descricao = models.CharField(max_length=50)
    ativa = models.BooleanField(default=True)
    
    class Meta:
        verbose_name = 'Unidade de Medida'
        verbose_name_plural = 'Unidades de Medida'
        ordering = ['sigla']
    
    def __str__(self):
        return f"{self.sigla} - {self.descricao}"


class Cliente(models.Model):
    nome = models.CharField(max_length=200)
    cpf_cnpj = models.CharField(max_length=18, unique=True)
    endereco = models.TextField()
    telefone = models.CharField(max_length=20, blank=True, null=True)
    email = models.EmailField(blank=True, null=True)
    criado_em = models.DateTimeField(auto_now_add=True)
    atualizado_em = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'Cliente'
        verbose_name_plural = 'Clientes'
        ordering = ['nome']
    
    def __str__(self):
        return f"{self.nome} - {self.cpf_cnpj}"


class Orcamento(models.Model):
    STATUS_CHOICES = [
        ('rascunho', 'Rascunho'),
        ('enviado', 'Enviado'),
        ('aprovado', 'Aprovado'),
        ('rejeitado', 'Rejeitado'),
        ('pedido', 'Pedido Gerado'),  # Novo status
        ('cancelado', 'Cancelado'),
    ]
    
    empresa = models.ForeignKey(Empresa, on_delete=models.PROTECT, related_name='orcamentos')
    cliente = models.ForeignKey(Cliente, on_delete=models.PROTECT, related_name='orcamentos')
    numero = models.CharField(max_length=20, unique=True, editable=False)
    data_emissao = models.DateField(auto_now_add=True)
    data_validade = models.DateField(blank=True, null=True)
    validade_dias = models.IntegerField(default=15, verbose_name='Validade (dias)')
    prazo_entrega = models.CharField(max_length=100, default='A Combinar', verbose_name='Prazo de Entrega')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='rascunho')
    observacoes = models.TextField(blank=True)
    desconto = models.DecimalField(max_digits=10, decimal_places=2, default=0, validators=[MinValueValidator(0)])
    total = models.DecimalField(max_digits=10, decimal_places=2, default=0, editable=False)
    bloqueado = models.BooleanField(default=False, verbose_name='Orçamento Bloqueado')  # Novo campo
    criado_em = models.DateTimeField(auto_now_add=True)
    atualizado_em = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'Orçamento'
        verbose_name_plural = 'Orçamentos'
        ordering = ['-data_emissao', '-numero']
    
    def __str__(self):
        return f"Orçamento {self.numero} - {self.cliente.nome}"
    
    def save(self, *args, **kwargs):
        if not self.numero:
            # Gerar número único do orçamento
            ultimo = Orcamento.objects.filter(empresa=self.empresa).order_by('-id').first()
            if ultimo and ultimo.numero:
                ultimo_num = int(ultimo.numero.split('-')[-1])
                novo_num = ultimo_num + 1
            else:
                novo_num = 1
            self.numero = f"ORC-{self.empresa.id}-{novo_num:05d}"
        super().save(*args, **kwargs)
    
    def calcular_total(self):
        """Calcula o total do orçamento baseado nos itens"""
        subtotal = sum(item.valor_total for item in self.itens.all())
        self.total = subtotal - self.desconto
        self.save()
        return self.total
    
    def gerar_pedido(self):
        """Converte orçamento em pedido e bloqueia edição"""
        self.status = 'pedido'
        self.bloqueado = True
        self.save()
    
    def pode_editar(self):
        """Verifica se o orçamento pode ser editado"""
        return not self.bloqueado


class ItemOrcamento(models.Model):
    orcamento = models.ForeignKey(Orcamento, on_delete=models.CASCADE, related_name='itens')
    numero_item = models.PositiveIntegerField()
    unidade = models.ForeignKey(UnidadeMedida, on_delete=models.PROTECT, verbose_name='Unidade')
    quantidade = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(0)])
    descricao = models.TextField(verbose_name='Descrição')
    marca = models.CharField(max_length=100, blank=True)
    valor_unitario = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(0)], verbose_name='Valor Unitário')
    valor_total = models.DecimalField(max_digits=10, decimal_places=2, editable=False)
    
    class Meta:
        verbose_name = 'Item do Orçamento'
        verbose_name_plural = 'Itens do Orçamento'
        ordering = ['numero_item']
        unique_together = ['orcamento', 'numero_item']
    
    def __str__(self):
        return f"Item {self.numero_item} - {self.descricao[:50]}"
    
    def save(self, *args, **kwargs):
        # Calcular valor total automaticamente
        self.valor_total = self.quantidade * self.valor_unitario
        
        # Atribuir número do item automaticamente se não existir
        if not self.numero_item:
            ultimo_item = ItemOrcamento.objects.filter(orcamento=self.orcamento).order_by('-numero_item').first()
            self.numero_item = (ultimo_item.numero_item + 1) if ultimo_item else 1
        
        super().save(*args, **kwargs)
        
        # Atualizar total do orçamento
        self.orcamento.calcular_total()
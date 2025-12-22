# orcamentos/admin.py
from django.contrib import admin
from .models import Empresa, Cliente, Orcamento, ItemOrcamento, UnidadeMedida

@admin.register(Empresa)
class EmpresaAdmin(admin.ModelAdmin):
    list_display = ['nome', 'cnpj', 'telefone', 'email', 'cor', 'ativa', 'criado_em']
    list_filter = ['ativa']
    search_fields = ['nome', 'cnpj']
    fieldsets = (
        ('Informações Básicas', {
            'fields': ('nome', 'cnpj','logo', 'cor', 'ativa')
        }),
        ('Contato', {
            'fields': ('endereco', 'telefone', 'email')
        }),
    )

@admin.register(UnidadeMedida)
class UnidadeMedidaAdmin(admin.ModelAdmin):
    list_display = ['sigla', 'descricao', 'ativa']
    list_filter = ['ativa']
    search_fields = ['sigla', 'descricao']
    list_editable = ['ativa']
    ordering = ['sigla']

@admin.register(Cliente)
class ClienteAdmin(admin.ModelAdmin):
    list_display = ['nome', 'cpf_cnpj', 'telefone', 'email', 'criado_em']
    search_fields = ['nome', 'cpf_cnpj', 'telefone']
    list_filter = ['criado_em']
    date_hierarchy = 'criado_em'

class ItemOrcamentoInline(admin.TabularInline):
    model = ItemOrcamento
    extra = 1
    fields = ['numero_item', 'unidade', 'quantidade', 'descricao', 'marca', 'valor_unitario', 'valor_total']
    readonly_fields = ['valor_total']

@admin.register(Orcamento)
class OrcamentoAdmin(admin.ModelAdmin):
    list_display = ['numero', 'empresa', 'cliente', 'data_emissao', 'status', 'bloqueado', 'total', 'criado_em']
    list_filter = ['status', 'empresa', 'data_emissao', 'bloqueado']
    search_fields = ['numero', 'cliente__nome', 'cliente__cpf_cnpj']
    inlines = [ItemOrcamentoInline]
    readonly_fields = ['numero', 'total', 'criado_em', 'atualizado_em']
    date_hierarchy = 'data_emissao'
    
    fieldsets = (
        ('Informações Principais', {
            'fields': ('numero', 'empresa', 'cliente', 'status', 'bloqueado')
        }),
        ('Prazos', {
            'fields': ('data_emissao', 'data_validade', 'validade_dias', 'prazo_entrega')
        }),
        ('Valores', {
            'fields': ('desconto', 'total')
        }),
        ('Observações', {
            'fields': ('observacoes',),
            'classes': ('collapse',)
        }),
        ('Datas do Sistema', {
            'fields': ('criado_em', 'atualizado_em'),
            'classes': ('collapse',)
        }),
    )
    
    def save_model(self, request, obj, form, change):
        """Impedir edição de orçamentos bloqueados"""
        if change and obj.bloqueado:
            from django.contrib import messages
            messages.warning(request, 'Este orçamento está bloqueado e não pode ser editado!')
            return
        super().save_model(request, obj, form, change)

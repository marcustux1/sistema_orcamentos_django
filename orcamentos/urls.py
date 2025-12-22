# =========================================
# orcamentos/urls.py - COMPLETO E ATUALIZADO
# =========================================

from django.urls import path
from . import views

app_name = 'orcamentos'

urlpatterns = [
    path('', views.selecionar_empresa, name='selecionar_empresa'),
    path('criar/<int:empresa_id>/', views.criar_orcamento, name='criar_orcamento'),
    path('editar/<int:orcamento_id>/', views.editar_orcamento, name='editar_orcamento'),
    path('listar/', views.listar_orcamentos, name='listar_orcamentos'),
    path('visualizar/<int:orcamento_id>/', views.visualizar_orcamento, name='visualizar_orcamento'),
    path('deletar/<int:orcamento_id>/', views.deletar_orcamento, name='deletar_orcamento'),
    path('gerar-pedido/<int:orcamento_id>/', views.gerar_pedido, name='gerar_pedido'),
    path('gerar-pdf/<int:orcamento_id>/', views.gerar_pdf, name='gerar_pdf'),
]

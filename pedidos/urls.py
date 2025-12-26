from django.urls import path
from . import views

urlpatterns = [
    path('', views.lista_pedidos, name='lista_pedidos'),
    path('novo/', views.criar_pedido, name='criar_pedido'),
    path('<int:pedido_id>/itens/', views.adicionar_itens, name='adicionar_itens'),
]

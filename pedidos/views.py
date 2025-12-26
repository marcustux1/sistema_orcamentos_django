from django.shortcuts import render, redirect, get_object_or_404
from .models import Pedido, ItemPedido
from .forms import PedidoForm, ItemPedidoForm

def lista_pedidos(request):
    pedidos = Pedido.objects.all()
    return render(request, 'pedidos/lista_pedidos.html', {'pedidos': pedidos})


def criar_pedido(request):
    if request.method == 'POST':
        form = PedidoForm(request.POST)
        if form.is_valid():
            pedido = form.save()
            return redirect('adicionar_itens', pedido_id=pedido.id)
    else:
        form = PedidoForm()

    return render(request, 'pedidos/criar_pedido.html', {'form': form})


def adicionar_itens(request, pedido_id):
    pedido = get_object_or_404(Pedido, id=pedido_id)
    itens = pedido.itens.all()

    if request.method == 'POST':
        form = ItemPedidoForm(request.POST)
        if form.is_valid():
            item = form.save(commit=False)
            item.pedido = pedido
            item.save()
            return redirect('adicionar_itens', pedido_id=pedido.id)
    else:
        form = ItemPedidoForm()

    return render(
        request,
        'pedidos/adicionar_itens.html',
        {
            'pedido': pedido,
            'itens': itens,
            'form': form
        }
    )

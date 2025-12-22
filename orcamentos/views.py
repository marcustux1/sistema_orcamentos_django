# orcamentos/views.py
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.db import transaction
from django.http import HttpResponse, FileResponse
from .models import Empresa, Orcamento, ItemOrcamento, Cliente, UnidadeMedida
from decimal import Decimal
from datetime import timedelta
import io
import os
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT

def selecionar_empresa(request):
    """View para selecionar a empresa"""
    empresas = Empresa.objects.filter(ativa=True)
    return render(request, 'orcamentos/selecionar_empresa.html', {'empresas': empresas})

def criar_orcamento(request, empresa_id):
    """View para criar um novo orçamento"""
    empresa = get_object_or_404(Empresa, id=empresa_id, ativa=True)
    unidades = UnidadeMedida.objects.filter(ativa=True)
    
    if request.method == 'POST':
        try:
            with transaction.atomic():
                # Criar ou obter cliente
                cliente_nome = request.POST.get('cliente_nome')
                cliente_cpf_cnpj = request.POST.get('cliente_cpf_cnpj')
                cliente_endereco = request.POST.get('cliente_endereco')
                cliente_telefone = request.POST.get('cliente_telefone', '')
                
                cliente, created = Cliente.objects.get_or_create(
                    cpf_cnpj=cliente_cpf_cnpj,
                    defaults={
                        'nome': cliente_nome,
                        'endereco': cliente_endereco,
                        'telefone': cliente_telefone,
                    }
                )
                
                if not created:
                    cliente.nome = cliente_nome
                    cliente.endereco = cliente_endereco
                    cliente.telefone = cliente_telefone
                    cliente.save()
                
                # Criar orçamento
                orcamento = Orcamento.objects.create(
                    empresa=empresa,
                    cliente=cliente,
                    status='rascunho'
                )
                
                # Processar itens
                itens_data = {}
                for key, value in request.POST.items():
                    if key.startswith('itens['):
                        parts = key.replace('itens[', '').replace(']', '').split('[')
                        if len(parts) == 2:
                            index, field = parts
                            if index not in itens_data:
                                itens_data[index] = {}
                            itens_data[index][field] = value
                
                # Criar itens do orçamento
                for index, item_data in itens_data.items():
                    if all(k in item_data for k in ['unidade', 'quantidade', 'descricao', 'valor_unitario']):
                        unidade = UnidadeMedida.objects.get(id=item_data['unidade'])
                        ItemOrcamento.objects.create(
                            orcamento=orcamento,
                            numero_item=int(index),
                            unidade=unidade,
                            quantidade=Decimal(item_data['quantidade']),
                            descricao=item_data['descricao'],
                            marca=item_data.get('marca', ''),
                            valor_unitario=Decimal(item_data['valor_unitario'])
                        )
                
                orcamento.calcular_total()
                
                messages.success(request, f'Orçamento {orcamento.numero} criado com sucesso!')
                return redirect('orcamentos:listar_orcamentos')
                
        except Exception as e:
            messages.error(request, f'Erro ao criar orçamento: {str(e)}')
    
    context = {
        'empresa': empresa,
        'unidades': unidades,
    }
    return render(request, 'orcamentos/criar_orcamento.html', context)

def editar_orcamento(request, orcamento_id):
    """View para editar um orçamento existente"""
    orcamento = get_object_or_404(Orcamento, id=orcamento_id)
    
    if not orcamento.pode_editar():
        messages.error(request, 'Este orçamento está bloqueado e não pode ser editado!')
        return redirect('orcamentos:visualizar_orcamento', orcamento_id=orcamento.id)
    
    unidades = UnidadeMedida.objects.filter(ativa=True)
    
    if request.method == 'POST':
        try:
            with transaction.atomic():
                # Atualizar cliente
                orcamento.cliente.nome = request.POST.get('cliente_nome')
                orcamento.cliente.cpf_cnpj = request.POST.get('cliente_cpf_cnpj')
                orcamento.cliente.endereco = request.POST.get('cliente_endereco')
                orcamento.cliente.telefone = request.POST.get('cliente_telefone', '')
                orcamento.cliente.save()
                
                # Deletar itens antigos
                orcamento.itens.all().delete()
                
                # Processar novos itens
                itens_data = {}
                for key, value in request.POST.items():
                    if key.startswith('itens['):
                        parts = key.replace('itens[', '').replace(']', '').split('[')
                        if len(parts) == 2:
                            index, field = parts
                            if index not in itens_data:
                                itens_data[index] = {}
                            itens_data[index][field] = value
                
                # Criar novos itens
                for index, item_data in itens_data.items():
                    if all(k in item_data for k in ['unidade', 'quantidade', 'descricao', 'valor_unitario']):
                        unidade = UnidadeMedida.objects.get(id=item_data['unidade'])
                        ItemOrcamento.objects.create(
                            orcamento=orcamento,
                            numero_item=int(index),
                            unidade=unidade,
                            quantidade=Decimal(item_data['quantidade']),
                            descricao=item_data['descricao'],
                            marca=item_data.get('marca', ''),
                            valor_unitario=Decimal(item_data['valor_unitario'])
                        )
                
                orcamento.calcular_total()
                
                messages.success(request, f'Orçamento {orcamento.numero} atualizado com sucesso!')
                return redirect('orcamentos:visualizar_orcamento', orcamento_id=orcamento.id)
                
        except Exception as e:
            messages.error(request, f'Erro ao atualizar orçamento: {str(e)}')
    
    itens = orcamento.itens.all().order_by('numero_item')
    
    context = {
        'orcamento': orcamento,
        'empresa': orcamento.empresa,
        'unidades': unidades,
        'itens': itens,
        'editando': True,
    }
    return render(request, 'orcamentos/criar_orcamento.html', context)

def listar_orcamentos(request):
    """View para listar todos os orçamentos"""
    orcamentos = Orcamento.objects.all().select_related('empresa', 'cliente').order_by('-criado_em')
    return render(request, 'orcamentos/listar_orcamentos.html', {'orcamentos': orcamentos})

def visualizar_orcamento(request, orcamento_id):
    """View para visualizar detalhes de um orçamento"""
    orcamento = get_object_or_404(Orcamento, id=orcamento_id)
    itens = orcamento.itens.all().order_by('numero_item')
    
    context = {
        'orcamento': orcamento,
        'itens': itens,
    }
    return render(request, 'orcamentos/visualizar_orcamento.html', context)

def gerar_pedido(request, orcamento_id):
    """Converte orçamento em pedido e bloqueia edição"""
    orcamento = get_object_or_404(Orcamento, id=orcamento_id)
    
    if request.method == 'POST':
        if not orcamento.bloqueado:
            orcamento.gerar_pedido()
            messages.success(request, f'Pedido gerado com sucesso! O orçamento {orcamento.numero} está agora bloqueado.')
        else:
            messages.warning(request, 'Este orçamento já foi convertido em pedido.')
        
        return redirect('orcamentos:visualizar_orcamento', orcamento_id=orcamento.id)
    
    return render(request, 'orcamentos/confirmar_pedido.html', {'orcamento': orcamento})

def deletar_orcamento(request, orcamento_id):
    """View para deletar um orçamento"""
    orcamento = get_object_or_404(Orcamento, id=orcamento_id)
    
    if orcamento.bloqueado:
        messages.error(request, 'Não é possível deletar um pedido gerado!')
        return redirect('orcamentos:listar_orcamentos')
    
    if request.method == 'POST':
        numero = orcamento.numero
        orcamento.delete()
        messages.success(request, f'Orçamento {numero} deletado com sucesso!')
        return redirect('orcamentos:listar_orcamentos')
    
    return render(request, 'orcamentos/confirmar_delete.html', {'orcamento': orcamento})

def gerar_pdf(request, orcamento_id):
    """Gera PDF do orçamento com logo da empresa"""
    orcamento = get_object_or_404(Orcamento, id=orcamento_id)
    itens = orcamento.itens.all().order_by('numero_item')
    
    # Criar buffer
    buffer = io.BytesIO()
    
    # Criar documento PDF
    doc = SimpleDocTemplate(buffer, pagesize=A4, topMargin=20*mm, bottomMargin=30*mm)
    elements = []
    styles = getSampleStyleSheet()
    
    # Estilo customizado
    titulo_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=16,
        textColor=colors.HexColor(orcamento.empresa.cor),
        alignment=TA_CENTER,
        spaceAfter=2,
    )
    
    subtitulo_style = ParagraphStyle(
        'Subtitle',
        parent=styles['Normal'],
        fontSize=10,
        alignment=TA_CENTER,
        spaceAfter=2,
    )
    
    # ============================================
    # LOGO DA EMPRESA (SE EXISTIR)
    # ============================================
    if orcamento.empresa.logo:
        try:
            from PIL import Image as PILImage
            
            # Caminho completo da logo
            logo_path = orcamento.empresa.logo.path
            
            # Verificar se o arquivo existe
            if os.path.exists(logo_path):
                # Abrir imagem para verificar dimensões
                pil_img = PILImage.open(logo_path)
                img_width, img_height = pil_img.size
                
                # Calcular proporção para manter aspect ratio
                # Tamanho máximo da logo no PDF
                max_width = 40 * mm   # 80 milímetros de largura
                max_height = 20 * mm  # 40 milímetros de altura
                
                # Calcular a proporção para manter o aspecto original
                ratio = min(max_width / img_width, max_height / img_height)
                new_width = img_width * ratio
                new_height = img_height * ratio
                
                # Adicionar logo ao PDF
                logo = Image(logo_path, width=new_width, height=new_height)
                logo.hAlign = 'CENTER'
                elements.append(logo)
                #elements.append(Spacer(1, 5*mm))
        except ImportError:
            # Se PIL não estiver instalado, apenas continuar sem a logo
            print("Aviso: Pillow não está instalado. A logo não será incluída no PDF.")
            print("Execute: pip install pillow")
        except Exception as e:
            # Se houver qualquer erro ao carregar a logo, apenas continuar sem ela
            print(f"Erro ao carregar logo: {e}")
    
    # ============================================
    # CABEÇALHO COM DADOS DA EMPRESA
    # ============================================
    elements.append(Paragraph(f"<b>{orcamento.empresa.nome}</b>", titulo_style))
    elements.append(Paragraph(f"CNPJ: {orcamento.empresa.cnpj}", subtitulo_style))
    elements.append(Paragraph(f"{orcamento.empresa.endereco}", subtitulo_style))
    elements.append(Paragraph(f"Tel: {orcamento.empresa.telefone} | Email: {orcamento.empresa.email}", subtitulo_style))
   # elements.append(Spacer(1,0*mm))
    
    # Título do documento
    tipo_doc = "PEDIDO" if orcamento.status == 'pedido' else "ORÇAMENTO"
    elements.append(Paragraph(f"<b>{tipo_doc} Nº {orcamento.numero}</b>", titulo_style))
   # elements.append(Spacer(1,0*mm))
    
    # Informações do cliente
    cliente_info = [
        ['Cliente:', orcamento.cliente.nome],
        ['CPF/CNPJ:', orcamento.cliente.cpf_cnpj],
        ['Endereço:', orcamento.cliente.endereco],
    ]
    
    if orcamento.cliente.telefone:
        cliente_info.append(['Telefone:', orcamento.cliente.telefone])
    
    cliente_table = Table(cliente_info, colWidths=[40*mm, 130*mm])
    cliente_table.setStyle(TableStyle([
        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 9),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
    ]))
    elements.append(cliente_table)
    elements.append(Spacer(1, 5*mm))
    
    # Informações da proposta
    proposta_info = [
        ['Data de Emissão:', orcamento.data_emissao.strftime('%d/%m/%Y')],
        ['Validade da Proposta:', f'{orcamento.validade_dias} dias'],
        ['Prazo de Entrega:', orcamento.prazo_entrega],
    ]
    
    proposta_table = Table(proposta_info, colWidths=[50*mm, 120*mm])
    proposta_table.setStyle(TableStyle([
        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 9),
    ]))
    elements.append(proposta_table)
    #elements.append(Spacer(1, 8*mm))
    
    # Tabela de itens
    data = [['#', 'Und', 'Qtd', 'Descrição', 'Marca', 'Valor Unit.', 'Total']]
    
    for item in itens:
        data.append([
            str(item.numero_item),
            item.unidade.sigla,
            str(item.quantidade),
            item.descricao[:50],
            item.marca or '-',
            f'R$ {item.valor_unitario:,.2f}'.replace(',', 'X').replace('.', ',').replace('X', '.'),
            f'R$ {item.valor_total:,.2f}'.replace(',', 'X').replace('.', ',').replace('X', '.'),
        ])
    
    # Linha de total
    data.append(['', '', '', '', '', 'TOTAL:', f'R$ {orcamento.total:,.2f}'.replace(',', 'X').replace('.', ',').replace('X', '.')])
    
    table = Table(data, colWidths=[10*mm, 15*mm, 15*mm, 65*mm, 30*mm, 25*mm, 28*mm])
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor(orcamento.empresa.cor)),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('ALIGN', (3, 1), (3, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 9),
        ('FONTSIZE', (0, 1), (-1, -1), 8),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('GRID', (0, 0), (-1, -2), 1, colors.grey),
        ('LINEABOVE', (0, -1), (-1, -1), 2, colors.HexColor(orcamento.empresa.cor)),
        ('BACKGROUND', (0, -1), (-1, -1), colors.lightgrey),
        ('FONTNAME', (5, -1), (-1, -1), 'Helvetica-Bold'),
    ]))
    elements.append(table)
    #elements.append(Spacer(1, 10*mm))
    
    # Texto de concordância
    texto_concordancia = """
    Proponho o fornecimento dos produtos nos valores mencionados, sob as condições gerais 
    e específicas, indicadas neste formulário com as quais concordo.
    """
    elements.append(Paragraph(texto_concordancia, styles['Normal']))
   # elements.append(Spacer(1, 5*mm))
    
    # Empresa e CNPJ
    elements.append(Paragraph(f"<b>{orcamento.empresa.nome}</b> - CNPJ: {orcamento.empresa.cnpj}", 
                             ParagraphStyle('Center', parent=styles['Normal'], alignment=TA_CENTER)))
    elements.append(Spacer(1, 15*mm))
    
    # Linha de assinatura
    linha_assinatura = Table([['_' * 60]], colWidths=[150*mm])
    linha_assinatura.setStyle(TableStyle([
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
    ]))
    elements.append(linha_assinatura)
    elements.append(Paragraph("Assinatura e Carimbo", 
                             ParagraphStyle('Center', parent=styles['Normal'], alignment=TA_CENTER, fontSize=9)))
    
    # Construir PDF
    doc.build(elements)
    
    # Retornar PDF
    buffer.seek(0)
    return FileResponse(buffer, as_attachment=True, filename=f'{orcamento.numero}.pdf')
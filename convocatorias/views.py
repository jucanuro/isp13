from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from .models import Convocatoria, DocumentoConvocatoria
from django.db import transaction

def home(request):
    plazas_conteo = Convocatoria.objects.filter(estado='PUBLICADO').count()
    
    print(f"DEBUG: Convocatorias encontradas: {plazas_conteo}")
    
    return render(request, 'convocatorias.html', {
        'plazas_conteo': plazas_conteo
    })

def listar_convocatorias(request):
    query = request.GET.get('q', '')
    estado_filtro = request.GET.get('estado', 'todos')
    
    convocatorias = Convocatoria.objects.all()
    
    if query:
        convocatorias = convocatorias.filter(titulo__icontains=query)
    
    if estado_filtro != 'todos':
        convocatorias = convocatorias.filter(estado=estado_filtro.upper())

    return render(request, 'convocatorias/listar_convocatoria.html', {
        'convocatorias': convocatorias,
        'query': query,
        'estado_actual': estado_filtro
    })

def gestionar_convocatoria(request, pk=None):
    convocatoria = get_object_or_404(Convocatoria, pk=pk) if pk else None
    
    if request.method == 'POST':
        titulo = request.POST.get('titulo')
        descripcion = request.POST.get('descripcion') or f"Proceso de convocatoria: {titulo}"
        info_correo = request.POST.get('info_correo')
        info_mesa_partes = request.POST.get('info_mesa_partes')
        estado = request.POST.get('estado')

        with transaction.atomic(): 
            if convocatoria:
                convocatoria.titulo = titulo
                convocatoria.descripcion = descripcion
                convocatoria.info_correo = info_correo
                convocatoria.info_mesa_partes = info_mesa_partes
                convocatoria.estado = estado
                convocatoria.save()
            else:
                convocatoria = Convocatoria.objects.create(
                    titulo=titulo,
                    descripcion=descripcion,
                    info_correo=info_correo,
                    info_mesa_partes=info_mesa_partes,
                    estado=estado
                )

            fases = request.POST.getlist('fase[]')
            nombres_doc = request.POST.getlist('nombre_doc[]')
            archivos = request.FILES.getlist('archivo[]')

            for i in range(len(archivos)):
                DocumentoConvocatoria.objects.create(
                    convocatoria=convocatoria,
                    fase=fases[i] if i < len(fases) else 'OTRO',
                    nombre_documento=nombres_doc[i] if i < len(nombres_doc) else f"Documento_{i}",
                    archivo=archivos[i]
                )

        messages.success(request, "Proceso guardado exitosamente.")
        return redirect('convocatoria:listar_convocatorias')

    return render(request, 'convocatorias/registrar_convocatoria.html', {
        'convocatoria': convocatoria,
        'fases_choices': DocumentoConvocatoria.FASE_CHOICES,
        'estados_choices': Convocatoria.ESTADO_CHOICES,
        'editando': bool(pk) 
    })

def eliminar_documento(request, doc_id):
    documento = get_object_or_404(DocumentoConvocatoria, id=doc_id)
    convocatoria_id = documento.convocatoria.id
    documento.delete()
    return redirect('convocatoria:editar_convocatoria', pk=convocatoria_id)
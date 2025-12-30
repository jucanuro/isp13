from django.shortcuts import render, redirect, get_object_or_404
from .models import Tesis
from django.contrib import messages
from django.http import HttpResponse
from lxml import etree

def registrar_tesis(request):
    if request.method == 'POST':
        titulo = request.POST.get('titulo')
        autor = request.POST.get('autor')
        asesor = request.POST.get('asesor')
        resumen = request.POST.get('resumen')
        archivo = request.FILES.get('archivo_pdf') 
        if titulo and autor and archivo:
            nueva_tesis = Tesis(
                titulo=titulo,
                autor=autor,
                asesor=asesor,
                resumen=resumen,
                archivo_pdf=archivo
            )
            nueva_tesis.save()
            messages.success(request, "¡Tesis registrada con éxito! Esperando validación.")
            return redirect('investigacion:lista_tesis') 
            
    return render(request, 'investigacion/registro.html')

def lista_tesis(request):
    estado_filtro = request.GET.get('estado')
    
    if estado_filtro and estado_filtro != 'todos':
        tesis_locales = Tesis.objects.filter(estado=estado_filtro).order_by('-fecha_registro')
    else:
        tesis_locales = Tesis.objects.all().order_by('-fecha_registro')

    return render(request, 'investigacion/lista.html', {
        'tesis_locales': tesis_locales,
        'estado_actual': estado_filtro or 'todos'
    })

def validar_tesis(request, tesis_id):
    tesis = get_object_or_404(Tesis, id=tesis_id)
    
    errores = []
    if not tesis.archivo_pdf:
        errores.append("Error: No se puede validar sin el archivo PDF original.")
    if len(tesis.resumen) < 10:
        errores.append("Error: El resumen es demasiado breve para los estándares ALICIA.")
    
    if errores:
        for error in errores:
            messages.error(request, error)
        return redirect('investigacion:lista_tesis')

    tesis.estado = 'validado'
    tesis.save()
    messages.success(request, f"¡Éxito! La tesis '{tesis.titulo[:30]}' ha sido validada correctamente.")
    return redirect('investigacion:lista_tesis')


def enviar_alicia(request, tesis_id):
    tesis = get_object_or_404(Tesis, id=tesis_id)
    
    campos_obligatorios = {
        'title': tesis.titulo,
        'creator': tesis.autor,
        'description': tesis.resumen,
        'format': 'application/pdf',
        'type': 'info:eu-repo/semantics/bachelorThesis' 
    }
    
    faltantes = [k for k, v in campos_obligatorios.items() if not v]

    if faltantes:
        messages.error(request, f"Error de Metadatos: El registro no cumple con el esquema Dublin Core requerido por ALICIA.")
        return redirect('investigacion:lista_tesis')

    try:
        tesis.estado = 'enviado' 
        tesis.save()
        
        messages.success(request, "¡Publicación Exitosa! La tesis ha sido depositada en el Repositorio Institucional y está lista para ser recolectada por el nodo nacional ALICIA.")
        
    except Exception as e:
        messages.error(request, "Error en el servidor de base de datos institucional.")

    return redirect('investigacion:lista_tesis')

from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from lxml import etree

def oai_repository(request, tesis_id):
    tesis = get_object_or_404(Tesis, id=tesis_id, estado='enviado')
    
    NS_MAP = {
        'oai_dc': "http://www.openarchives.org/OAI/2.0/oai_dc/",
        'dc': "http://purl.org/dc/elements/1.1/",
        'xsi': "http://www.w3.org/2001/XMLSchema-instance"
    }

    schema_location = "http://www.openarchives.org/OAI/2.0/oai_dc/ http://www.openarchives.org/OAI/2.0/oai_dc.xsd"
    
    root = etree.Element(
        "{%s}dc" % NS_MAP['oai_dc'], 
        nsmap=NS_MAP,
        attrib={"{%s}schemaLocation" % NS_MAP['xsi']: schema_location}
    )
    
    etree.SubElement(root, "{%s}title" % NS_MAP['dc']).text = tesis.titulo
    etree.SubElement(root, "{%s}creator" % NS_MAP['dc']).text = tesis.autor
    etree.SubElement(root, "{%s}description" % NS_MAP['dc']).text = tesis.resumen
    etree.SubElement(root, "{%s}publisher" % NS_MAP['dc']).text = 'IESPP "13 DE JULIO DE 1882" SAN PABLO'
    
    etree.SubElement(root, "{%s}date" % NS_MAP['dc']).text = tesis.fecha_registro.strftime('%Y-%m-%d')
    etree.SubElement(root, "{%s}type" % NS_MAP['dc']).text = "info:eu-repo/semantics/bachelorThesis"
    etree.SubElement(root, "{%s}rights" % NS_MAP['dc']).text = "info:eu-repo/semantics/openAccess"
    etree.SubElement(root, "{%s}language" % NS_MAP['dc']).text = "spa"
    
    if tesis.archivo_pdf:
        full_url = request.build_absolute_uri(tesis.archivo_pdf.url)
        etree.SubElement(root, "{%s}identifier" % NS_MAP['dc']).text = full_url

    xml_output = etree.tostring(root, pretty_print=True, xml_declaration=True, encoding='UTF-8')
    
    return HttpResponse(xml_output, content_type="application/xml")

def editar_tesis(request, tesis_id):
    tesis = get_object_or_404(Tesis, id=tesis_id)
    
    if request.method == 'POST':
        tesis.titulo = request.POST.get('titulo')
        tesis.autor = request.POST.get('autor')
        tesis.asesor = request.POST.get('asesor')
        tesis.resumen = request.POST.get('resumen')
        
        nuevo_archivo = request.FILES.get('archivo_pdf')
        if nuevo_archivo:
            tesis.archivo_pdf = nuevo_archivo
            
        tesis.save()
        messages.success(request, "¡Cambios guardados correctamente!")
        return redirect('investigacion:lista_tesis')
    
    return render(request, 'investigacion/registro.html', {
        'tesis': tesis, 
        'editando': True
    })
    
def eliminar_tesis(request, tesis_id):
    tesis = get_object_or_404(Tesis, id=tesis_id)
    tesis.delete()
    messages.warning(request, "La tesis ha sido eliminada del sistema.")
    return redirect('investigacion:lista_tesis')
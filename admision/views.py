from django.shortcuts import render
from .models import ResultadoAdmision


def resultados_admision_modal(request):
    resultados = (
        ResultadoAdmision.objects
        .select_related('tipo_examen')
        .filter(estado='publicado')
        .order_by('orden', '-fecha_examen', '-fecha_publicacion')
    )

    return render(request, 'modals/resultados_admision.html', {
        'resultados': resultados
    })
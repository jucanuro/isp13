from .models import Convocatoria

def conteo_convocatorias(request):
    cantidad = Convocatoria.objects.filter(estado__in=['PUBLICADO', 'EN_PROCESO']).count()
    return {
        'plazas_conteo': cantidad
    }
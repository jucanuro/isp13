from django import template

from core.models import MiembroEquipo

register = template.Library()


@register.filter
def agrupar_por_area(miembros):
    """
    Agrupa los miembros en el orden de MiembroEquipo.AREA_CHOICES
    (directiva → docente → administrativo), no en el alfabético del
    ordering del modelo. Omite las áreas sin miembros.
    """
    miembros = list(miembros)
    grupos = []
    for clave, etiqueta in MiembroEquipo.AREA_CHOICES:
        del_area = [m for m in miembros if m.area == clave]
        if del_area:
            grupos.append({"clave": clave, "etiqueta": etiqueta, "miembros": del_area})
    return grupos

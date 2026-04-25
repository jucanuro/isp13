from django.contrib import admin
from .models import TipoExamenAdmision, ResultadoAdmision


@admin.register(TipoExamenAdmision)
class TipoExamenAdmisionAdmin(admin.ModelAdmin):
    list_display = (
        'nombre',
        'activo',
        'orden',
        'creado',
        'actualizado',
    )

    list_filter = (
        'activo',
    )

    search_fields = (
        'nombre',
        'descripcion',
    )

    ordering = (
        'orden',
        'nombre',
    )

    list_editable = (
        'activo',
        'orden',
    )


@admin.register(ResultadoAdmision)
class ResultadoAdmisionAdmin(admin.ModelAdmin):
    list_display = (
        'titulo',
        'tipo_examen',
        'fecha_examen',
        'estado',
        'es_destacado',
        'orden',
        'fecha_publicacion',
    )

    list_filter = (
        'tipo_examen',
        'estado',
        'es_destacado',
        'fecha_examen',
    )

    search_fields = (
        'titulo',
        'descripcion',
        'tipo_examen__nombre',
    )

    ordering = (
        'orden',
        '-fecha_examen',
    )

    list_editable = (
        'estado',
        'es_destacado',
        'orden',
    )

    autocomplete_fields = (
        'tipo_examen',
    )
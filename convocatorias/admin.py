from django.contrib import admin
from django.utils.html import format_html
from .models import Convocatoria, DocumentoConvocatoria

class DocumentoInline(admin.StackedInline): 
    model = DocumentoConvocatoria
    extra = 1
    fieldsets = (
        (None, {
            'fields': (('fase', 'nombre_documento'), 'archivo')
        }),
    )

@admin.register(Convocatoria)
class ConvocatoriaAdmin(admin.ModelAdmin):
    list_display = ('titulo_recortado', 'estado', 'color_status', 'docs_count', 'fecha_creacion')
    list_editable = ('estado',)
    list_filter = ('estado', 'fecha_creacion')
    search_fields = ('titulo',)
    inlines = [DocumentoInline]

    fieldsets = (
        ('Configuración del Proceso', {
            'fields': ('titulo', 'estado'),
            'description': 'Identificación principal y estado de visibilidad en la web.'
        }),
        ('Contenido Informativo', {
            'fields': ('descripcion', 'mensaje_evaluacion'),
            'classes': ('collapse',), 
        }),
        ('Canales de Postulación', {
            'fields': (('info_correo', 'info_mesa_partes'),),
        }),
    )

    def titulo_recortado(self, obj):
        return obj.titulo[:60] + "..." if len(obj.titulo) > 60 else obj.titulo
    titulo_recortado.short_description = "Título"

    def docs_count(self, obj):
        return obj.documentos.count()
    docs_count.short_description = "Total Archivos"

    def color_status(self, obj):
        colores = {
            'REGISTRADO': '#94a3b8', 'PUBLICADO': '#22c55e',
            'EN_PROCESO': '#3b82f6', 'FINALIZADO': '#6b7280',
        }
        return format_html(
            '<span style="background:{}; color:white; padding:4px 10px; border-radius:15px; font-weight:bold; font-size:10px;">{}</span>',
            colores.get(obj.estado, '#000'), obj.get_estado_display()
        )
    color_status.short_description = "Indicador"

    class Media:
        css = { 'all': ('https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css',) }
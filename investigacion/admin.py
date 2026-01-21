from django.contrib import admin
from .models import Tesis

@admin.register(Tesis)
class TesisAdmin(admin.ModelAdmin):
    list_display = ('titulo_corto', 'autor', 'tipo_tesis_display', 'estado', 'fecha_publicacion')
    
    list_filter = ('estado', 'tipo_tesis', 'derechos_acceso', 'fecha_publicacion')
    
    search_fields = ('titulo', 'autor', 'autor_dni', 'asesor')
    
    fieldsets = (
        ('Información General', {
            'fields': ('titulo', 'autor', 'resumen', 'asesor')
        }),
        ('Datos de Identidad (RENATI)', {
            'fields': ('autor_dni', 'autor_orcid'),
            'description': 'Identificadores obligatorios para el cruce con SUNEDU/CONCYTEC'
        }),
        ('Clasificación ALICIA', {
            'fields': ('tipo_tesis', 'ocde_codigo', 'ocde_nombre', 'institucion'),
            'classes': ('collapse',), 
        }),
        ('Archivos y Publicación', {
            'fields': ('archivo_pdf', 'fecha_publicacion', 'derechos_acceso')
        }),
        ('Estado del Flujo', {
            'fields': ('estado',),
        }),
    )

    def titulo_corto(self, obj):
        return obj.titulo[:60] + "..." if len(obj.titulo) > 60 else obj.titulo
    titulo_corto.short_description = "Título"

    def tipo_tesis_display(self, obj):
        return obj.get_tipo_tesis_display()
    tipo_tesis_display.short_description = "Grado"

    actions = ['marcar_como_validado', 'marcar_como_enviado']

    def marcar_como_validado(self, request, queryset):
        queryset.update(estado='validado')

    def marcar_como_enviado(self, request, queryset):
        queryset.update(estado='enviado')
    marcar_como_enviado.short_description = "Marcar como enviadas a ALICIA"
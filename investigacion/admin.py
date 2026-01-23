from django.contrib import admin
from .models import Tesis, Autor, Asesor

class AutorInline(admin.TabularInline):
    model = Tesis.autores.through
    extra = 1
    verbose_name = "Autor de la Investigación"

class AsesorInline(admin.TabularInline):
    model = Tesis.asesores.through
    extra = 1
    verbose_name = "Asesor de la Investigación"

@admin.register(Autor)
class AutorAdmin(admin.ModelAdmin):
    list_display = ('nombre_completo', 'dni', 'orcid')
    search_fields = ('nombre_completo', 'dni')

@admin.register(Asesor)
class AsesorAdmin(admin.ModelAdmin):
    list_display = ('nombre_completo', 'dni')
    search_fields = ('nombre_completo', 'dni')

@admin.register(Tesis)
class TesisAdmin(admin.ModelAdmin):
    list_display = ('titulo_corto', 'get_autores', 'tipo_tesis_display', 'estado', 'fecha_publicacion')
    list_filter = ('estado', 'tipo_tesis', 'derechos_acceso', 'fecha_publicacion')
    search_fields = ('titulo', 'autores__nombre_completo', 'autores__dni', 'asesores__nombre_completo')
    
    inlines = [AutorInline, AsesorInline]
    exclude = ('autores', 'asesores')

    fieldsets = (
        ('Información General', {
            'fields': ('titulo', 'resumen')
        }),
        ('Clasificación ALICIA y OCDE', {
            'fields': ('tipo_tesis', 'ocde_codigo', 'ocde_nombre'),
            'description': 'Metadatos obligatorios para la recolección de CONCYTEC'
        }),
        ('Documentación Obligatoria (Trilogía)', {
            'fields': ('archivo_pdf', 'constancia_originalidad', 'reporte_turnitin'),
            'description': 'Cargue los tres archivos PDF requeridos para la validación'
        }),
        ('Datos Institucionales', {
            'fields': ('institucion_nombre', 'institucion_ruc', 'institucion_pais'),
            'classes': ('collapse',), 
        }),
        ('Publicación y Derechos', {
            'fields': ('fecha_publicacion', 'derechos_acceso', 'estado'),
        }),
    )


    def titulo_corto(self, obj):
        return obj.titulo[:60] + "..." if len(obj.titulo) > 60 else obj.titulo
    titulo_corto.short_description = "Título"

    def tipo_tesis_display(self, obj):
        return obj.get_tipo_tesis_display()
    tipo_tesis_display.short_description = "Grado"

    def get_autores(self, obj):
        return ", ".join([a.nombre_completo for a in obj.autores.all()])
    get_autores.short_description = "Autores"


    actions = ['marcar_como_validado', 'marcar_como_publicado']

    @admin.action(description="Validar seleccionadas (Biblioteca)")
    def marcar_como_validado(self, request, queryset):
        queryset.update(estado='validado')

    @admin.action(description="Marcar como publicadas en OAI-PMH")
    def marcar_como_publicado(self, request, queryset):
        queryset.update(estado='publicado')
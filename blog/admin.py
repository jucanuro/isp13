from django.contrib import admin
from .models import Post

@admin.register(Post)
class PostAdmin(admin.ModelAdmin):
    # Columnas que se verán en la lista principal
    list_display = ('titulo', 'autor', 'fecha_publicacion', 'publicado')
    
    # Filtros laterales para encontrar posts rápido
    list_filter = ('publicado', 'fecha_publicacion', 'autor')
    
    # Buscador por título y contenido
    search_fields = ('titulo', 'contenido')
    
    # Orden predeterminado (más reciente primero)
    ordering = ('-fecha_publicacion',)
    
    # Permite editar el estado de publicación directamente desde la lista
    list_editable = ('publicado',)
    
    # Rellena automáticamente el autor al crear un post desde el admin
    def save_model(self, request, obj, form, change):
        if not obj.pk:  # Si el post es nuevo
            obj.autor = request.user
        super().save_model(request, obj, form, change)

    # Mejorar la interfaz de edición
    fieldsets = (
        ('Contenido Principal', {
            'fields': ('titulo', 'contenido')
        }),
        ('Información de Autoría y Estado', {
            'fields': ('autor', 'publicado'),
            'description': 'Configuración de visibilidad del post.'
        }),
    )
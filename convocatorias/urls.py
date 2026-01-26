from django.urls import path
from . import views

app_name = 'convocatoria'

urlpatterns = [
    path('lista/', views.listar_convocatorias, name='listar_convocatorias'),
    
    path('registrar/', views.gestionar_convocatoria, name='registrar_convocatoria'),
    
    path('editar/<int:pk>/', views.gestionar_convocatoria, name='editar_convocatoria'),
    
    path('documento/eliminar/<int:doc_id>/', views.eliminar_documento, name='eliminar_documento'),
]
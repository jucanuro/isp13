from django.urls import path
from . import views

# Esta línea es la que falta y causa el error
app_name = 'investigacion' 

urlpatterns = [
    path('lista/', views.lista_tesis, name='lista_tesis'),
    path('registrar/', views.registrar_tesis, name='registrar_tesis'),
    path('validar/<int:tesis_id>/', views.validar_tesis, name='validar_tesis'),
    path('enviar-alicia/<int:tesis_id>/', views.enviar_alicia, name='enviar_alicia'),
    path('editar/<int:tesis_id>/', views.editar_tesis, name='editar_tesis'),
    path('eliminar/<int:tesis_id>/', views.eliminar_tesis, name='eliminar_tesis'),
]
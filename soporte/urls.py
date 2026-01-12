# soporte/urls.py
from django.urls import path
from . import views

app_name = 'soporte'

urlpatterns = [
    path('asistencia-identidad/', views.solicitar_asistencia, name='asistencia_identidad'),
        
    path('gestion/', views.lista_solicitudes, name='lista_solicitudes'),
]
from django.urls import path

from . import views


app_name = "biblioteca"


urlpatterns = [
    path("", views.catalogo, name="catalogo"),
    path("libro/<int:pk>/", views.detalle_libro, name="detalle_libro"),
    path("registrar/", views.registrar_libro, name="registrar_libro"),
]

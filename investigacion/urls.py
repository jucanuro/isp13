from django.urls import path

from . import views
from .views_oai import oai_endpoint


app_name = "investigacion"


urlpatterns = [
    path(
        "lista/",
        views.lista_tesis,
        name="lista_tesis",
    ),
    path(
        "registrar/",
        views.registrar_tesis,
        name="registrar_tesis",
    ),
    path(
        "editar/<int:tesis_id>/",
        views.editar_tesis,
        name="editar_tesis",
    ),
    path(
        "validar/<int:tesis_id>/",
        views.validar_tesis,
        name="validar_tesis",
    ),
    path(
        "enviar-alicia/<int:tesis_id>/",
        views.enviar_alicia,
        name="enviar_alicia",
    ),
    path(
        "eliminar/<int:tesis_id>/",
        views.eliminar_tesis,
        name="eliminar_tesis",
    ),
    path(
        "repositorio/tesis/<uuid:tesis_uuid>/",
        views.detalle_tesis,
        name="detalle_tesis",
    ),
    path(
        "repositorio/",
        views.repositorio_publico,
        name="repositorio_publico",
    ),
    path(
        "tesis/<int:tesis_id>/agregar-autor/",
        views.agregar_autor_ajax,
        name="agregar_autor_ajax",
    ),
    path(
        "tesis/<int:tesis_id>/agregar-asesor/",
        views.agregar_asesor_ajax,
        name="agregar_asesor_ajax",
    ),
    path(
        "tesis/<int:tesis_id>/eliminar-relacion/",
        views.eliminar_relacion_ajax,
        name="eliminar_relacion_ajax",
    ),
    path(
        "investigacion/oai/<int:tesis_id>/",
        views.oai_repository,
        name="oai_repository",
    ),
    path(
        "oai/",
        oai_endpoint,
        name="oai_endpoint",
    ),
]
from django.core.management.base import BaseCommand
from django.db import transaction

from core.models import MenuItem, MenuPrincipal


NAVBAR = [
    {
        "titulo": "Inicio",
        "tipo": "enlace",
        "url": "/",
        "items": [],
    },
    {
        "titulo": "Nosotros",
        "tipo": "menu",
        "items": [
            {"titulo": "Misión y Visión", "icono": "crosshairs", "modal_slug": "mision"},
            {"titulo": "Nuestra Historia", "icono": "landmark", "modal_slug": "historia"},
            {"titulo": "Organigrama", "icono": "project-diagram", "modal_slug": "organigrama"},
            {"titulo": "Directorio", "icono": "users-gear", "modal_slug": "personal"},
            {"titulo": "Docentes", "icono": "user-tie", "modal_slug": "docentes"},
        ],
    },
    {
        "titulo": "Admisión",
        "tipo": "menu",
        "items": [
            {"titulo": "Proceso de Admisión", "icono": "user-graduate", "modal_slug": "admision", "activo": False},
            {"titulo": "Cronograma", "icono": "calendar-check", "modal_slug": "cronograma_admision", "activo": False},
            {"titulo": "Requisitos", "icono": "clipboard-list", "modal_slug": "requisitos_admision", "activo": False},
            {"titulo": "Resultados de Admisión", "icono": "square-poll-vertical", "modal_slug": "resultados_admision"},
        ],
    },
    {
        "titulo": "Gestión Académica",
        "tipo": "menu",
        "items": [
            {"titulo": "Educación Inicial", "icono": "child", "modal_slug": "perfil_inicial", "grupo": "Programas de Estudio"},
            {"titulo": "Educación Primaria", "icono": "book-reader", "modal_slug": "perfil_primaria", "grupo": "Programas de Estudio"},
            {
                "titulo": "Secundaria",
                "subtitulo": "Ciudadania y Ciencias Sociales, Ciencia y Tecnología, Comunicación",
                "icono": "microscope",
                "modal_slug": "perfil_secundaria",
                "grupo": "Programas de Estudio",
            },
            {"titulo": "Matrícula", "icono": "file-signature", "modal_slug": "matricula", "grupo": "Gestión Académica"},
            {"titulo": "Horario Clases", "icono": "calendar-day", "modal_slug": "horario-clases", "grupo": "Gestión Académica"},
            {"titulo": "Horario Docentes", "icono": "user-clock", "modal_slug": "horario-docentes", "grupo": "Gestión Académica"},
            {"titulo": "Plan Curricular", "icono": "book", "modal_slug": "plan-curricular", "grupo": "Gestión Académica"},
        ],
    },
    {
        "titulo": "Unidades",
        "tipo": "menu",
        "items": [
            {"titulo": "Funciones", "icono": "file-alt", "modal_slug": "u_academica_funciones", "grupo": "U. Académica"},
            {"titulo": "Dependencias", "icono": "sitemap", "modal_slug": "u_academica_dependencias", "grupo": "U. Académica"},
            {"titulo": "Jefes", "icono": "user-tie", "modal_slug": "u_academica_jefes", "grupo": "U. Académica"},

            {"titulo": "Funciones", "icono": "file-alt", "modal_slug": "u_formacion_funciones", "grupo": "U. Formación Continua"},
            {"titulo": "Jefe de Unidades", "icono": "user-tie", "modal_slug": "u_formacion_jefe", "grupo": "U. Formación Continua"},
            {"titulo": "Cursos, Talleres y Programas", "icono": "chalkboard-teacher", "modal_slug": "u_formacion_cursos", "grupo": "U. Formación Continua"},
            {"titulo": "Conferencias, Seminarios", "icono": "bullhorn", "modal_slug": "u_formacion_conferencias", "grupo": "U. Formación Continua"},
            {"titulo": "Programas MINEDU", "icono": "landmark", "modal_slug": "u_formacion_minedu", "grupo": "U. Formación Continua"},

            {"titulo": "Funciones", "icono": "clipboard-list", "modal_slug": "u_inv_funciones", "grupo": "U. Investigación"},
            {"titulo": "Jefe", "icono": "user-tie", "modal_slug": "u_inv_jefe", "grupo": "U. Investigación"},
            {"titulo": "Líneas de Investigación", "icono": "route", "modal_slug": "u_inv_lineas", "grupo": "U. Investigación"},
            {"titulo": "Reglamento de Investigación", "icono": "gavel", "modal_slug": "u_inv_reglamento", "grupo": "U. Investigación"},
            {"titulo": "Guías de Investigación", "icono": "book", "modal_slug": "u_inv_guias", "grupo": "U. Investigación"},
            {"titulo": "Actividades y Eventos", "icono": "calendar-alt", "modal_slug": "u_inv_actividades", "grupo": "U. Investigación"},
            {"titulo": "Recursos", "icono": "folder-open", "modal_slug": "u_inv_recursos", "grupo": "U. Investigación"},
            {
                "titulo": "Gestión de Tesis",
                "icono": "graduation-cap",
                "tipo_destino": "url",
                "url": "/lista/",
                "grupo": "U. Investigación",
                "destacado": True,
            },

            {"titulo": "Funciones", "icono": "cog", "modal_slug": "u_bienestar_funciones", "grupo": "Bienestar y Empleabilidad"},
            {"titulo": "Jefe", "icono": "user", "modal_slug": "u_bienestar_jefe", "grupo": "Bienestar y Empleabilidad"},
            {"titulo": "Servicios", "icono": "concierge-bell", "modal_slug": "u_bienestar_servicios", "grupo": "Bienestar y Empleabilidad"},
            {"titulo": "Actividades", "icono": "calendar-check", "modal_slug": "u_bienestar_actividades", "grupo": "Bienestar y Empleabilidad"},
            {"titulo": "Seguimiento Egresados", "icono": "user-graduate", "modal_slug": "u_bienestar_egresados", "grupo": "Bienestar y Empleabilidad"},
            {"titulo": "Bolsa de Trabajo", "icono": "briefcase", "modal_slug": "u_bienestar_bolsa", "grupo": "Bienestar y Empleabilidad"},
        ],
    },
    {
        "titulo": "Documentos De Gestión",
        "tipo": "menu",
        "items": [
            {"titulo": "Reglamento Institucional", "subtitulo": "Vigencia 2023 - 2028", "icono": "file-contract", "modal_slug": "doc_reglamento"},
            {"titulo": "Proyecto Curricular (PCI)", "subtitulo": "Planificación Pedagógica", "icono": "book-open", "modal_slug": "doc_pci"},
            {"titulo": "Manual de Procesos", "subtitulo": "Gestión Institucional", "icono": "cog", "modal_slug": "doc_mapro"},
        ],
    },
]


class Command(BaseCommand):
    help = (
        "Crea el navbar principal (menús e ítems) a partir del contenido "
        "que antes estaba fijo en templates/header.html. Es seguro volver "
        "a correrlo: no duplica menús que ya existan con el mismo título."
    )

    @transaction.atomic
    def handle(self, *args, **options):
        creados_menu = 0
        creados_items = 0

        for orden_menu, datos_menu in enumerate(NAVBAR):
            menu, fue_creado = MenuPrincipal.objects.get_or_create(
                titulo=datos_menu["titulo"],
                defaults={
                    "tipo": datos_menu["tipo"],
                    "url": datos_menu.get("url", ""),
                    "orden": orden_menu,
                    "activo": True,
                },
            )

            if fue_creado:
                creados_menu += 1
            else:
                continue  # ya existía: no tocar sus ítems para no pisar ediciones

            for orden_item, datos_item in enumerate(datos_menu["items"]):
                MenuItem.objects.create(
                    menu=menu,
                    grupo=datos_item.get("grupo", ""),
                    titulo=datos_item["titulo"],
                    subtitulo=datos_item.get("subtitulo", ""),
                    icono=datos_item.get("icono", "file-alt"),
                    tipo_destino=datos_item.get("tipo_destino", "modal"),
                    modal_slug=datos_item.get("modal_slug", ""),
                    url=datos_item.get("url", ""),
                    destacado=datos_item.get("destacado", False),
                    orden=orden_item,
                    activo=datos_item.get("activo", True),
                )
                creados_items += 1

        self.stdout.write(
            self.style.SUCCESS(
                f"Navbar: {creados_menu} menús nuevos, {creados_items} ítems creados."
            )
        )

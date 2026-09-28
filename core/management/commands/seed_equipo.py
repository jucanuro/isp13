"""
Crea miembros del equipo de DEMO para revisar el diseño de la sección
del equipo institucional en el home.

⚠ NO CORRER EN PRODUCCIÓN: los nombres son ficticios y quedarían
publicados en el sitio. Usar solo en desarrollo local.

    python manage.py seed_equipo            # crea los registros de demo
    python manage.py seed_equipo --limpiar  # borra solo los registros de demo
"""

from django.core.management.base import BaseCommand
from django.db import transaction

from core.models import MiembroEquipo


# Marca que identifica los registros de demo: --limpiar borra solo los
# miembros cuyo nombre_completo coincide exactamente con esta lista.
MIEMBROS_DEMO = [
    {"grado_academico": "Dr.", "nombre_completo": "Aurelio Tomás Ejemplo Ramos", "cargo": "Director General (DEMO)", "area": "directiva"},
    {"grado_academico": "Mg.", "nombre_completo": "Beatriz Elena Muestra Salinas", "cargo": "Jefa de Unidad Académica (DEMO)", "area": "directiva"},
    {"grado_academico": "Mg.", "nombre_completo": "Carlos Alberto Prueba Quispe", "cargo": "Secretario Académico (DEMO)", "area": "directiva"},
    {"grado_academico": "Lic.", "nombre_completo": "Diana Rosa Ficticia Torres", "cargo": "Docente de Matemática (DEMO)", "area": "docente"},
    {"grado_academico": "Mg.", "nombre_completo": "Eduardo Luis Ensayo Huamán", "cargo": "Docente de Comunicación (DEMO)", "area": "docente"},
    {"grado_academico": "", "nombre_completo": "Fabiola Maqueta Lima", "cargo": "Docente de Educación Inicial (DEMO)", "area": "docente"},
    {"grado_academico": "", "nombre_completo": "Gustavo Boceto Vega", "cargo": "Jefe de Administración (DEMO)", "area": "administrativo"},
    {"grado_academico": "Bach.", "nombre_completo": "Helena Borrador", "cargo": "Secretaria (DEMO)", "area": "administrativo"},
]


class Command(BaseCommand):
    help = (
        "Crea 8 miembros del equipo de DEMO (sin foto) para revisar el diseño. "
        "NO CORRER EN PRODUCCIÓN. Con --limpiar borra solo esos registros de demo."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "--limpiar",
            action="store_true",
            help="Borra solo los miembros de demo creados por este comando.",
        )

    @transaction.atomic
    def handle(self, *args, **options):
        self.stdout.write(self.style.WARNING(
            "⚠ seed_equipo crea datos FICTICIOS. No lo corras en producción."
        ))

        nombres_demo = [m["nombre_completo"] for m in MIEMBROS_DEMO]

        if options["limpiar"]:
            borrados, _ = MiembroEquipo.objects.filter(
                nombre_completo__in=nombres_demo
            ).delete()
            self.stdout.write(self.style.SUCCESS(f"Borrados {borrados} miembros de demo."))
            return

        creados = 0
        for orden, datos in enumerate(MIEMBROS_DEMO):
            _, creado = MiembroEquipo.objects.get_or_create(
                nombre_completo=datos["nombre_completo"],
                defaults={**datos, "orden": orden},
            )
            creados += creado

        self.stdout.write(self.style.SUCCESS(
            f"Creados {creados} miembros de demo ({len(MIEMBROS_DEMO) - creados} ya existían)."
        ))

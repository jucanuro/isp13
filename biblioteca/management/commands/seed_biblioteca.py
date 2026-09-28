from django.core.management.base import BaseCommand
from django.db import transaction

from biblioteca.models import Categoria, Libro


CATEGORIAS = [
    ("Pedagogía y didáctica", 1),
    ("Psicología educativa", 2),
    ("Educación inicial", 3),
    ("Ciencias y matemática", 4),
    ("Lenguaje y literatura", 5),
    ("Obras de consulta", 6),
]

# ISBN de demostración: válidos por dígito de control, no corresponden a
# ediciones reales. Dos registros sin ISBN a propósito (índice único parcial).
LIBROS = [
    {
        "titulo": "Didáctica general para la formación docente",
        "autores": "María Elena Salazar Ruiz",
        "tipo": "libro",
        "categoria": "Pedagogía y didáctica",
        "editorial": "Fondo Editorial Magisterial",
        "anio_publicacion": 2019,
        "isbn": "978-612-00-0001-4",
        "ejemplares": 4,
        "ubicacion": "371.3 SAL",
        "descripcion": "Fundamentos de la planificación, la mediación y la evaluación de los aprendizajes en el aula.",
    },
    {
        "titulo": "Evaluación formativa en la educación básica",
        "autores": "Jorge Luis Quispe Mendoza; Rosa Chávez Díaz",
        "tipo": "libro",
        "categoria": "Pedagogía y didáctica",
        "editorial": "Ediciones Andinas",
        "anio_publicacion": 2021,
        "isbn": "978-612-00-0002-1",
        "ejemplares": 3,
        "ubicacion": "371.26 QUI",
        "descripcion": "Criterios, rúbricas y retroalimentación para evaluar por competencias.",
    },
    {
        "titulo": "Psicología del desarrollo en la niñez",
        "autores": "Carmen Torres Vega",
        "tipo": "libro",
        "categoria": "Psicología educativa",
        "editorial": "Universitaria del Norte",
        "anio_publicacion": 2016,
        "isbn": "978-612-00-0003-8",
        "ejemplares": 2,
        "ubicacion": "155.4 TOR",
        "descripcion": "Desarrollo cognitivo, afectivo y social desde el nacimiento hasta los doce años.",
    },
    {
        "titulo": "El juego como estrategia en educación inicial",
        "autores": "Ana Lucía Rojas Paredes",
        "tipo": "manual",
        "categoria": "Educación inicial",
        "editorial": "Editorial Cajamarca",
        "anio_publicacion": 2020,
        "isbn": "",
        "ejemplares": 5,
        "ubicacion": "Estante A-2",
        "descripcion": "Propuestas de juego libre y dirigido para el aula de 3 a 5 años.",
    },
    {
        "titulo": "Matemática para docentes de primaria",
        "autores": "Pedro Huamán Cruz",
        "tipo": "libro",
        "categoria": "Ciencias y matemática",
        "editorial": "Fondo Editorial Magisterial",
        "anio_publicacion": 2018,
        "isbn": "978-612-00-0004-5",
        "ejemplares": 6,
        "ubicacion": "372.7 HUA",
        "descripcion": "Números, geometría y resolución de problemas con enfoque didáctico.",
    },
    {
        "titulo": "Ciencia escolar: indagación en el aula",
        "autores": "Lucía Fernández Soto; Miguel Ángel Ramos",
        "tipo": "manual",
        "categoria": "Ciencias y matemática",
        "editorial": "Ediciones Andinas",
        "anio_publicacion": 2022,
        "isbn": "",
        "ejemplares": 2,
        "ubicacion": "Estante C-1",
        "descripcion": "Secuencias de indagación científica para primaria y secundaria.",
    },
    {
        "titulo": "Comprensión lectora y producción de textos",
        "autores": "Silvia Mendoza Alarcón",
        "tipo": "libro",
        "categoria": "Lenguaje y literatura",
        "editorial": "Universitaria del Norte",
        "anio_publicacion": 2017,
        "isbn": "978-612-00-0005-2",
        "ejemplares": 3,
        "ubicacion": "372.4 MEN",
        "descripcion": "Estrategias para leer, comprender y escribir textos académicos y escolares.",
    },
    {
        "titulo": "Revista Peruana de Educación, n.º 12",
        "autores": "Comité editorial",
        "tipo": "revista",
        "categoria": "Pedagogía y didáctica",
        "editorial": "Asociación de Docentes del Perú",
        "anio_publicacion": 2023,
        "isbn": "",
        "ejemplares": 1,
        "ubicacion": "Hemeroteca H-4",
        "descripcion": "Número dedicado a la formación inicial docente en zonas rurales.",
    },
    {
        "titulo": "Diccionario de la lengua española (edición escolar)",
        "autores": "Equipo lexicográfico",
        "tipo": "referencia",
        "categoria": "Obras de consulta",
        "editorial": "Editorial Lexis",
        "anio_publicacion": 2015,
        "isbn": "978-612-00-0006-9",
        "ejemplares": 8,
        "ubicacion": "R 463 DIC",
        "descripcion": "Obra de consulta en sala. No se presta a domicilio.",
    },
    {
        "titulo": "Historia de San Pablo y su escuela normal",
        "autores": "Oscar Cabrera Linares",
        "tipo": "otro",
        "categoria": None,
        "editorial": "Edición del autor",
        "anio_publicacion": 1998,
        "isbn": "84-00-00001-3",
        "ejemplares": 1,
        "ubicacion": "Fondo local F-1",
        "descripcion": "Crónica local de la educación en la provincia de San Pablo.",
    },
]


class Command(BaseCommand):
    help = "Crea categorías y 10 libros de demostración para la biblioteca."

    def add_arguments(self, parser):
        parser.add_argument(
            "--limpiar",
            action="store_true",
            help="Borra TODOS los libros y categorías antes de sembrar.",
        )

    @transaction.atomic
    def handle(self, *args, **options):
        if options["limpiar"]:
            libros, _ = Libro.objects.all().delete()
            categorias, _ = Categoria.objects.all().delete()
            self.stdout.write(f"Eliminados: {libros} libro(s) y {categorias} categoría(s).")

        categorias = {}
        for nombre, orden in CATEGORIAS:
            categorias[nombre], _ = Categoria.objects.get_or_create(
                nombre=nombre, defaults={"orden": orden}
            )

        creados = 0
        for datos in LIBROS:
            defaults = dict(datos)
            titulo = defaults.pop("titulo")
            defaults["categoria"] = categorias.get(defaults["categoria"])
            # Valida con las mismas reglas del formulario (ISBN, año) antes de guardar.
            Libro(titulo=titulo, **defaults).full_clean(
                validate_unique=False, validate_constraints=False
            )
            _, creado = Libro.objects.get_or_create(titulo=titulo, defaults=defaults)
            creados += creado

        self.stdout.write(
            self.style.SUCCESS(
                f"Biblioteca: {len(categorias)} categorías, {creados} libro(s) nuevo(s) "
                f"({Libro.objects.count()} en total)."
            )
        )

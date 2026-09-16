import random
import zlib
from datetime import date, timedelta

from django.core.files.base import ContentFile
from django.core.management.base import BaseCommand

from investigacion.models import Asesor, Autor, PalabraClave, Tesis


NOMBRES = [
    "María", "Ana", "Luis", "Carlos", "Rosa", "Elena", "Jorge", "Pedro",
    "Lucía", "Marco", "Yaneli", "Talita", "Doris", "Silvia", "Yesenia",
    "Anthony", "Bersa", "Karen", "Mariza", "Anita", "Thalia", "Benigno",
    "Carmen", "Oksana", "Yaqueli", "Cecilia", "Dayana", "Ruth", "Janina",
    "Santos", "Ediver", "Marleni", "Judith", "Teodora", "Denise",
]

APELLIDOS = [
    "Chávez", "Rodríguez", "Díaz", "Sánchez", "Vargas", "Torres",
    "Mendoza", "Ramos", "Cabrera", "Silva", "Zegarra", "Carrascal",
    "Pinedo", "Martos", "Rojas", "Alfaro", "Micha", "Rety", "Tello",
    "Aliaga", "Pereyra", "Paredes", "Zamora", "Human", "Leiva", "Quiliche",
    "Sifuentes", "Barboza", "Vargas", "Nuñez", "Cotrina", "Izquierdo",
    "Medina", "Mego", "Marin", "Aguilar", "Machuca", "Malaver", "Hoyos",
    "Bernal",
]

PROGRAMAS = [
    "Educación Inicial",
    "Educación Primaria",
    "Educación Secundaria",
]

HABILIDADES = [
    "comprensión lectora", "expresión oral", "pensamiento matemático",
    "autoestima", "autonomía", "motricidad fina", "cultura ambiental",
    "competencias socioemocionales", "identidad personal", "preescritura",
    "lectoescritura", "resolución de problemas", "hábitos de lectura",
    "gestión del enfoque ambiental", "autorregulación de emociones",
    "socialización", "estrategias lúdicas", "indagación científica",
]

TITULO_TEMPLATES = [
    "{habilidad_cap} en estudiantes de {grado} de una institución educativa {nivel} de San Pablo, {anio}",
    "Nivel de {habilidad} en niños de {edad} años de una institución educativa inicial de San Pablo, {anio}",
    "Estrategias para desarrollar {habilidad} en estudiantes de educación {nivel} de San Pablo, {anio}",
    "La {habilidad} y su relación con {habilidad2} en estudiantes de {grado} de una institución educativa de Cajamarca, {anio}",
    "Percepción docente sobre el uso de {habilidad} en el desarrollo de actividades de aprendizaje, San Pablo {anio}",
    "Mejorando {habilidad} en estudiantes de {grado} de una institución educativa de San Pablo, {anio}",
]

GRADOS = [
    "tres años", "cuatro años", "cinco años",
    "primer grado", "segundo grado", "tercer grado",
    "cuarto grado", "quinto grado", "sexto grado",
]

NIVELES_TXT = {
    "Educación Inicial": "inicial",
    "Educación Primaria": "primaria",
    "Educación Secundaria": "secundaria",
}

PDF_BYTES = (
    b"%PDF-1.4\n"
    b"1 0 obj<< /Type /Catalog /Pages 2 0 R >>endobj\n"
    b"2 0 obj<< /Type /Pages /Kids [3 0 R] /Count 1 >>endobj\n"
    b"3 0 obj<< /Type /Page /Parent 2 0 R /MediaBox [0 0 200 200] >>endobj\n"
    b"trailer<< /Size 4 /Root 1 0 R >>\n"
    b"%%EOF"
)


def dni_for(nombre_completo, prefix=70):
    checksum = zlib.crc32(nombre_completo.encode("utf-8")) % 900000
    return str(prefix * 1000000 + checksum).zfill(8)


def nombre_aleatorio():
    return f"{random.choice(NOMBRES)} {random.choice(APELLIDOS)} {random.choice(APELLIDOS)}"


class Command(BaseCommand):
    help = "Crea tesis de ejemplo (publicadas) para probar /repositorios/."

    def add_arguments(self, parser):
        parser.add_argument(
            "--count",
            type=int,
            default=50,
            help="Cantidad de tesis a crear (por defecto 50).",
        )

    def handle(self, *args, **options):
        total = options["count"]

        palabras_pool = [
            PalabraClave.objects.get_or_create(nombre=habilidad.capitalize())[0]
            for habilidad in HABILIDADES
        ]

        asesores_pool = []
        for _ in range(10):
            nombre = nombre_aleatorio()
            asesor, _ = Asesor.objects.get_or_create(
                dni=dni_for(nombre, prefix=71),
                defaults={"nombre_completo": nombre},
            )
            asesores_pool.append(asesor)

        creadas = 0

        for _ in range(total):
            habilidad = random.choice(HABILIDADES)
            habilidad2 = random.choice([h for h in HABILIDADES if h != habilidad])
            programa = random.choice(PROGRAMAS)
            nivel = NIVELES_TXT[programa]
            grado = random.choice(GRADOS)
            edad = random.choice(["tres", "cuatro", "cinco"])
            anio = random.randint(2021, 2026)

            titulo = random.choice(TITULO_TEMPLATES).format(
                habilidad=habilidad,
                habilidad_cap=habilidad.capitalize(),
                habilidad2=habilidad2,
                grado=grado,
                nivel=nivel,
                edad=edad,
                anio=anio,
            )

            autores = []
            for _ in range(random.choice([1, 1, 2])):
                nombre = nombre_aleatorio()
                autor, _ = Autor.objects.get_or_create(
                    dni=dni_for(nombre, prefix=70),
                    defaults={"nombre_completo": nombre},
                )
                autores.append(autor)

            fecha_pub = date(anio, random.randint(1, 12), random.randint(1, 28))

            tesis = Tesis(
                titulo=titulo,
                resumen=(
                    f"La presente investigación tuvo como objetivo analizar {habilidad} "
                    f"en estudiantes de {programa.lower()} de una institución educativa "
                    f"de San Pablo, Cajamarca, {anio}. Se desarrolló bajo un enfoque "
                    f"cuantitativo, con un diseño descriptivo, aplicando instrumentos "
                    f"validados para la recolección de datos."
                ),
                grado_academico=f"Título de Profesor de {programa}",
                programa_academico=programa,
                idioma="spa",
                estado="publicado",
                derechos_acceso="info:eu-repo/semantics/openAccess",
                fecha_publicacion=fecha_pub,
                fecha_disponibilidad=fecha_pub,
            )

            tesis.archivo_pdf.save(
                f"seed_tesis_{dni_for(titulo)}.pdf",
                ContentFile(PDF_BYTES),
                save=False,
            )

            tesis.save()
            tesis.autores.set(autores)

            if random.random() < 0.7:
                tesis.asesores.set([random.choice(asesores_pool)])

            tesis.palabras_clave.set(random.sample(palabras_pool, k=random.randint(2, 4)))

            creadas += 1

        self.stdout.write(
            self.style.SUCCESS(
                f"Se crearon {creadas} tesis publicadas de prueba en /repositorios/."
            )
        )

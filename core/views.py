from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.cache import cache

from investigacion.models import Tesis

import requests
import re
from bs4 import BeautifulSoup

from sickle import Sickle
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from lxml import etree
import urllib3
import io


PTE_ENTIDAD_ID = 37929
PTE_BASE_URL = "https://www.transparencia.gob.pe"

PTE_TEMAS_CONFIG = [
    {
        "key": "datos_generales",
        "anchor": "datos-generales",
        "nombre": "Datos Generales",
        "id_tema": 1,
        "url_path": "enlaces/pte_transparencia_enlaces.aspx",
        "icono": "🏛️",
        "activo": True,
    },
    {
        "key": "planeamiento",
        "anchor": "planeamiento",
        "nombre": "Planeamiento y Organización",
        "id_tema": 5,
        "url_path": "enlaces/pte_transparencia_enlaces.aspx",
        "icono": "🗂️",
        "activo": False,
    },
    {
        "key": "presupuesto",
        "anchor": "presupuesto",
        "nombre": "Presupuesto",
        "id_tema": 19,
        "url_path": "reportes_directos/pte_transparencia_info_finan.aspx",
        "icono": "💳",
        "activo": False,
    },
    {
        "key": "proyectos",
        "anchor": "proyectos",
        "nombre": "Proyectos de Inversión e Infobras",
        "id_tema": 26,
        "url_path": "reportes_directos/pte_transparencia_proyectos.aspx",
        "icono": "👷",
        "activo": False,
    },
    {
        "key": "personal",
        "anchor": "personal",
        "nombre": "Personal",
        "id_tema": 32,
        "url_path": "personal/pte_transparencia_personal_inicio.aspx",
        "icono": "👥",
        "activo": False,
    },
    {
        "key": "contratacion",
        "anchor": "contratacion",
        "nombre": "Contratación de bienes y servicios",
        "id_tema": 34,
        "url_path": "contrataciones/pte_transparencia_contrataciones.aspx",
        "icono": "📝",
        "activo": False,
    },
    {
        "key": "actividades",
        "anchor": "actividades",
        "nombre": "Actividades oficiales",
        "id_tema": None,
        "url_path": None,
        "icono": "🗓️",
        "activo": False,
    },
    {
        "key": "acceso_informacion",
        "anchor": "acceso-informacion",
        "nombre": "Acceso a la información",
        "id_tema": 49,
        "url_path": "reportes_directos/pep_transparencia_acceso_informacion.aspx",
        "icono": "📰",
        "activo": False,
    },
    {
        "key": "registro_visitas",
        "anchor": "registro-visitas",
        "nombre": "Registro de visitas",
        "id_tema": None,
        "url_path": None,
        "icono": "🚪",
        "activo": False,
    },
]

ARTICULO_42_ITEMS = [
    {
        "titulo": "Relación de estudiantes becados",
        "icono": "🎓",
        "url": "https://drive.google.com/drive/folders/1lUyFz2fr6UWlSWzjsyzVU2OJVJs9bd_S",
    },
    {
        "titulo": "Tasas, montos de pensiones, otros pagos",
        "icono": "💰",
        "url": "https://drive.google.com/drive/folders/16FbMcQPSvLue6RKB49kdIoF_2KXfQdOu",
    },
    {
        "titulo": "Proyectos de investigación-gastos",
        "icono": "📘",
        "url": "https://drive.google.com/drive/folders/1gdFGKnsM0IIzpC_dsEHhuVGT1rY0deuK",
    },
    {
        "titulo": "Conformación del cuerpo docente",
        "icono": "👥",
        "url": "https://drive.google.com/drive/folders/1Ms-Am9PGeB1ZYOQFJ0gp681DJ3rfZmrM?usp=sharing",
    },
    {
        "titulo": "Ingresantes y matriculados por año",
        "icono": "🧑‍🎓",
        "url": "https://drive.google.com/drive/folders/1MerrXTatEc0KHtWZijYgBJZwTM6jGHgc",
    },
    {
        "titulo": "Programas y horarios de estudios",
        "icono": "📅",
        "url": "https://drive.google.com/drive/folders/1KFWRbTaJGik4rAXmVJL1w_Ku0b4moA0S",
    },
    {
        "titulo": "Vigencia del licenciamiento",
        "icono": "🏛️",
        "url": "https://drive.google.com/drive/folders/1Ms-Am9PGeB1ZYOQFJ0gp681DJ3rfZmrM?usp=sharing",
    },
    {
        "titulo": "Reglamento institucional",
        "icono": "📖",
        "url": "https://drive.google.com/drive/folders/1ybhKsCF5noX0i3KkJDD-pVtXe82_ZSpg",
    },
    {
        "titulo": "Inversiones, reinversiones",
        "icono": "🏗️",
        "url": "https://drive.google.com/drive/folders/1z7cMAP-LIaCrWKW_NVyh1J9a0LWal7Yi",
    },
    {
        "titulo": "Texto Único de Procedimientos",
        "icono": "📄",
        "url": "https://drive.google.com/drive/folders/1wUqP9i6fibH09x_ShZjxii38pKI8-Uuz",
    },
]


def home(request):
    tesis_locales = (
        Tesis.objects
        .filter(estado='publicado')
        .prefetch_related('autores')
        .order_by('-fecha_registro')[:6]
    )

    return render(request, 'index.html', {
        'tesis_locales': tesis_locales,
        'mostrar_boton_ver_mas': True,
        'template_padre': 'investigacion/vacio.html'
    })


@login_required
def dashboard_view(request):
    total_tesis = Tesis.objects.count()
    tesis_pendientes = Tesis.objects.filter(estado='pendiente').count()

    return render(request, 'dashboard.html', {
        'total_tesis': total_tesis,
        'tesis_pendientes': tesis_pendientes,
        'template_padre': 'investigacion/vacio.html'
    })


def auth_view(request):
    if request.user.is_authenticated:
        return redirect('dashboard')

    if request.method == 'POST':
        u = request.POST.get('username')
        p = request.POST.get('password')

        user = authenticate(request, username=u, password=p)

        if user is not None:
            login(request, user)
            messages.success(request, f"Bienvenido de nuevo, {u}")
            return redirect('dashboard')

        messages.error(request, "Credenciales incorrectas. Inténtalo de nuevo.")

    return render(request, 'core/login.html')


def logout_view(request):
    logout(request)
    messages.info(request, "Has cerrado sesión correctamente.")
    return redirect('login')


def modal_content(request, modal_id):
    return render(request, f'modals/{modal_id}.html')


def construir_url_pte_tema(config):
    if not config.get("id_tema") or not config.get("url_path"):
        return (
            f"{PTE_BASE_URL}/enlaces/"
            f"pte_transparencia_enlaces.aspx?id_entidad={PTE_ENTIDAD_ID}"
        )

    return (
        f"{PTE_BASE_URL}/{config['url_path']}"
        f"?id_entidad={PTE_ENTIDAD_ID}"
        f"&id_tema={config['id_tema']}&ver="
    )


def extraer_url_real_pte(href):
    if not href:
        return None

    href = href.strip()

    if href.startswith("http://") or href.startswith("https://"):
        return href

    match = re.search(r"pte_js_enviar_Link\((.*?)\)", href)

    if match:
        contenido = match.group(1)
        partes = re.findall(r"'([^']*)'", contenido)

        if len(partes) >= 2:
            return partes[1]

    if href.startswith("../"):
        return f"{PTE_BASE_URL}/{href.replace('../', '')}"

    if href.startswith("/"):
        return f"{PTE_BASE_URL}{href}"

    return None


def limpiar_titulo_pte(texto):
    texto = re.sub(r"\s+", " ", texto or "").strip()
    texto = texto.replace("ARTICULO", "Artículo")
    return texto


def detectar_icono_por_titulo(titulo):
    texto = titulo.lower()

    if "directorio" in texto or "personal" in texto or "servidor" in texto:
        return "users"

    if "ley" in texto or "decreto" in texto or "resolución" in texto or "norma" in texto:
        return "scale"

    if "dirección" in texto or "entidad" in texto:
        return "building-library"

    if "presupuesto" in texto or "finan" in texto:
        return "currency-dollar"

    if "horario" in texto or "actividad" in texto:
        return "calendar-days"

    if "reglamento" in texto or "tupa" in texto:
        return "clipboard-document-list"

    return "document-text"

def es_link_footer_gobpe(titulo, url):
    texto = (titulo or "").lower()
    link = (url or "").lower()

    categorias_footer = [
        "accesibilidad e inclusión",
        "administración pública",
        "agricultura, ganadería y pesca",
        "arte, deporte y cultura",
        "ciencia, tecnología e innovación",
        "comercio, negocio y emprendimiento",
        "defensa, seguridad y justicia",
        "derechos humanos",
        "economía y finanzas",
        "educación",
        "energía y minas",
        "gestión municipal",
        "identidad, nacimiento, matrimonio y defunción",
        "infraestructura, comunicaciones y servicios públicos",
        "inmuebles y vivienda",
        "medio ambiente",
        "migración, turismo y viajes",
        "otros",
        "participación ciudadana",
        "programas y organizaciones sociales",
        "salud",
        "trabajo y pensiones",
        "transformación digital",
        "transparencia e integridad",
        "transporte y vehículos",
        "tributación",
        "sobre el estado peruano",
        "¿qué es gob.pe?",
        "política de privacidad",
    ]

    if any(cat in texto for cat in categorias_footer):
        return True

    if "gob.pe/busquedas?categoria" in link:
        return True

    return False

def obtener_links_pte_por_tema(config):
    if not config.get("id_tema") or not config.get("url_path"):
        return []

    cache_key = f"pte_{PTE_ENTIDAD_ID}_{config['key']}"
    data = cache.get(cache_key)

    if data is not None:
        return data

    url = construir_url_pte_tema(config)
    enlaces = []
    vistos = set()

    try:
        response = requests.get(
            url,
            timeout=20,
            headers={
                "User-Agent": (
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) "
                    "Chrome/120.0 Safari/537.36"
                )
            }
        )
        response.raise_for_status()

        soup = BeautifulSoup(response.text, "html.parser")
        grupo_actual = config["nombre"]

        for tag in soup.find_all(["h4", "li", "a"]):
            if tag.name == "h4":
                grupo = limpiar_titulo_pte(tag.get_text(" ", strip=True))
                if grupo:
                    grupo_actual = grupo.title()

            if tag.name != "a":
                continue

            titulo = limpiar_titulo_pte(tag.get_text(" ", strip=True))
            href = tag.get("href", "")
            url_real = extraer_url_real_pte(href)
            
            if not titulo or not url_real:
                continue
            
            if es_link_footer_gobpe(titulo, url_real):
                continue


            titulo_lower = titulo.lower()

            if titulo_lower in [
                "datos generales",
                "directorio",
                "marco legal",
                "dirección de la entidad",
                "normativa de transparencia y acceso a la información pública",
                "planeamiento y organización",
                "presupuesto",
                "proyectos de inversión e infobras",
                "personal",
                "contratación de bienes y servicios",
                "actividades oficiales",
                "acceso a la información",
                "registro de visitas",
            ]:
                continue

            clave = f"{titulo_lower}|{url_real}"

            if clave in vistos:
                continue

            vistos.add(clave)

            enlaces.append({
                "titulo": titulo,
                "url": url_real,
                "grupo": grupo_actual,
                "icono": detectar_icono_por_titulo(titulo),
                "tema": config["key"],
                "tema_nombre": config["nombre"],
                "origen": "PTE oficial",
            })

        cache.set(cache_key, enlaces, 60 * 60 * 6)
        return enlaces

    except Exception:
        cache.set(cache_key, [], 60 * 10)
        return []


def portal_transparencia(request):
    responsable = {
        "institucion": "INSTITUTO DE EDUCACIÓN SUPERIOR PEDAGÓGICO PÚBLICO 13 DE JULIO DE 1882",
        "siglas": "IESPP 13 JULIO 1882",
        "responsable_portal": "OSCAR ORLANDO SORIANO PALOMINO",
        "nombramiento_portal": "RD N° 043 - 2022 - DRECAJ/DG - IESPP",
        "correo_portal": "osoriano@13dejuliode1882sp.edu.pe",
        "telefono_portal": "948275153",
        "responsable_acceso": "Por actualizar",
        "nombramiento_acceso": "Información pendiente de actualización",
        "correo_acceso": "-",
        "telefono_acceso": "-",
        "director_general": "OSCAR ORLANDO SORIANO PALOMINO",
        "portal_oficial": (
            f"{PTE_BASE_URL}/enlaces/"
            f"pte_transparencia_enlaces.aspx?id_entidad={PTE_ENTIDAD_ID}"
        ),
    }

    secciones_pte = []

    for config in PTE_TEMAS_CONFIG:
        links = obtener_links_pte_por_tema(config)
        secciones_pte.append({
            "key": config["key"],
            "anchor": config["anchor"],
            "nombre": config["nombre"],
            "icono": config["icono"],
            "activo": config["activo"],
            "links": links,
            "url_oficial": construir_url_pte_tema(config),
        })

    directorio_items = []
    marco_legal_items = []

    for seccion in secciones_pte:
        for item in seccion["links"]:
            grupo = item.get("grupo", "").lower()
            titulo = item.get("titulo", "").lower()

            if (
                "directorio" in grupo
                or "dirección" in titulo
                or "servidores" in titulo
                or "personal docente" in titulo
            ):
                directorio_items.append(item)

            elif (
                "marco legal" in grupo
                or "ley" in titulo
                or "decreto" in titulo
                or "resolución" in titulo
                or "norma" in titulo
            ):
                marco_legal_items.append(item)

    if not directorio_items:
        directorio_items = [
            {
                "titulo": "Dirección institucional",
                "url": "https://13dejuliode1882sp.edu.pe/",
                "grupo": "Dirección de la entidad",
                "origen": "Respaldo manual",
            },
            {
                "titulo": "Directorio del personal docente nombrado del IESPP 13 de Julio de 1882",
                "url": "https://www.gob.pe/institucion/20202096582/funcionarios/",
                "grupo": "Servidores civiles y datos de contacto",
                "origen": "Respaldo manual",
            },
        ]

    if not marco_legal_items:
        marco_legal_items = [
            {
                "titulo": "Norma de creación de la entidad",
                "url": "https://drive.google.com/file/d/1Ek7zhCx8jqhhYDNC33RS-hFoNX6kUCyF/view?usp=sharing",
                "grupo": "Marco Legal",
                "origen": "Respaldo manual",
            },
            {
                "titulo": "Ley N° 27806 - Transparencia y Acceso a la Información Pública",
                "url": "https://spij.minjus.gob.pe/spij-ext-web/#/detallenorma/H829967",
                "grupo": "Marco Legal",
                "origen": "Respaldo manual",
            },
            {
                "titulo": "Ley N° 27444 - Procedimiento Administrativo General",
                "url": "https://spij.minjus.gob.pe/spij-ext-web/#/detallenorma/H805476",
                "grupo": "Marco Legal",
                "origen": "Respaldo manual",
            },
            {
                "titulo": "Resolución Directoral N° 066-2025-JUS/DGTAIPD",
                "url": "https://www.gob.pe/institucion/antaip/normas-legales/7244059-066-2025-jus-dgtaipd",
                "grupo": "Marco Legal",
                "origen": "Respaldo manual",
            },
        ]

    temas = [
        {
            "nombre": config["nombre"],
            "icono": config["icono"],
            "activo": config["activo"],
            "anchor": config["anchor"],
        }
        for config in PTE_TEMAS_CONFIG
    ]

    fuente_dinamica = any(seccion["links"] for seccion in secciones_pte)

    return render(request, "portal.html", {
        "responsable": responsable,
        "temas": temas,
        "articulo_42_items": ARTICULO_42_ITEMS,
        "secciones_pte": secciones_pte,
        "directorio_items": directorio_items,
        "marco_legal_items": marco_legal_items,
        "fuente_dinamica": fuente_dinamica,
    })
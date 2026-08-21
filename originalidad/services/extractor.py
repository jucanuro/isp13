"""
Servicio para la extracción limpia de texto desde archivos binarios (PDF y DOCX).
"""
import io
from typing import Union
from django.core.files.storage import default_storage


def extraer_texto_desde_archivo(archivo_input: Union[str, object]) -> str:
    """
    Extrae texto plano desde un FileField o ruta de archivo en formato PDF o DOCX.
    """
    if isinstance(archivo_input, str):
        file_obj = default_storage.open(archivo_input, 'rb')
        filename = archivo_input
    else:
        file_obj = archivo_input
        filename = getattr(archivo_input, 'name', '')

    filename_lower = filename.lower()
    texto = ""

    try:
        if filename_lower.endswith('.pdf'):
            texto = _extraer_pdf(file_obj)
        elif filename_lower.endswith('.docx'):
            texto = _extraer_docx(file_obj)
        else:
            raise ValueError(f"Formato no soportado para la extracción de texto: {filename}")
    finally:
        if isinstance(archivo_input, str):
            file_obj.close()

    return _limpiar_texto(texto)


def _extraer_pdf(file_obj) -> str:
    """Extrae texto usando pypdf."""
    try:
        import pypdf
        reader = pypdf.PdfReader(file_obj)
        paginas = []
        for page in reader.pages:
            t = page.extract_text()
            if t:
                paginas.append(t)
        return "\n".join(paginas)
    except ImportError:
        raise ImportError("Se requiere la librería 'pypdf' para procesar archivos PDF.")


def _extraer_docx(file_obj) -> str:
    """Extrae texto usando python-docx."""
    try:
        import docx
        doc = docx.Document(file_obj)
        return "\n".join([p.text for p in doc.paragraphs if p.text.strip()])
    except ImportError:
        raise ImportError("Se requiere la librería 'python-docx' para procesar archivos DOCX.")


def _limpiar_texto(texto: str) -> str:
    """Normaliza saltos de línea y espacios en blanco excesivos."""
    if not texto:
        return ""
    lineas = [linea.strip() for linea in texto.splitlines() if linea.strip()]
    return "\n".join(lineas)
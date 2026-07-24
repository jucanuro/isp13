from datetime import date, datetime, timezone as datetime_timezone
import re

from django.http import HttpResponse, HttpResponseNotAllowed
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from lxml import etree

from .models import Tesis
from .oai import build_oai_dc


# ============================================================
# CONFIGURACIÓN GENERAL OAI-PMH
# ============================================================

OAI_NS = "http://www.openarchives.org/OAI/2.0/"
XSI_NS = "http://www.w3.org/2001/XMLSchema-instance"
OAI_SCHEMA = "http://www.openarchives.org/OAI/2.0/OAI-PMH.xsd"

OAI_DC_NS = "http://www.openarchives.org/OAI/2.0/oai_dc/"
OAI_DC_SCHEMA = (
    "http://www.openarchives.org/OAI/2.0/oai_dc/oai_dc.xsd"
)

REPOSITORY_NAME = (
    "Repositorio Institucional IESPP 13 de Julio de 1882"
)

ADMIN_EMAIL = "repositorio@13dejuliode1882sp.edu.pe"

IDENTIFIER_AUTHORITY = (
    "repositorio.13dejuliode1882sp.edu.pe"
)

SUPPORTED_METADATA_PREFIX = "oai_dc"

SET_SPEC = "tesis"
SET_NAME = "Tesis y trabajos de investigación"


SUPPORTED_VERBS = {
    "Identify",
    "ListMetadataFormats",
    "ListSets",
    "ListIdentifiers",
    "ListRecords",
    "GetRecord",
}


ALLOWED_ARGUMENTS = {
    "Identify": {
        "verb",
    },
    "ListMetadataFormats": {
        "verb",
        "identifier",
    },
    "ListSets": {
        "verb",
        "resumptionToken",
    },
    "ListIdentifiers": {
        "verb",
        "metadataPrefix",
        "from",
        "until",
        "set",
        "resumptionToken",
    },
    "ListRecords": {
        "verb",
        "metadataPrefix",
        "from",
        "until",
        "set",
        "resumptionToken",
    },
    "GetRecord": {
        "verb",
        "identifier",
        "metadataPrefix",
    },
}


# ============================================================
# FUNCIONES GENERALES XML
# ============================================================

def oai_tag(name):
    """
    Crea una etiqueta XML dentro del namespace oficial OAI-PMH.
    """
    return f"{{{OAI_NS}}}{name}"


def utc_now_text():
    """
    Fecha y hora actual en UTC para responseDate.
    """
    return timezone.now().astimezone(
        datetime_timezone.utc
    ).strftime("%Y-%m-%dT%H:%M:%SZ")


def get_base_url(request):
    """
    Devuelve la URL del endpoint sin los parámetros GET.

    En producción debe devolver algo como:
    https://repositorio.13dejuliode1882sp.edu.pe/oai/
    """
    return request.build_absolute_uri(request.path)


def create_oai_root():
    """
    Construye la raíz XML OAI-PMH con namespaces y esquema XSD.
    """
    root = etree.Element(
        oai_tag("OAI-PMH"),
        nsmap={
            None: OAI_NS,
            "xsi": XSI_NS,
        },
    )

    root.set(
        f"{{{XSI_NS}}}schemaLocation",
        f"{OAI_NS} {OAI_SCHEMA}",
    )

    etree.SubElement(
        root,
        oai_tag("responseDate"),
    ).text = utc_now_text()

    return root


def add_request_element(
    root,
    request,
    params,
    include_attributes=True,
):
    """
    Agrega el elemento request exigido por OAI-PMH.
    """
    request_element = etree.SubElement(
        root,
        oai_tag("request"),
    )

    request_element.text = get_base_url(request)

    if include_attributes:
        for key in params.keys():
            value = params.get(key)

            if value is not None:
                request_element.set(key, value)

    return request_element


def xml_response(root, status=200):
    """
    Convierte el árbol XML en una respuesta HTTP.
    """
    xml_content = etree.tostring(
        root,
        pretty_print=True,
        xml_declaration=True,
        encoding="UTF-8",
    )

    return HttpResponse(
        xml_content,
        content_type="application/xml; charset=utf-8",
        status=status,
    )


def oai_error(request, params, code, message):
    """
    Genera un error dentro de una respuesta XML OAI-PMH válida.
    """
    root = create_oai_root()

    # En badVerb y badArgument el protocolo exige que
    # request no exponga atributos.
    include_attributes = code not in {
        "badVerb",
        "badArgument",
    }

    add_request_element(
        root,
        request,
        params,
        include_attributes=include_attributes,
    )

    error = etree.SubElement(
        root,
        oai_tag("error"),
    )

    error.set("code", code)
    error.text = message

    # Los errores OAI se devuelven dentro del XML.
    return xml_response(root, status=200)


# ============================================================
# IDENTIFICADORES Y FECHAS
# ============================================================

def get_published_queryset():
    """
    Solo expone registros que ya se encuentren publicados.
    """
    return Tesis.objects.filter(estado="publicado")


def get_record_date(tesis):
    """
    Obtiene la fecha que se usará como datestamp OAI.

    Cuando agreguemos fecha_actualizacion al modelo, tendrá prioridad.
    """
    fields = (
        "fecha_actualizacion",
        "fecha_publicacion",
        "fecha_registro",
    )

    for field_name in fields:
        value = getattr(tesis, field_name, None)

        if not value:
            continue

        if isinstance(value, datetime):
            if timezone.is_aware(value):
                return value.astimezone(
                    datetime_timezone.utc
                ).date()

            return value.date()

        if isinstance(value, date):
            return value

    return timezone.localdate()


def get_record_datestamp(tesis):
    """
    Datestamp con granularidad diaria.
    """
    return get_record_date(tesis).isoformat()


def get_record_identifier(tesis):
    """
    Identificador persistente usado por OAI-PMH.
    """
    return (
        f"oai:{IDENTIFIER_AUTHORITY}:tesis/{tesis.pk}"
    )


def extract_record_pk(identifier):
    """
    Extrae el ID de la tesis desde un identificador OAI.

    También reconoce temporalmente el formato anterior:
    oai:isp13:tesis/ID
    """
    if not identifier:
        return None

    patterns = (
        (
            rf"^oai:"
            rf"{re.escape(IDENTIFIER_AUTHORITY)}"
            rf":tesis/(\d+)$"
        ),
        r"^oai:isp13:tesis/(\d+)$",
    )

    for pattern in patterns:
        match = re.fullmatch(pattern, identifier)

        if match:
            return int(match.group(1))

    return None


def get_published_record(identifier):
    """
    Busca una tesis publicada utilizando su identificador OAI.
    """
    record_pk = extract_record_pk(identifier)

    if record_pk is None:
        return None

    return get_published_queryset().filter(
        pk=record_pk
    ).first()


def append_header(parent, tesis):
    """
    Agrega el encabezado OAI de un registro.
    """
    header = etree.SubElement(
        parent,
        oai_tag("header"),
    )

    etree.SubElement(
        header,
        oai_tag("identifier"),
    ).text = get_record_identifier(tesis)

    etree.SubElement(
        header,
        oai_tag("datestamp"),
    ).text = get_record_datestamp(tesis)

    etree.SubElement(
        header,
        oai_tag("setSpec"),
    ).text = SET_SPEC

    return header


def append_record(parent, tesis, request):
    """
    Agrega encabezado y metadatos Dublin Core.
    """
    record = etree.SubElement(
        parent,
        oai_tag("record"),
    )

    append_header(record, tesis)

    metadata = etree.SubElement(
        record,
        oai_tag("metadata"),
    )

    metadata.append(
        build_oai_dc(tesis, request)
    )

    return record


# ============================================================
# VALIDACIÓN DE FECHAS Y LISTADOS
# ============================================================

def parse_oai_date(value):
    """
    Valida fechas OAI con formato YYYY-MM-DD.
    """
    if not value:
        return None

    try:
        parsed_date = date.fromisoformat(value)
    except (TypeError, ValueError):
        return None

    if parsed_date.isoformat() != value:
        return None

    return parsed_date


def validate_list_request(request, params):
    """
    Valida los argumentos usados en ListRecords
    y ListIdentifiers.
    """
    resumption_token = params.get("resumptionToken")

    if resumption_token is not None:
        if len(params) != 2:
            return None, oai_error(
                request,
                params,
                "badArgument",
                (
                    "resumptionToken debe ser el único "
                    "argumento además de verb."
                ),
            )

        # Por ahora no se emiten tokens porque la cantidad
        # de registros todavía no requiere paginación OAI.
        return None, oai_error(
            request,
            params,
            "badResumptionToken",
            (
                "El resumptionToken es inválido "
                "o ya expiró."
            ),
        )

    metadata_prefix = params.get("metadataPrefix")

    if not metadata_prefix:
        return None, oai_error(
            request,
            params,
            "badArgument",
            (
                "Falta el argumento obligatorio "
                "metadataPrefix."
            ),
        )

    if metadata_prefix != SUPPORTED_METADATA_PREFIX:
        return None, oai_error(
            request,
            params,
            "cannotDisseminateFormat",
            (
                "El formato de metadatos solicitado "
                "no está disponible."
            ),
        )

    set_spec = params.get("set")

    if set_spec and set_spec != SET_SPEC:
        return None, oai_error(
            request,
            params,
            "noRecordsMatch",
            (
                "No existen registros para "
                "el conjunto solicitado."
            ),
        )

    from_value = params.get("from")
    until_value = params.get("until")

    from_date = (
        parse_oai_date(from_value)
        if from_value
        else None
    )

    until_date = (
        parse_oai_date(until_value)
        if until_value
        else None
    )

    if from_value and from_date is None:
        return None, oai_error(
            request,
            params,
            "badArgument",
            (
                "El argumento from debe utilizar "
                "el formato YYYY-MM-DD."
            ),
        )

    if until_value and until_date is None:
        return None, oai_error(
            request,
            params,
            "badArgument",
            (
                "El argumento until debe utilizar "
                "el formato YYYY-MM-DD."
            ),
        )

    if (
        from_date
        and until_date
        and from_date > until_date
    ):
        return None, oai_error(
            request,
            params,
            "badArgument",
            (
                "El argumento from no puede ser "
                "posterior al argumento until."
            ),
        )

    records = []

    for tesis in get_published_queryset():
        current_date = get_record_date(tesis)

        if from_date and current_date < from_date:
            continue

        if until_date and current_date > until_date:
            continue

        records.append(tesis)

    records.sort(
        key=lambda item: (
            get_record_date(item),
            item.pk,
        )
    )

    if not records:
        return None, oai_error(
            request,
            params,
            "noRecordsMatch",
            (
                "No existen registros que coincidan "
                "con los argumentos enviados."
            ),
        )

    return records, None


# ============================================================
# ENDPOINT PRINCIPAL
# ============================================================

@csrf_exempt
def oai_endpoint(request):
    """
    Endpoint principal OAI-PMH.

    Acepta solicitudes GET y POST.
    """
    if request.method == "GET":
        params = request.GET

    elif request.method == "POST":
        params = request.POST

    else:
        return HttpResponseNotAllowed(
            ["GET", "POST"]
        )

    repeated_arguments = [
        key
        for key, values in params.lists()
        if len(values) != 1
    ]

    if repeated_arguments:
        return oai_error(
            request,
            params,
            "badArgument",
            (
                "La solicitud contiene "
                "argumentos repetidos."
            ),
        )

    verb = params.get("verb")

    if not verb or verb not in SUPPORTED_VERBS:
        return oai_error(
            request,
            params,
            "badVerb",
            (
                "El verbo OAI-PMH no existe "
                "o no fue enviado."
            ),
        )

    unknown_arguments = (
        set(params.keys())
        - ALLOWED_ARGUMENTS[verb]
    )

    if unknown_arguments:
        return oai_error(
            request,
            params,
            "badArgument",
            (
                "La solicitud contiene "
                "argumentos no permitidos."
            ),
        )

    handlers = {
        "Identify": oai_identify,
        "ListMetadataFormats": (
            oai_list_metadata_formats
        ),
        "ListSets": oai_list_sets,
        "ListIdentifiers": oai_list_identifiers,
        "ListRecords": oai_list_records,
        "GetRecord": oai_get_record,
    }

    return handlers[verb](request, params)


# ============================================================
# VERBO: IDENTIFY
# ============================================================

def oai_identify(request, params):
    root = create_oai_root()

    add_request_element(
        root,
        request,
        params,
    )

    identify = etree.SubElement(
        root,
        oai_tag("Identify"),
    )

    etree.SubElement(
        identify,
        oai_tag("repositoryName"),
    ).text = REPOSITORY_NAME

    etree.SubElement(
        identify,
        oai_tag("baseURL"),
    ).text = get_base_url(request)

    etree.SubElement(
        identify,
        oai_tag("protocolVersion"),
    ).text = "2.0"

    etree.SubElement(
        identify,
        oai_tag("adminEmail"),
    ).text = ADMIN_EMAIL

    available_dates = [
        get_record_date(tesis)
        for tesis in get_published_queryset()
    ]

    earliest_date = (
        min(available_dates)
        if available_dates
        else timezone.localdate()
    )

    etree.SubElement(
        identify,
        oai_tag("earliestDatestamp"),
    ).text = earliest_date.isoformat()

    etree.SubElement(
        identify,
        oai_tag("deletedRecord"),
    ).text = "no"

    etree.SubElement(
        identify,
        oai_tag("granularity"),
    ).text = "YYYY-MM-DD"

    return xml_response(root)


# ============================================================
# VERBO: LISTMETADATAFORMATS
# ============================================================

def oai_list_metadata_formats(request, params):
    identifier = params.get("identifier")

    if (
        identifier
        and get_published_record(identifier) is None
    ):
        return oai_error(
            request,
            params,
            "idDoesNotExist",
            (
                "El identificador solicitado "
                "no existe."
            ),
        )

    root = create_oai_root()

    add_request_element(
        root,
        request,
        params,
    )

    list_formats = etree.SubElement(
        root,
        oai_tag("ListMetadataFormats"),
    )

    metadata_format = etree.SubElement(
        list_formats,
        oai_tag("metadataFormat"),
    )

    etree.SubElement(
        metadata_format,
        oai_tag("metadataPrefix"),
    ).text = SUPPORTED_METADATA_PREFIX

    etree.SubElement(
        metadata_format,
        oai_tag("schema"),
    ).text = OAI_DC_SCHEMA

    etree.SubElement(
        metadata_format,
        oai_tag("metadataNamespace"),
    ).text = OAI_DC_NS

    return xml_response(root)


# ============================================================
# VERBO: LISTSETS
# ============================================================

def oai_list_sets(request, params):
    if params.get("resumptionToken") is not None:
        return oai_error(
            request,
            params,
            "badResumptionToken",
            (
                "El resumptionToken es inválido "
                "o ya expiró."
            ),
        )

    root = create_oai_root()

    add_request_element(
        root,
        request,
        params,
    )

    list_sets = etree.SubElement(
        root,
        oai_tag("ListSets"),
    )

    set_element = etree.SubElement(
        list_sets,
        oai_tag("set"),
    )

    etree.SubElement(
        set_element,
        oai_tag("setSpec"),
    ).text = SET_SPEC

    etree.SubElement(
        set_element,
        oai_tag("setName"),
    ).text = SET_NAME

    return xml_response(root)


# ============================================================
# VERBO: LISTIDENTIFIERS
# ============================================================

def oai_list_identifiers(request, params):
    records, error = validate_list_request(
        request,
        params,
    )

    if error:
        return error

    root = create_oai_root()

    add_request_element(
        root,
        request,
        params,
    )

    list_identifiers = etree.SubElement(
        root,
        oai_tag("ListIdentifiers"),
    )

    for tesis in records:
        append_header(
            list_identifiers,
            tesis,
        )

    return xml_response(root)


# ============================================================
# VERBO: LISTRECORDS
# ============================================================

def oai_list_records(request, params):
    records, error = validate_list_request(
        request,
        params,
    )

    if error:
        return error

    root = create_oai_root()

    add_request_element(
        root,
        request,
        params,
    )

    list_records = etree.SubElement(
        root,
        oai_tag("ListRecords"),
    )

    for tesis in records:
        append_record(
            list_records,
            tesis,
            request,
        )

    return xml_response(root)


# ============================================================
# VERBO: GETRECORD
# ============================================================

def oai_get_record(request, params):
    identifier = params.get("identifier")
    metadata_prefix = params.get("metadataPrefix")

    if not identifier or not metadata_prefix:
        return oai_error(
            request,
            params,
            "badArgument",
            (
                "GetRecord requiere los argumentos "
                "identifier y metadataPrefix."
            ),
        )

    if metadata_prefix != SUPPORTED_METADATA_PREFIX:
        return oai_error(
            request,
            params,
            "cannotDisseminateFormat",
            (
                "El formato de metadatos solicitado "
                "no está disponible."
            ),
        )

    tesis = get_published_record(identifier)

    if tesis is None:
        return oai_error(
            request,
            params,
            "idDoesNotExist",
            (
                "El identificador solicitado "
                "no existe."
            ),
        )

    root = create_oai_root()

    add_request_element(
        root,
        request,
        params,
    )

    get_record = etree.SubElement(
        root,
        oai_tag("GetRecord"),
    )

    append_record(
        get_record,
        tesis,
        request,
    )

    return xml_response(root)
from lxml import etree


DC_NS = "http://purl.org/dc/elements/1.1/"
OAI_DC_NS = "http://www.openarchives.org/OAI/2.0/oai_dc/"
XSI_NS = "http://www.w3.org/2001/XMLSchema-instance"

NSMAP = {
    "oai_dc": OAI_DC_NS,
    "dc": DC_NS,
    "xsi": XSI_NS,
}


def clean_value(value):
    if value is None:
        return ""

    return str(value).strip()


def add_dc_element(parent, element_name, value):
    value = clean_value(value)

    if not value:
        return None

    element = etree.SubElement(
        parent,
        f"{{{DC_NS}}}{element_name}",
    )
    element.text = value

    return element


def add_unique_dc_elements(parent, element_name, values):
    added_values = set()

    for value in values:
        normalized_value = clean_value(value)

        if not normalized_value:
            continue

        comparable_value = normalized_value.casefold()

        if comparable_value in added_values:
            continue

        add_dc_element(
            parent,
            element_name,
            normalized_value,
        )

        added_values.add(comparable_value)


def get_publication_date(tesis):
    fecha_publicacion = getattr(
        tesis,
        "fecha_publicacion",
        None,
    )

    if fecha_publicacion:
        return fecha_publicacion.strftime("%Y-%m-%d")

    fecha_registro = getattr(
        tesis,
        "fecha_registro",
        None,
    )

    if fecha_registro:
        return fecha_registro.strftime("%Y-%m-%d")

    return ""


def get_thesis_type(tesis):
    thesis_type = clean_value(
        getattr(tesis, "tipo_tesis", "")
    )

    if not thesis_type:
        return ""

    return thesis_type.split("_", 1)[0]


def get_language(tesis):
    language = clean_value(
        getattr(tesis, "idioma", "")
    )

    return language or "spa"


def get_access_rights(tesis):
    return clean_value(
        getattr(tesis, "derechos_acceso", "")
    )


def get_license_uri(tesis):
    return clean_value(
        getattr(tesis, "licencia_uri", "")
    )


def get_persistent_identifier(tesis):
    return clean_value(
        getattr(
            tesis,
            "identificador_persistente",
            "",
        )
    )


def get_pdf_url(tesis, request):
    archivo_pdf = getattr(
        tesis,
        "archivo_pdf",
        None,
    )

    if not archivo_pdf:
        return ""

    try:
        return request.build_absolute_uri(
            archivo_pdf.url
        )
    except (ValueError, AttributeError):
        return ""


def get_file_format(tesis):
    archivo_pdf = getattr(
        tesis,
        "archivo_pdf",
        None,
    )

    if not archivo_pdf:
        return ""

    return "application/pdf"


def build_oai_dc(tesis, request):
    schema_location = (
        "http://www.openarchives.org/OAI/2.0/oai_dc/ "
        "http://www.openarchives.org/OAI/2.0/oai_dc.xsd"
    )

    dc = etree.Element(
        f"{{{OAI_DC_NS}}}dc",
        nsmap=NSMAP,
        attrib={
            f"{{{XSI_NS}}}schemaLocation": (
                schema_location
            )
        },
    )

    add_dc_element(
        dc,
        "title",
        getattr(tesis, "titulo", ""),
    )

    authors = tesis.autores.all()

    for author in authors:
        add_dc_element(
            dc,
            "creator",
            getattr(author, "nombre_completo", ""),
        )

    advisors = tesis.asesores.all()

    for advisor in advisors:
        add_dc_element(
            dc,
            "contributor",
            getattr(advisor, "nombre_completo", ""),
        )

    add_dc_element(
        dc,
        "description",
        getattr(tesis, "resumen", ""),
    )

    subject_values = [
        getattr(tesis, "ocde_nombre", ""),
    ]

    ocde_code = clean_value(
        getattr(tesis, "ocde_codigo", "")
    )

    if ocde_code:
        subject_values.append(
            f"OCDE {ocde_code}"
        )

    ocde_uri = clean_value(
        getattr(tesis, "ocde_uri", "")
    )

    if ocde_uri:
        subject_values.append(ocde_uri)

    keywords = getattr(
        tesis,
        "palabras_clave",
        None,
    )

    if keywords is not None:
        if hasattr(keywords, "all"):
            subject_values.extend(
                clean_value(
                    getattr(keyword, "nombre", keyword)
                )
                for keyword in keywords.all()
            )
        elif isinstance(keywords, str):
            subject_values.extend(
                keyword.strip()
                for keyword in keywords.split(",")
            )

    add_unique_dc_elements(
        dc,
        "subject",
        subject_values,
    )

    add_dc_element(
        dc,
        "publisher",
        getattr(
            tesis,
            "institucion_nombre",
            "",
        ),
    )

    add_dc_element(
        dc,
        "date",
        get_publication_date(tesis),
    )

    add_dc_element(
        dc,
        "type",
        get_thesis_type(tesis),
    )

    add_dc_element(
        dc,
        "format",
        get_file_format(tesis),
    )

    add_dc_element(
        dc,
        "language",
        get_language(tesis),
    )

    add_dc_element(
        dc,
        "rights",
        get_access_rights(tesis),
    )

    license_uri = get_license_uri(tesis)

    if license_uri:
        add_dc_element(
            dc,
            "rights",
            license_uri,
        )

    persistent_identifier = (
        get_persistent_identifier(tesis)
    )

    pdf_url = get_pdf_url(
        tesis,
        request,
    )

    add_unique_dc_elements(
        dc,
        "identifier",
        [
            persistent_identifier,
            pdf_url,
        ],
    )

    country = clean_value(
        getattr(
            tesis,
            "pais_publicacion",
            getattr(tesis, "pais", ""),
        )
    )

    if country:
        add_dc_element(
            dc,
            "coverage",
            country,
        )

    return dc
from lxml import etree

DC_NS = "http://purl.org/dc/elements/1.1/"
OAI_DC_NS = "http://www.openarchives.org/OAI/2.0/oai_dc/"
XSI_NS = "http://www.w3.org/2001/XMLSchema-instance"

NSMAP = {
    "oai_dc": OAI_DC_NS,
    "dc": DC_NS,
    "xsi": XSI_NS,
}

def build_oai_dc(tesis, request):
    schema_location = (
        "http://www.openarchives.org/OAI/2.0/oai_dc/ "
        "http://www.openarchives.org/OAI/2.0/oai_dc.xsd"
    )

    dc = etree.Element(
        "{%s}dc" % OAI_DC_NS,
        nsmap=NSMAP,
        attrib={"{%s}schemaLocation" % XSI_NS: schema_location},
    )

    etree.SubElement(dc, "{%s}title" % DC_NS).text = tesis.titulo
    etree.SubElement(dc, "{%s}description" % DC_NS).text = tesis.resumen

    if tesis.fecha_publicacion:
        etree.SubElement(dc, "{%s}date" % DC_NS).text = tesis.fecha_publicacion.strftime("%Y-%m-%d")

    clean_type = tesis.tipo_tesis.split("_")[0]
    etree.SubElement(dc, "{%s}type" % DC_NS).text = clean_type

    etree.SubElement(dc, "{%s}rights" % DC_NS).text = tesis.derechos_acceso
    etree.SubElement(dc, "{%s}language" % DC_NS).text = "spa"

    if tesis.ocde_codigo:
        etree.SubElement(dc, "{%s}subject" % DC_NS).text = f"OCDE:{tesis.ocde_codigo}"
    if tesis.ocde_nombre:
        etree.SubElement(dc, "{%s}subject" % DC_NS).text = tesis.ocde_nombre

    # PDF primero
    if tesis.archivo_pdf:
        etree.SubElement(dc, "{%s}identifier" % DC_NS).text = request.build_absolute_uri(tesis.archivo_pdf.url)

    for autor in tesis.autores.all():
        etree.SubElement(dc, "{%s}creator" % DC_NS).text = autor.nombre_completo
        etree.SubElement(dc, "{%s}identifier" % DC_NS).text = f"DNI:{autor.dni}"
        if autor.orcid:
            etree.SubElement(dc, "{%s}identifier" % DC_NS).text = autor.orcid

    etree.SubElement(dc, "{%s}publisher" % DC_NS).text = tesis.institucion_nombre
    etree.SubElement(dc, "{%s}identifier" % DC_NS).text = f"RUC:{tesis.institucion_ruc}"

    for asesor in tesis.asesores.all():
        etree.SubElement(dc, "{%s}contributor" % DC_NS).text = asesor.nombre_completo

    return dc

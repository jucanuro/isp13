from django.http import HttpResponse
from django.utils.timezone import now
from lxml import etree
from .models import Tesis
from .oai import build_oai_dc


def oai_endpoint(request):
    verb = request.GET.get("verb")

    if verb == "Identify":
        return oai_identify()

    if verb == "ListRecords":
        return oai_list_records(request)

    return HttpResponse(
        "<error code='badVerb'>Verbo OAI-PMH no soportado</error>",
        content_type="application/xml",
        status=400
    )


def oai_identify():
    root = etree.Element("OAI-PMH")
    etree.SubElement(root, "responseDate").text = now().strftime("%Y-%m-%dT%H:%M:%SZ")

    identify = etree.SubElement(root, "Identify")
    etree.SubElement(identify, "repositoryName").text = "Repositorio Institucional IESP 13 de Julio de 1882"
    etree.SubElement(identify, "baseURL").text = "https://repositorio.isp13.edu.pe/oai/"
    etree.SubElement(identify, "protocolVersion").text = "2.0"
    etree.SubElement(identify, "adminEmail").text = "repositorio@isp13.edu.pe"
    etree.SubElement(identify, "earliestDatestamp").text = "2024-01-01"
    etree.SubElement(identify, "deletedRecord").text = "no"
    etree.SubElement(identify, "granularity").text = "YYYY-MM-DD"

    return HttpResponse(
        etree.tostring(root, pretty_print=True, xml_declaration=True, encoding="UTF-8"),
        content_type="application/xml",
    )


def oai_list_records(request):
    metadata_prefix = request.GET.get("metadataPrefix")
    if metadata_prefix != "oai_dc":
        return HttpResponse(
            "<error code='cannotDisseminateFormat'>Formato no soportado</error>",
            content_type="application/xml",
            status=400
        )

    root = etree.Element("OAI-PMH")
    etree.SubElement(root, "responseDate").text = now().strftime("%Y-%m-%dT%H:%M:%SZ")

    list_records = etree.SubElement(root, "ListRecords")

    for tesis in Tesis.objects.filter(estado="publicado"):
        record = etree.SubElement(list_records, "record")

        header = etree.SubElement(record, "header")
        etree.SubElement(header, "identifier").text = f"oai:isp13:tesis/{tesis.id}"

        datestamp = (
            tesis.fecha_publicacion.strftime("%Y-%m-%d")
            if tesis.fecha_publicacion
            else tesis.fecha_registro.strftime("%Y-%m-%d")
        )
        etree.SubElement(header, "datestamp").text = datestamp

        metadata = etree.SubElement(record, "metadata")
        metadata.append(build_oai_dc(tesis, request))

    return HttpResponse(
        etree.tostring(root, pretty_print=True, xml_declaration=True, encoding="UTF-8"),
        content_type="application/xml",
    )

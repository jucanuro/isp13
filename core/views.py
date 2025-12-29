from django.shortcuts import render
import requests
from sickle import Sickle
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from lxml import etree
import urllib3
import io

def home(request):
    tesis_list = []
    # Cambiamos a la UNI, que es más estable para OAI-PMH externo
    url = 'https://repositorio.uni.edu.pe/oai/request'
    params = {'verb': 'ListRecords', 'metadataPrefix': 'oai_dc'}
    
    # Headers de un navegador real de Windows para que no nos redirija a HTML
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'application/xml, text/xml, */*'
    }
    
    try:
        response = requests.get(url, params=params, headers=headers, verify=False, timeout=20)
        
        # Si el contenido empieza con '<!', es que nos envió HTML y no XML
        if response.status_code == 200 and not response.content.strip().startswith(b'<!'):
            parser = etree.XMLParser(recover=True, remove_blank_text=True)
            xml_data = etree.fromstring(response.content, parser=parser)
            
            ns = {
                'oai': 'http://www.openarchives.org/OAI/2.0/',
                'dc': 'http://purl.org/dc/elements/1.1/'
            }
            
            records = xml_data.xpath('//oai:record', namespaces=ns)
            
            for i, record in enumerate(records):
                if i >= 6: break
                
                # Usamos local-name() para ignorar problemas de prefijos
                title = record.xpath('.//*[local-name()="title"]/text()')
                creator = record.xpath('.//*[local-name()="creator"]/text()')
                identifier = record.xpath('.//*[local-name()="identifier"]/text()')
                
                tesis_list.append({
                    'title': title[0] if title else 'Investigación UNI',
                    'author': creator[0] if creator else 'Autor Institucional',
                    'link': identifier[0] if identifier else '#',
                    'type': 'Tesis / Proyecto'
                })
        else:
            print("AVISO: El servidor envió HTML o está bloqueado. Usando datos locales.")
            # Datos de respaldo basados en la GUIA ALICIA
            tesis_list = [
                {'title': 'Implementación de Repositorios con DSpace 7', 'author': 'Unidad de Posgrado', 'link': '#', 'type': 'Guía Técnica'},
                {'title': 'Estudio de Interoperabilidad ALICIA 2.0', 'author': 'CONCYTEC', 'link': '#', 'type': 'Tesis'},
                {'title': 'Gestión de Metadatos en Educación Superior', 'author': 'Área de Investigación', 'link': '#', 'type': 'Artículo'}
            ]

    except Exception as e:
        print(f"!!! ERROR: {e}")
        tesis_list = None 

    return render(request, 'index.html', {'tesis': tesis_list})
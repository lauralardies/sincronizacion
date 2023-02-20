import asyncio
import aiohttp
from bs4 import BeautifulSoup
from urllib.parse import urlparse
from os import sep

async def wget(session, uri):
    async with session.get(uri) as response:
        if response.status != 200:
            return None
        if response.content_type.startswith('text/'):
            return await response.text()
        else:
            return await response.read()

async def download(session, uri):
    content = await wget(session, uri)
    if content is None:
        return None
    with open(uri.split(sep)[-1], 'wb') as f:
        f.write(content)
        return uri

def get_images_src_from_html(html_doc):
    '''
    Recupera todo el contenido de los atributos src de las etiquetas img.
    '''
    soup = BeautifulSoup(html_doc, 'html_parser')
    return (img.get('scr') for img in soup.find_all('img'))

def get_uri_from_images_src(base_uri, images_src):
    '''
    Devuelve una a una cada URI de la imagen a descargar.
    '''
    parsed_base = urlparse(base_uri)
    for src in images_src:
        parsed = urlparse(src)
        if parsed.netloc == '':
            path = parsed.path
            if parsed.query:
                path += '?' + parsed.query
            if path[0] != '/':
                if parsed_base.path == '/':
                    path = '/' + path
                else:
                    path = '/' + '/'.join(parsed_base.path.split('/')[:-1]) + '/' + path
            yield parsed_base.scheme + '://' + parsed_base.netloc + path
        else:
            yield parsed.geturl()

async def main(uri):
    async with aiohttp.ClientSession() as session:
        async with session.get(uri) as response:
            if response.status != 200:
                return None
            if response.content_type.startswith('text/'):
                return await response.text()
            else:
                return await response.read()


asyncio.run(main("http://www.formation-python.com/")) 

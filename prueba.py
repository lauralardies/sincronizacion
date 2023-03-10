import asyncio
import aiohttp
from bs4 import BeautifulSoup
from functools import partial
from urllib.parse import urlparse
from os import sep
from sys import stderr

async def wget(session, uri):
    '''
    Devuelve el contenido designado por una URI.
    '''
    async with session.get(uri) as response:
        if response.status != 200:
            return None
        if response.content_type.startswith('text/'):
            return await response.text()
        else:
            return await response.read()

def write_in_file(filename, content):
    '''
    Administra la parte bloqueante.
    '''
    with open(filename, 'wb') as f:
        f.write(content)

async def download(session, uri):
    '''
    Guardar en disco duro un archivo designado por una URI.
    '''
    content = await wget(session, uri)
    if content is None:
        return None
    loop = asyncio.get_running_loop()
    await loop.run_in_executor(None, partial(write_in_file, uri.split(sep)[-1], content))
    return uri

async def get_images_src_from_html(html_doc):
    '''
    Recupera todo el contenido de los atributos src de las etiquetas img.
    '''
    soup = BeautifulSoup(html_doc, 'html.parser')
    for img in soup.find_all('img'):
        yield img.get('scr')
        await asyncio.sleep(0.001)

async def get_uri_from_images_src(base_uri, images_src):
    '''
    Devuelve una a una cada URI de la imagen a descargar.
    '''
    parsed_base = urlparse(base_uri)
    async for src in images_src:
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
        await asyncio.sleep(0.001)

async def get_images(session, page_uri):
    '''
    Recuperaci??n de las URI de todas las im??genes de una p??gina.
    '''
    html = await wget(session, page_uri)
    if not html:
        print('Error: No se ha encontrado ninguna imagen', stderr)
        return None
    '''
    Recuperaci??n de las im??genes.
    '''
    images_src_gen = get_images_src_from_html(html)
    images_uri_gen = get_uri_from_images_src(page_uri, images_src_gen)
    async for image_uri in images_uri_gen:
        print('Descarga de %s' % image_uri)
        await download(session, image_uri)

async def main():
    web_page_uri = 'http://www.formation-python.com/'
    async with aiohttp.ClientSession() as session:
        await get_images(session, web_page_uri)

if __name__ == '__main__':
    asyncio.run(main())
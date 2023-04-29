# sincronizacion

Mi dirección de GitHub para este repositorio es la siguiente: [GitHub](https://github.com/lauralardies/sincronizacion)
https://github.com/lauralardies/sincronizacion

## Breve introducción
En este ejercicio estamos implementando en Python un código para descargar imágenes de una página web (¡Importante! Debes de tener en cuenta que sólo analizamos páginas web HTTP) y descargarlas en el disco.

Nuestro código no muestra nada en pantalla al terminar de ejecutarse debido a que la página web que estamos analizando no cuenta con ninguna imagen.

## Código `main.py`
```
import asyncio # Módulo para trabajar de manera asíncrona.
import aiohttp # Para hacer solicitudes HTTP.
from bs4 import BeautifulSoup # Para analizar HTML.
from functools import partial
from urllib.parse import urlparse #Para anañizar URLs.
from os import sep
from sys import stderr

async def wget(session, uri):
    '''
    Devuelve el contenido designado por una URI.
    '''
    async with session.get(uri) as response:
        if response.status != 200: # Respuesta distinta a 200 --> Devolvemos None.
            return None
        if response.content_type.startswith('text/'): # Contenido de la respuesta comienza por 'text/' --> Devolvemos el contenido como string.
            return await response.text()
        else: # Si el contenido no comienza por 'text/' --> Devolvemos el contenido como bytes.
            return await response.read()

def write_in_file(filename, content):
    '''
    Administra la parte bloqueante.
    Cualquier otra tarea que esté esperando en la misma tarea se bloqueará hasta que se complete esta tarea.
    '''
    with open(filename, 'wb') as f:
        f.write(content)

async def download(session, uri):
    '''
    Guardar en disco duro un archivo designado por una URI.
    '''
    content = await wget(session, uri) # Descarga de un archivo desde una URL determinada.
    if content is None:
        return None
    loop = asyncio.get_running_loop()
    # Como write_in_file es bloqueante (función anterior) --> Empleamos run_in_executor para ejecutarla en subproceso.
    await loop.run_in_executor(None, partial(write_in_file, uri.split(sep)[-1], content))
    return uri # Devolvemos la URL de la descarga completada.

async def get_images_src_from_html(html_doc):
    '''
    Recupera todo el contenido de los atributos src de las etiquetas img.
    '''
    soup = BeautifulSoup(html_doc, 'html.parser') # Para analizar HTML.
    for img in soup.find_all('img'):
        yield img.get('scr') # Devuelve cada URL de imagen individualmente.
        await asyncio.sleep(0.001) # Evitamos bloqueos.

async def get_uri_from_images_src(base_uri, images_src):
    '''
    Devuelve una a una cada URI de la imagen a descargar.
    '''
    parsed_base = urlparse(base_uri) # Analizamos 'base_uri'.
    async for src in images_src: # Cada elemento de images_src se analiza con urlparse().
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
        await asyncio.sleep(0.001) # Permitimos que otros procesos se ejecuten mientras se esperan las operaciones de entrada/salida (I/O).

async def get_images(session, page_uri):
    '''
    Recuperación de las URI de todas las imágenes de una página.
    '''
    html = await wget(session, page_uri) # Recuperamos el HTML de la página.
    if not html: # Entra en el if si la función wget no encuentra nada.
        print('Error: No se ha encontrado ninguna imagen', stderr) 
        return None
    '''
    Recuperación de las imágenes.
    '''
    images_src_gen = get_images_src_from_html(html) # Extraemos etiquetas de la imagen.
    images_uri_gen = get_uri_from_images_src(page_uri, images_src_gen) # Generamos una lista de URLs de imágenes.
    async for image_uri in images_uri_gen:
        print('Descarga de %s' % image_uri)
        await download(session, image_uri) # Descargamos cada imagen y la guardamos en el disco.

async def main():
    web_page_uri = 'http://www.formation-python.com/'
    async with aiohttp.ClientSession() as session: # ClientSession se recomienda como interfaz para realizar solicitudes HTTP.
        await get_images(session, web_page_uri)

if __name__ == '__main__':
    asyncio.run(main())
```

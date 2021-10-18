import requests
import urllib.parse
import m3u8
import os
import math
import asyncio
import aiohttp
import time


url_api = "https://gql.twitch.tv/gql"

cabecera_token = {
            'Accept': '*/*',
            'Accept-Encoding': 'gzip, deflate, br',
            'Accept-Language': 'es-ES',
            'Authorization': 'undefined',
            'Client-Id': 'kimne78kx3ncx6brgo4mv6wki5h1ko',
            'Connection': 'keep-alive',
            'Content-Length': '662',
            'Content-Type': 'text/plain;charset=UTF-8',
            'Device-Id': '0xuvWh0J2XUXQo78MMqtsAdD4xGPZ1ON',
            'Host': 'gql.twitch.tv',
            'Origin': 'https://www.twitch.tv',
            'Referer': 'https://www.twitch.tv/',
            'sec-ch-ua': '"Chromium";v="93", " Not A;Brand";v="99", "Google Chrome";v="93"',
            'sec-ch-ua-mobile': '?0',
            'sec-ch-ua-platform': '"Windows"',
            'Sec-Fetch-Dest': 'empty',
            'Sec-Fetch-Mode': 'cors',
            'Sec-Fetch-Site': 'same-site',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) '
                          'Chrome/92.0.4515.131 Safari/537.36'
            }

cabecera_m3u8 = {
            'Accept': 'application/x-mpegURL, application/vnd.apple.mpegurl, application/json, text/plain',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) '
                          'Chrome/92.0.4515.131 Safari/537.36'
            }

cabecera_data = {
            'Accept': '*/*',
            'Accept-Encoding': 'gzip, deflate, br',
            'Accept-Language': 'es-ES',
            'Authorization': 'undefined',
            'Client-Id': 'kimne78kx3ncx6brgo4mv6wki5h1ko',
            'Connection': 'keep-alive',
            'Content-Length': '287',
            'Content-Type': 'text/plain;charset=UTF-8',
            'Device-Id': '0xuvWh0J2XUXQo78MMqtsAdD4xGPZ1ON',
            'Host': 'gql.twitch.tv',
            'Origin': 'https://www.twitch.tv',
            'Referer': 'https://www.twitch.tv/',
            'sec-ch-ua': '"Chromium";v="93", " Not A;Brand";v="99", "Google Chrome";v="93"',
            'sec-ch-ua-mobile': '?0',
            'sec-ch-ua-platform': '"Windows"',
            'Sec-Fetch-Dest': 'empty',
            'Sec-Fetch-Mode': 'cors',
            'Sec-Fetch-Site': 'same-site',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) '
                          'Chrome/92.0.4515.131 Safari/537.36'
            }

lst_simb = {
    '|': '.l.',
    '>': '.M.',
    '<': '.m.',
    '"': '.__.',
    '?':  '.!.',
    '*': '.x.',
    ':': '.-.',
    '/': '.).',
    '\\': '.(.',
    }


def solicitarToken(vodID):
    global url_api
    global cabecera_token

    bdy_token = [
        {
            'operationName':'PlaybackAccessToken_Template',
            'query': 'query PlaybackAccessToken_Template($login: String!, $isLive: Boolean!, $vodID: ID!, $isVod: '
                     'Boolean!, $playerType: String!) {  streamPlaybackAccessToken(channelName: $login, params: '
                     '{platform: \"web\", playerBackend: \"mediaplayer\", playerType: $playerType}) '
                     '@include(if: $isLive) {    value    signature    __typename  }  videoPlaybackAccessToken'
                     '(id: $vodID, params: {platform: \"web\", playerBackend: \"mediaplayer\", playerType: '
                     '$playerType}) @include(if: $isVod) {    value    signature    __typename  }}',
            'variables':{
                'isLive':False,
                'login':'',
                'isVod': True,
                'vodID': vodID,
                'playerType': 'site'
            }
        }
    ]

    respuesta_token = requests.post(url_api, json=bdy_token, headers=cabecera_token)
    contenido_token = respuesta_token.json()

    firma = contenido_token[0]['data']['videoPlaybackAccessToken']['signature']
    token = contenido_token[0]['data']['videoPlaybackAccessToken']['value']
    token_cod = urllib.parse.quote(token, safe='')

    return firma, token_cod


def obtenerReso(vodID, firma, token_cod):
    global cabecera_m3u8
    
    url_reso = 'https://usher.ttvnw.net/vod/' + vodID + '.m3u8?allow_source=true& player_backend=mediaplayer&' \
               'playlist_include_framerate=true&reassignments_supported=true&sig=' + firma + '&supported_codecs=' \
               'avc1&token=' + token_cod + '&cdm=wv&player_version=1.5.0'

    arch_reso = requests.get(url_reso, headers=cabecera_m3u8)

    m3u8_reso = m3u8.loads(arch_reso.text)

    return m3u8_reso.data['playlists'][0]['uri']


def obtenerFrag(url_frag):
    global cabecera_m3u8

    arch_frag = requests.get(url_frag, headers=cabecera_m3u8)

    m3u8_frag = m3u8.loads(arch_frag.text)

    return m3u8_frag.data['segments']


def obtenerNom(vodID):
    global url_api
    global cabecera_data
    
    bdy_data = [
        {
            'operationName':'ComscoreStreamingQuery',
            'variables':{
                'channel':'',
                'clipSlug':'',
                'isClip': False,
		'isLive': False,
		'isVodOrCollection':  True,
                'vodID': vodID,
            },
	    'extensions': {
		    'persistedQuery': {
			    'version': 1,
			    'sha256Hash': 'e1edae8122517d013405f237ffcc124515dc6ded82480a88daef69c83b53ac01'
			}
		}
        }
    ]

    respuesta_data = requests.post(url_api, json=bdy_data, headers=cabecera_data)
    data = respuesta_data.json()

    return data[0]['data']['video']['title']


async def descargarFrag(session, url, i):
    async with session.get(url) as respuesta:
        if respuesta.status == 200:
            contenido = await respuesta.content.read()
            with open("./ts/" + str(i) + ".ts", "wb") as fragmento:
                fragmento.write(contenido)
        else:
            os.system("echo URL: " + url)
            os.system("echo status: " + str(respuesta.status))


async def realizarTareas(url_ts, lista_frag):
    async with aiohttp.ClientSession() as session:
        tareas = [descargarFrag(session, url_ts + item['uri'], i) for i, item in enumerate(lista_frag)]
        await asyncio.gather(*tareas)


def crearTxtProp(nom_vid):
    segnd_creac = os.path.getctime(nom_vid + ".mp4")
    fech_creac = time.ctime(segnd_creac)
    segnd_modi = os.path.getmtime(nom_vid + ".mp4")
    fech_modi = time.ctime(segnd_modi)
    segnd_accs = os.path.getatime(nom_vid + ".mp4")
    fech_accs = time.ctime(segnd_accs)

    with open(nom_vid + ".txt", "w", encoding = 'utf-8') as archivo:
        archivo.write("nomvid=" + nom_vid + "\n")
        archivo.write("screac=" + str(segnd_creac) + "\n")
        archivo.write("smodi=" + str(segnd_modi) + "\n")
        archivo.write("saccs=" + str(segnd_accs) + "\n\n")
        archivo.write("======================================================\n")
        archivo.write("Nombre: " + nom_vid + "\n\n")
        archivo.write("Fecha de Creacion: " + fech_creac + "\n")
        archivo.write("Segundos de Creacion: " + str(segnd_creac) + "\n\n")
        archivo.write("Fecha de Modificacion: " + fech_modi + "\n")
        archivo.write("Segundos de Modificacion: " + str(segnd_modi) + "\n\n")
        archivo.write("Fecha de Acceso: " + fech_accs + "\n")
        archivo.write("Segundos de Acceso: " + str(segnd_accs) + "\n")


def main(vodID):
    global lst_simb
    
    nom_orig = obtenerNom(vodID)
    os.system("echo Nombre Original: " + nom_orig)
    nom_modf = nom_orig
    for simbolo in lst_simb:
        nom_modf = nom_modf.replace(simbolo, lst_simb[simbolo])
    os.system("echo Nombre Modificado:  " + nom_modf)
    
    firma, token_cod = solicitarToken(vodID)
    url_frag = obtenerReso(vodID, firma, token_cod)
    lista_frag = obtenerFrag(url_frag)

    url_ts = url_frag[:len(url_frag)- url_frag[::-1].index('/')]
    os.system("echo -------------------------------------------------")
    os.system("echo URL HLS Fragmentos: " + url_frag)
    os.system("echo URL HLS Base TS: " + url_ts)

    if len(nom_modf + ".mp4") > 203:
        nom_vid = nom_modf[:203] + " [...]"
    else:
        nom_vid = nom_modf
    os.system("echo -------------------------------------------------")
    os.system("echo Nombre de archivo recortado: \n")
    os.system("echo " + nom_vid)

    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    os.system("echo -------------------------------------------------")
    os.system("echo Descarga de Fragmentos. Errores:")
    os.system("mkdir ts")
    asyncio.run(realizarTareas(url_ts, lista_frag))

    os.system("echo -------------------------------------------------")
    os.system("echo Union de archivos TS")
    with open(nom_vid + ".ts", "wb") as arch_ts:
        for i in range(len(lista_frag)):
            with open("./ts/" + str(i) + ".ts", "rb") as fragmento:
                arch_ts.write(fragmento.read())
            os.remove("./ts/" + str(i) + ".ts")
    os.system("rd ts")
    
    os.system("echo -------------------------------------------------")
    os.system("echo Ejecutando ffmpeg.exe")
    os.system("echo Comando:")
    os.system('echo ffmpeg.exe -y -i "' + nom_vid + '.ts" -c:v copy -c:a copy "' + nom_vid + '.mp4"')
    os.system('ffmpeg.exe -y -i "' + nom_vid + '.ts" -c:v copy -c:a copy "' + nom_vid + '.mp4"')
    os.system("echo -------------------------------------------------")
    os.system("echo Eliminando archivo TS")
    os.remove(nom_vid + '.ts')

    peso_arch = os.stat(nom_vid + '.mp4').st_size
    peso_arch = peso_arch/1024/1024/1024
    os.system("echo -------------------------------------------------")
    os.system("echo Peso del archivo: %.2f GB" %peso_arch)

    os.system("echo -------------------------------------------------")
    os.system("echo Creando archivo de propiedades del MP4")
    crearTxtProp(nom_vid)

    os.system("echo -------------------------------------------------")
    os.system("echo Comprimiendo archivo MP4. Ejecutando winrar.exe")
    os.system("echo Comando:")
    if peso_arch <= 14:
        os.system('echo winrar.exe a -afrar -df -m5 -mt3 -ri15 -t -tk -ts "' + nom_vid + '.rar" "' + nom_vid + '.mp4"')
        os.system('winrar.exe a -afrar -df -m5 -mt3 -ri15 -t -tk -ts "' + nom_vid + '.rar" "' + nom_vid + '.mp4"')
    elif peso_arch > 14 and peso_arch <= 28:
        tam_vol = math.ceil(peso_arch/2)
        os.system('echo winrar.exe a -afrar -df -m5 -mt3 -ri15 -t -tk -ts -v' + str(tam_vol) + 'g "' + nom_vid +
              '.rar" "' + nom_vid + '.mp4"')
        os.system('winrar.exe a -afrar -df -m5 -mt3 -ri15 -t -tk -ts -v' + str(tam_vol) + 'g "' + nom_vid +
                  '.rar" "' + nom_vid + '.mp4"')
    else:
        os.system('echo winrar.exe a -afrar -df -m5 -mt3 -ri15 -t -tk -ts -v14g "' + nom_vid +
              '.rar" "' + nom_vid + '.mp4"')
        os.system('winrar.exe a -afrar -df -m5 -mt3 -ri15 -t -tk -ts -v14g "' + nom_vid +
                  '.rar" "' + nom_vid + '.mp4"')

main("1120047700")
main("1121034384")
main("1122057857")

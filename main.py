from fastapi import FastAPI, Request
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
import yt_dlp
import os
import uuid
import glob

app = FastAPI()

os.makedirs("descargas", exist_ok=True)
os.makedirs("static", exist_ok=True)

# --- SISTEMA DE COOKIES SEGURAS ---
# Lee el contenido de las cookies desde las variables de entorno de Render
contenido_cookies = os.environ.get("YOUTUBE_COOKIES")

if contenido_cookies:
    # Crea el archivo cookies.txt en el servidor Linux en tiempo de ejecución
    with open("cookies.txt", "w", encoding="utf-8") as f:
        f.write(contenido_cookies)
# ----------------------------------

app.mount("/static", StaticFiles(directory="static"), name="static")

app.mount("/static", StaticFiles(directory="static"), name="static")

@app.get("/", response_class=HTMLResponse)
async def leer_index():
    with open("static/index.html", "r", encoding="utf-8") as f:
        return f.read()

@app.post("/descargar")
async def procesar_descarga(request: Request):
    datos = await request.json()
    url = datos.get("url")
    tipo = datos.get("tipo")
    calidad = datos.get("calidad")
    miniatura = datos.get("miniatura")
    subtitulos = datos.get("subtitulos")
    
    id_unico = str(uuid.uuid4())[:8]
    ruta_salida = f"descargas/{id_unico}_%(title)s.%(ext)s"
    ruta_script = os.path.dirname(os.path.abspath(__file__))
    
    opciones_ytdlp = {
        'outtmpl': ruta_salida,
        'noplaylist': True,
        'quiet': True,
        'ffmpeg_location': ruta_script,
        'cookiefile': 'cookies.txt',  # Dejar esto igual, el script ya habrá creado el archivo
        opciones_ytdlp = {
        'outtmpl': ruta_salida,
        'noplaylist': True,
        'quiet': True,
        'ffmpeg_location': ruta_script,
        'cookiefile': 'cookies.txt',
        'extractor_args': {
            'youtube': {
                # Usamos Smart TV y Web Móvil: ambos soportan cookies y evaden el bloqueo estricto
                'player_client': ['tv', 'mweb']
            }
        },
        'postprocessors': []
    }
        'postprocessors': []
    }
    
    if "MP3" in tipo:
        opciones_ytdlp['format'] = 'bestaudio/best'
        opciones_ytdlp['postprocessors'].append({
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': calidad,
        })
    else:
        if calidad == "best":
            opciones_ytdlp['format'] = 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best'
        else:
            opciones_ytdlp['format'] = f'bestvideo[height<={calidad}][ext=mp4]+bestaudio[ext=m4a]/best[height<={calidad}][ext=mp4]/best'
        
        opciones_ytdlp['merge_output_format'] = 'mp4'
        
        if subtitulos:
            opciones_ytdlp['writesubtitles'] = True
            opciones_ytdlp['writeautomaticsub'] = True
            opciones_ytdlp['subtitleslangs'] = ['es', 'en']
            opciones_ytdlp['postprocessors'].append({
                'key': 'FFmpegEmbedSubtitle'
            })

    if miniatura:
        opciones_ytdlp['writethumbnail'] = True
        opciones_ytdlp['postprocessors'].append({
            'key': 'EmbedThumbnail'
        })

    try:
        with yt_dlp.YoutubeDL(opciones_ytdlp) as ydl:
            ydl.extract_info(url, download=True)
            
        archivos_procesados = glob.glob(f"descargas/{id_unico}_*")
        
        if not archivos_procesados:
            return {"error": "El motor de conversión falló y el archivo no se generó en el servidor."}
            
        archivo_final = archivos_procesados[0]
        nombre_final = os.path.basename(archivo_final)[9:] 
        
        return FileResponse(
            path=archivo_final, 
            filename=nombre_final, 
            media_type='application/octet-stream'
        )
    except Exception as e:
        return {"error": str(e)}

import requests
import re
import sys
import datetime

TOPIC = "tren_alausi_hernan_2026"
TARGET_DATES = ["2026-10-15", "2026-10-16", "2026-10-17", "2026-10-18"]
EVENT_ID = "063823ac-91ad-439a-b352-53e48869dd0b"
SUBEVENT_ID = "4b41d460-67f4-4408-9ecd-f0e752b61ba5"

def get_api_key():
    url = "https://app.ticketexito.com/evento/trenalausi/actividad/tren-turistico"
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
    }
    html_resp = requests.get(url, headers=headers)
    html_resp.raise_for_status()
    
    # Buscar el bundle principal que cambia de nombre en cada build
    match = re.search(r'src="(main-.*?\.js)"', html_resp.text)
    if not match:
        raise Exception("No se encontró el archivo JS principal en el HTML")
    js_filename = match.group(1)
    
    js_url = f"https://app.ticketexito.com/{js_filename}"
    js_resp = requests.get(js_url, headers=headers)
    js_resp.raise_for_status()
    
    # Extraer el API Key hardcodeado en el código de Angular
    key_match = re.search(r'api_key:"(.*?)"', js_resp.text)
    if not key_match:
        raise Exception("No se encontró el API Key en el JS bundle")
        
    return key_match.group(1)

def main():
    try:
        print("Obteniendo API Key...")
        api_key = get_api_key()
        
        api_url = f"https://api.ticketexito.com/web/eventos/{EVENT_ID}/subeventos/{SUBEVENT_ID}/fechas"
        headers = {
            'x-api-key': api_key,
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        
        print(f"Consultando fechas disponibles...")
        resp = requests.get(api_url, headers=headers)
        resp.raise_for_status()
        data = resp.json()
        
        fechas = data.get('data', {}).get('fechas', [])
        
        fechas_encontradas = [fecha for fecha in TARGET_DATES if fecha in fechas]
        
        if fechas_encontradas:
            tz = datetime.timezone(datetime.timedelta(hours=-5))
            now = datetime.datetime.now(tz)
            timestamp = now.strftime("%Y-%m-%d %H:%M:%S UTC-5")
            
            fechas_str = ", ".join(fechas_encontradas)
            message = f"🚨 ¡Tiquetes habilitados para: {fechas_str}! Entra a comprar.\n\nDetectado a las: {timestamp}"
            
            ntfy_url = f"https://ntfy.sh/{TOPIC}"
            requests.post(ntfy_url, data=message.encode('utf-8'))
            print(f"¡Disponibilidad detectada para {fechas_str}! Notificación enviada.")
        else:
            print(f"Sin disponibilidad para los días buscados ({TARGET_DATES}) aún. Fechas encontradas: {fechas}")
            
    except Exception as e:
        print(f"Error durante el monitoreo: {e}", file=sys.stderr)
        # Terminamos con código 0 para que GitHub Actions no marque fallo continuo si la web cambia
        sys.exit(0)

if __name__ == "__main__":
    main()

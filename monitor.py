import os
import json
import requests
import re
import sys
import datetime

TOPIC = "tren_alausi_hernan_2026"
EVENT_ID = "063823ac-91ad-439a-b352-53e48869dd0b"
SUBEVENT_ID = "4b41d460-67f4-4408-9ecd-f0e752b61ba5"
KNOWN_DATES_FILE = "known_dates.json"
HISTORIAL_FILE = "historial_aperturas.txt"

def load_known_dates():
    if os.path.exists(KNOWN_DATES_FILE):
        try:
            with open(KNOWN_DATES_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                return set(data.get("known_dates", []))
        except Exception as e:
            print(f"Advertencia al leer {KNOWN_DATES_FILE}: {e}")
    return set()

def save_known_dates(known_dates):
    with open(KNOWN_DATES_FILE, "w", encoding="utf-8") as f:
        json.dump({"known_dates": sorted(list(known_dates))}, f, indent=2)

def registrar_historial(entry):
    with open(HISTORIAL_FILE, "a", encoding="utf-8") as f:
        f.write(entry + "\n")

def get_api_key():
    url = "https://app.ticketexito.com/evento/trenalausi/actividad/tren-turistico"
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
    }
    html_resp = requests.get(url, headers=headers)
    html_resp.raise_for_status()
    
    match = re.search(r'src="(main-.*?\.js)"', html_resp.text)
    if not match:
        raise Exception("No se encontró el archivo JS principal en el HTML")
    js_filename = match.group(1)
    
    js_url = f"https://app.ticketexito.com/{js_filename}"
    js_resp = requests.get(js_url, headers=headers)
    js_resp.raise_for_status()
    
    key_match = re.search(r'api_key:"(.*?)"', js_resp.text)
    if not key_match:
        raise Exception("No se encontró el API Key en el JS bundle")
        
    return key_match.group(1)

def main():
    try:
        known_dates = load_known_dates()
        print(f"Fechas ya conocidas ({len(known_dates)}): {sorted(list(known_dates))}")
        
        print("Obteniendo API Key...")
        api_key = get_api_key()
        
        api_url = f"https://api.ticketexito.com/web/eventos/{EVENT_ID}/subeventos/{SUBEVENT_ID}/fechas"
        headers = {
            'x-api-key': api_key,
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        
        print("Consultando fechas disponibles en TicketÉxito...")
        resp = requests.get(api_url, headers=headers)
        resp.raise_for_status()
        data = resp.json()
        
        fechas_servidor = data.get('data', {}).get('fechas', [])
        print(f"Fechas activas en el servidor: {fechas_servidor}")
        
        # Detectar si hay fechas nuevas que no hayamos visto antes
        nuevas_fechas = [f for f in fechas_servidor if f not in known_dates]
        
        if nuevas_fechas:
            nuevas_fechas.sort()
            tz = datetime.timezone(datetime.timedelta(hours=-5))
            now = datetime.datetime.now(tz)
            timestamp = now.strftime("%Y-%m-%d %H:%M:%S UTC-5")
            
            fechas_str = ", ".join(nuevas_fechas)
            message = (
                f"🚨 ¡Nuevas fechas habilitadas para el Tren de Alausí!\n\n"
                f"Nuevas fechas: {fechas_str}\n"
                f"Detectado a las: {timestamp}\n\n"
                f"¡Entra a comprar ahora!"
            )
            
            ntfy_url = f"https://ntfy.sh/{TOPIC}"
            requests.post(ntfy_url, data=message.encode('utf-8'))
            print(f"¡Nuevas fechas detectadas ({fechas_str})! Notificación enviada a ntfy.")
            
            # Actualizar estado y registrar en el historial
            known_dates.update(nuevas_fechas)
            save_known_dates(known_dates)
            registrar_historial(f"[{timestamp}] Habilitadas: {fechas_str}")
            print("Estado e historial actualizados correctamente.")
        else:
            print("Sin fechas nuevas. Todas las fechas del servidor ya son conocidas.")
            
    except Exception as e:
        print(f"Error durante el monitoreo: {e}", file=sys.stderr)
        sys.exit(0)

if __name__ == "__main__":
    main()

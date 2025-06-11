#kod na pico do sprawdzania czy pico poprawnie sie laczy z siecia
import wifi
import time

try:
    from secrets import secrets
except ImportError:
    print("Utwórz plik secrets.py z danymi WiFi")
    raise

print("Łączenie z WiFi...")
try:
    wifi.radio.connect(secrets["ssid"], secrets["password"])
    print("Połączono z:", secrets["ssid"])
    print("Adres IP:", wifi.radio.ipv4_address)
except Exception as e:
    print("Błąd połączenia WiFi:", e)

while True:
    print("Status: połączony" if wifi.radio.ipv4_address else "Status: brak połączenia")
    time.sleep(5)

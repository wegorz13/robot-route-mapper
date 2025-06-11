# pythonowy skrypt do wysylania komend do pico, najpierw nalezy sprawdzic ip dla polaczonego pico na wyjsciu
# pico przy wgrywaniu kodu/ laczeniu sie z siecia
import keyboard
import requests
import time

PICO_IP = "http://192.168.137.158"  # ← adres IP Pico W

# Mapowanie klawiszy na komendy
KEY_TO_CMD = {
    "up": "forward",
    "down": "backward",
    "left": "left",
    "right": "right",
    "space": "stop"
}

last_command = None

def send_command(cmd):
    global last_command
    if cmd != last_command:
        try:
            r = requests.get(f"{PICO_IP}/drive?cmd={cmd}", timeout=1)
            print(f"Wysłano: {cmd} | Odpowiedź: {r.text}")
            last_command = cmd
        except Exception as e:
            print("Błąd:", e)


print("Sterowanie robotem: ↑ ↓ ← →, [SPACJA] = STOP, [ESC] = Wyjście")

try:
    while True:
        found = False
        for key, cmd in KEY_TO_CMD.items():
            if keyboard.is_pressed(key):
                send_command(cmd)
                found = True
                break
        if not found:
            send_command("stop")  # zatrzymaj, gdy nie wciskasz nic
        if keyboard.is_pressed("esc"):
            break
        time.sleep(0.1)
except KeyboardInterrupt:
    pass

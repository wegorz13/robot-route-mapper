# do debugowania polaczenia wifi, zeby bylo wiadomo czy pico widzi z czym chcemy sie laczyc
import wifi

print("Skanuję sieci...")
for network in wifi.radio.start_scanning_networks():
    print("Znaleziono:", network.ssid)
wifi.radio.stop_scanning_networks()

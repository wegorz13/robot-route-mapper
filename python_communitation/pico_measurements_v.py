# kod na pico do pomiarow odleglosci liniowej i kontowej w jednostce czasu
import time
import board
import digitalio
import pwmio
import wifi
import socketpool
from secrets import secrets

# Standby
stby01 = digitalio.DigitalInOut(board.GP5)
stby01.direction = digitalio.Direction.OUTPUT
stby23 = digitalio.DigitalInOut(board.GP12)
stby23.direction = digitalio.Direction.OUTPUT
stby01.value = True
stby23.value = True

# INx
in10 = digitalio.DigitalInOut(board.GP6)
in10.direction = digitalio.Direction.OUTPUT
in11 = digitalio.DigitalInOut(board.GP4)
in11.direction = digitalio.Direction.OUTPUT
in12 = digitalio.DigitalInOut(board.GP13)
in12.direction = digitalio.Direction.OUTPUT
in13 = digitalio.DigitalInOut(board.GP11)
in13.direction = digitalio.Direction.OUTPUT

in20 = digitalio.DigitalInOut(board.GP7)
in20.direction = digitalio.Direction.OUTPUT
in21 = digitalio.DigitalInOut(board.GP3)
in21.direction = digitalio.Direction.OUTPUT
in22 = digitalio.DigitalInOut(board.GP14)
in22.direction = digitalio.Direction.OUTPUT
in23 = digitalio.DigitalInOut(board.GP10)
in23.direction = digitalio.Direction.OUTPUT

# PWM
m0 = pwmio.PWMOut(board.GP8, frequency=1000)
m1 = pwmio.PWMOut(board.GP2, frequency=1000)
m2 = pwmio.PWMOut(board.GP15, frequency=1000)
m3 = pwmio.PWMOut(board.GP9, frequency=1000)

motors = [
    # (IN_A, IN_B, PWM)
    (in10, in20, m0),  # Motor 0
    (in11, in21, m1),  # Motor 1
    (in12, in22, m2),  # Motor 2
    (in13, in23, m3),  # Motor 3
]


def stop_motor(nr):
    in_a, in_b, pwm = motors[nr]
    in_a.value = False
    in_b.value = False
    pwm.duty_cycle = 0


def move_motor(nr, direction, power=100):
    in_a, in_b, pwm = motors[nr]
    pw = int((power * 65535) // 100)
    if direction == "forward":
        in_a.value = True
        in_b.value = False
    elif direction == "backward":
        in_a.value = False
        in_b.value = True
    else:
        in_a.value = False
        in_b.value = False
        pw = 0
    pwm.duty_cycle = pw


def stop_all():
    for i in range(4):
        stop_motor(i)


def move_forward():
    move_motor(0, "forward")  # lewy tylni silnik
    move_motor(1, "forward")  # prawy tylni silnik
    move_motor(2, "forward")  # lewy przedni silnik
    move_motor(3, "forward")  # prawy przedni silnik


def move_backward():
    move_motor(0, "backward")  # lewy tylni silnik
    move_motor(1, "backward")  # prawy tylni silnik
    move_motor(2, "backward")  # lewy przedni silnik
    move_motor(3, "backward")  # prawy przedni silnik


def go_left():
    move_motor(0, "forward")  # lewy tylni silnik
    move_motor(1, "backward")  # prawy tylni silnik
    move_motor(2, "backward")  # lewy przedni silnik
    move_motor(3, "forward")  # prawy przedni silnik


def go_right():
    move_motor(0, "backward")  # lewy tylni silnik
    move_motor(1, "forward")  # prawy tylni silnik
    move_motor(2, "forward")  # lewy przedni silnik
    move_motor(3, "backward")  # prawy przedni silnik


def turn_left():
    move_motor(0, "backward")  # lewy tylni silnik
    move_motor(1, "forward")  # prawy tylni silnik
    move_motor(2, "backward")  # lewy przedni silnik
    move_motor(3, "forward")  # prawy przedni silnik


def turn_right():
    move_motor(0, "forward")  # lewy tylni silnik
    move_motor(1, "backward")  # prawy tylni silnik
    move_motor(2, "forward")  # lewy przedni silnik
    move_motor(3, "backward")  # prawy przedni silnik


# --- Połączenie z WiFi ---
print("Łączenie z WiFi...")
wifi.radio.connect(secrets["ssid"], secrets["password"])
print("Połączono z:", secrets["ssid"])
print("Adres IP:", wifi.radio.ipv4_address)

# --- Serwer socketowy ---
pool = socketpool.SocketPool(wifi.radio)
server = pool.socket(pool.AF_INET, pool.SOCK_STREAM)
server.bind((str(wifi.radio.ipv4_address), 80))
server.listen(1)
print("Nasłuchuję na porcie 80")

# --- Główna pętla ---
while True:
    conn, addr = server.accept()
    print("Połączono z:", addr)
    buffer = bytearray(1024)
    size = conn.recv_into(buffer)
    request = buffer[:size].decode("utf-8")
    print("Żądanie:\n", request)

    response_body = "OK"
    try:
        get_line = request.split(" ")[1].lstrip("/")
        path, _, query = get_line.partition("?")
        if path == "drive":
            cmd = None
            for param in query.split("&"):
                if param.startswith("cmd="):
                    cmd = param.split("=")[1]
            if cmd == "forward":
                if cmd == "forward":
                    move_forward()
                    time.sleep(1)
                    stop_all()
                    response_body = "Wszystkie silniki do przodu przez 1s"
            elif cmd == "right":
                turn_right()  # skręt w prawo
                start = time.monotonic()
                # Czekaj aż komenda "stop" zostanie odebrana
                while True:
                    conn2, addr2 = server.accept()
                    buffer2 = bytearray(1024)
                    size2 = conn2.recv_into(buffer2)
                    request2 = buffer2[:size2].decode("utf-8")
                    print("Żądanie:\n", request2)
                    get_line2 = request2.split(" ")[1].lstrip("/")
                    path2, _, query2 = get_line2.partition("?")
                    if path2 == "drive":
                        cmd2 = None
                        for param2 in query2.split("&"):
                            if param2.startswith("cmd="):
                                cmd2 = param2.split("=")[1]
                        if cmd2 == "stop":
                            stop_all()
                            end = time.monotonic()
                            elapsed = end - start
                            response_body = f"Czas działania silników: {elapsed:.2f} sekundy"
            elif cmd == "backward":
                move_backward()
                time.sleep(1)
                stop_all()
                response_body = "Wszystkie silniki do tyłu przez 1s"
            elif cmd == "left":
                turn_left()
                start = time.monotonic()
                # Czekaj aż komenda "stop" zostanie odebrana
                while True:
                    conn2, addr2 = server.accept()
                    buffer2 = bytearray(1024)
                    size2 = conn2.recv_into(buffer2)
                    request2 = buffer2[:size2].decode("utf-8")
                    print("Żądanie:\n", request2)
                    get_line2 = request2.split(" ")[1].lstrip("/")
                    path2, _, query2 = get_line2.partition("?")
                    if path2 == "drive":
                        cmd2 = None
                        for param2 in query2.split("&"):
                            if param2.startswith("cmd="):
                                cmd2 = param2.split("=")[1]
                        if cmd2 == "stop":
                            stop_all()
                            end = time.monotonic()
                            elapsed = end - start
                            response_body = f"Czas działania silników: {elapsed:.2f} sekundy"
            elif cmd == "stop":
                stop_all()
                response_body = "Wszystkie silniki zatrzymane"
            else:
                response_body = "Nieznana komenda"
        else:
            response_body = "Użyj /drive?cmd=forward"
    except Exception as e:
        response_body = f"Błąd: {e}"

    response = f"""\
HTTP/1.1 200 OK

{response_body}
"""
    conn.send(response.encode("utf-8"))
    conn.close()

# docelowy kod na pico do sterowania pojazdem i wysylania odpowiedzi
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
print("Connecting with WiFi...")
wifi.radio.connect(secrets["ssid"], secrets["password"])
print("Connected with:", secrets["ssid"])
print("IP Adress:", wifi.radio.ipv4_address)

# --- Serwer socketowy ---
pool = socketpool.SocketPool(wifi.radio)
server = pool.socket(pool.AF_INET, pool.SOCK_STREAM)
server.bind((str(wifi.radio.ipv4_address), 80))
server.listen(1)
print("Port 80")

# --- Główna pętla ---
last_cmd = None
last_cmd_time = None

while True:
    conn, addr = server.accept()
    print("Connected with:", addr)
    buffer = bytearray(1024)
    size = conn.recv_into(buffer)
    request = buffer[:size].decode("utf-8")
    print("Request:\n", request)

    response_body = "OK"
    try:
        get_line = request.split(" ")[1].lstrip("/")
        path, _, query = get_line.partition("?")
        if path == "drive":
            cmd = None
            for param in query.split("&"):
                if param.startswith("cmd="):
                    cmd = param.split("=")[1]
            if cmd in ["forward", "backward", "left", "right"]:
                if last_cmd != cmd:
                    last_cmd = cmd
                    last_cmd_time = time.monotonic()
                if cmd == "forward":
                    move_forward()
                elif cmd == "right":
                    go_right()
                elif cmd == "backward":
                    move_backward()
                elif cmd == "left":
                    go_left()
            elif cmd == "stop":
                stop_all()
                if last_cmd_time is not None:
                    elapsed = time.monotonic() - last_cmd_time
                    response_body = f"{last_cmd} : {elapsed:.2f}"
                    last_cmd = None
                    last_cmd_time = None
                else:
                    response_body = "engines stopped"
            else:
                response_body = "unknown command"
        else:
            response_body = "command error"
    except Exception as e:
        response_body = f"Error: {e}"

    response = f"""\
HTTP/1.1 200 OK

{response_body}
"""
    conn.send(response.encode("utf-8"))
    conn.close()

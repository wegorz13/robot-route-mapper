# do debugowania dzialania silnikow
import time
import board
import digitalio
import pwmio

# Lista używanych pinów (numery GP)
used_pins = [2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15]

# Przygotuj listę wszystkich pinów GP0-GP28 (bez używanych)
all_pins = [getattr(board, f"GP{i}") for i in range(29) if hasattr(board, f"GP{i}")]
test_pins = [p for i, p in enumerate(all_pins) if i not in used_pins]

# Ustaw silniki do przodu (przypisania jak w Twoim kodzie)
stby01 = digitalio.DigitalInOut(board.GP5)
stby01.direction = digitalio.Direction.OUTPUT
stby23 = digitalio.DigitalInOut(board.GP12)
stby23.direction = digitalio.Direction.OUTPUT
stby01.value = True
stby23.value = True

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

m0 = pwmio.PWMOut(board.GP8, frequency=1000)
m1 = pwmio.PWMOut(board.GP2, frequency=1000)
m2 = pwmio.PWMOut(board.GP15, frequency=1000)
m3 = pwmio.PWMOut(board.GP9, frequency=1000)

# Funkcja: wszystkie silniki do przodu
def all_motors_forward(power=100):
    pw = int((power * 65535) // 100)
    in10.value = True
    in20.value = False
    in11.value = True
    in21.value = False
    in12.value = True
    in22.value = False
    in13.value = True
    in23.value = False
    m0.duty_cycle = pw
    m1.duty_cycle = pw
    m2.duty_cycle = pw
    m3.duty_cycle = pw

# Przygotuj wejścia na nieużywanych pinach
inputs = []
for pin in test_pins:
    inp = digitalio.DigitalInOut(pin)
    inp.direction = digitalio.Direction.INPUT
    inp.pull = digitalio.Pull.UP
    inputs.append((pin, inp))

print("Testuję nieużywane piny. Kręcę wszystkimi silnikami do przodu.")
all_motors_forward()

try:
    while True:
        for pin, inp in inputs:
            if not inp.value:
                print(f"Impuls na pinie {pin}")
        time.sleep(0.01)
except KeyboardInterrupt:
    # Zatrzymaj silniki po przerwaniu
    m0.duty_cycle = 0
    m1.duty_cycle = 0
    m2.duty_cycle = 0
    m3.duty_cycle = 0
    print("STOP")
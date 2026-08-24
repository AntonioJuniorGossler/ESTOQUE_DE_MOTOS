import serial

porta = serial.Serial(
    port='COM1',
    baudrate=9600,
    timeout=1
)

def ler_tag():

    if porta.in_waiting:

        tag = porta.readline().decode().strip()

        return tag

    return None
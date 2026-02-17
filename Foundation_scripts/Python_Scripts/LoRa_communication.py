import serial
import time

PORT = '/dev/serial0'
BAUD = 9600

def send_command(ser, command):
    ser.write((command + '\r\n').encode())
    time.sleep(0.3)
    response = ser.readlines()
    return [line.decode(errors="ignore").strip() for line in response]

try:
    lora = serial.Serial(PORT, BAUD, timeout=1)
    print("Connected to LoRa module.\n")
except Exception as e:
    print("Could not connect:", e)
    exit()

time.sleep(1)

# Checking LoRa RYLR998 moduule configuration
print("Checking LoRa configuration...\n")

commands = {
    "Band": "AT+BAND?",
    "Address": "AT+ADDRESS?",
    "Network ID": "AT+NETWORKID?",
    "Parameters (SF,BW,CR,Preamble)": "AT+PARAMETER?"
}

for label, cmd in commands.items():
    print(f"Sending {cmd}")
    response = send_command(lora, cmd)
    for line in response:
        print(f"{label}: {line}")
    print()

print("Configuration check complete.\n")

# ************************LoRA Rx Code Test************************

#import serial
#import time

try:
    lora = serial.Serial('/dev/serial0', 9600, timeout=1)
    print("Connected to LoRa module.")
except Exception as e:
    print("Could not connect:", e)
    exit()

print("Listening for messages...")

try:
    while True:
        line = lora.readline()
        if line:
            try:
                print("Received:", line.decode().strip())
            except:
                print("Raw bytes:", line)
except KeyboardInterrupt:
    print("Stopping...")

lora.close()

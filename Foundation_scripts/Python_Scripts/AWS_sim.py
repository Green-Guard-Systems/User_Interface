#Incoming LoRa packet simulator
import time
import json
import awscrt
import awsiot
from awscrt import mqtt
from awsiot import mqtt_connection_builder

# 1. Setup the Address and Identity
ENDPOINT = "a1kefksbmaj4e4-ats.iot.us-east-1.amazonaws.com"              #AWS End-Point Unique to individual users "Domain configuration > domain name"
#CLIENT_ID = "CentralGateway"                                            #THIS IS MY "THING" Created in IoT Core (Match both script and AWS title)
CLIENT_ID = "SmartFarm_P1_01"                                            #OSCAR's thing

# 2. Point to the Security Keys (All these files are together in a single folder inside the Raspy!!!)
PATH_TO_CERT = "/home/pi/AWS/AWScertificates/certificate.pem.crt"        #certificate
PATH_TO_KEY = "/home/pi/AWS/AWScertificates/private.pem.key"             #private key
PATH_TO_ROOT_CA = "/home/pi/AWS/AWScertificates/AmazonRootCA1.pem"       #Point to RootCA1 loaded onto Raspy

# 3. Create the Connection Object
mqtt_connection = mqtt_connection_builder.mtls_from_path(
    endpoint=ENDPOINT,
    cert_filepath=PATH_TO_CERT,
    pri_key_filepath=PATH_TO_KEY,
    ca_filepath=PATH_TO_ROOT_CA,
    client_id=CLIENT_ID,
    clean_session=False,
    keep_alive_secs=30
)

# 4. Open the Connection
print("Connecting...")
connect_future = mqtt_connection.connect()
connect_future.result() 
print("Connected!")

def decode_lora_packet(raw_input):

    # Remove AT command wrapper if present
    # This part of the code if for testing purposes, once added to the AWS code 
    ## the recieved message will have "+RCV=..." format, so thispart is cruusial
    if "AT+SEND" in raw_input or "+RCV=" in raw_input:
        try:
            #extracting LoRa HEX message
            hex_payload = raw_input.split(",")[2].strip()

            print("HEX Payload:", hex_payload)

            # Convert HEX → 32-bit binary
            raw_input = bin(int(hex_payload, 16))[2:].zfill(32)

            print("Binary (32-bit):", raw_input)
        except:
            print("Invalid AT format.")
            return

    # because the dollar signs have to be removed anyways, the incoming payload can be recieved 
    # as a binary string entirely 
    #binary_string = raw_input.replace("$", "") 


    # ---------------- Safety Check 1: Length (32 bits expected)
    if len(raw_input) != 32:
        print("ERROR!! Packet is not 32 bits.")
        print("Length received:", len(raw_input))
        return

    # --------------- Safety Check 2: Even Parity (MSB coming into play) 
    parity_bit = int(raw_input[0])  # MSB
    data_bits = raw_input[1:]

    ones_count = data_bits.count('1')

    expected_parity = ones_count % 2  # 0 if even, 1 if odd

    if expected_parity != parity_bit:
        print("ERROR!! Parity check failed.")
        print("Parity bit:", parity_bit)
        # print("Expected parity:", expected_parity)
        return

    print("***Parity check passed**.")

    # -------------separating the bits according to their respective data fields
    node_type_bits = raw_input[-3:]     # Node Type
    node_id_bits = raw_input[-11:-3]    # Node ID
    health_bits = raw_input[-13:-11]    # Health Class
    battery_bits = raw_input[-20:-13]   # Battery Level
    soil_bits = raw_input[-31:-20]      # Soil Moisture

    node_type_map = {
        0: "Gateway",
        1: "Cluster Node",
        2: "Field Node",
        3: "Overhead Node"
    }

    health_map = {
        0: "Bacterial",
        1: "Healthy",
        2: "Invalid"
    }
    
    # -------------converting binary clusters to integers for easier interpretation
    node_type = int(node_type_bits, 2)
    node_id = int(node_id_bits, 2)
    health_class = int(health_bits, 2)
    battery = int(battery_bits, 2)
    soil_moisture = int(soil_bits, 2)
    
    # -------------Adding more complexity to Node ID
    node_prefix_map = {
    0: "GW",
    1: "CN",
    2: "FN",
    3: "ON"
    }

    prefix = node_prefix_map.get(node_type, "UN")
    formatted_number = f"{node_id:06d}"
    full_node_id = f"{prefix}{formatted_number}"


    # ****************** soil moisture interpretation ******************
    
    SOIL_MIN = 200  # max amount of water content in the soil (completely wet)
    SOIL_MAX = 2000 # min amount of water content in the soil (completely dry)

    # duue to noise and other factors, the soil moisture value might go beyond
    # the expected range, so we will cap it within the min and max values for a more accurate percentage calculation
    soil_raw = max(SOIL_MIN, min(soil_moisture, SOIL_MAX))

    soil_percent = (SOIL_MAX - soil_raw) / (SOIL_MAX - SOIL_MIN) * 100
    soil_percent = round(soil_percent, 1)

    #cathegorizing what each percentage range mean for the soil condition
    if soil_percent > 70:
        moisture_status = "Very Wet"
    elif soil_percent > 40:
        moisture_status = "Moist"
    elif soil_percent > 20:
        moisture_status = "Dry"
    else:
        moisture_status = "Very Dry"

 
    # ------------- Final Output -------------

    node_type_label = node_type_map.get(node_type, "unknown")
    health_type_lable = health_map.get(health_class, "Reserved")

    moist = int(22)

    print("\n--- Decoded Packet ---")
    print("Device ID     :", CLIENT_ID)
    print("Node Type     :", node_type_label)
    print("Node ID       :", full_node_id)
    print("Health Class  :", health_type_lable)
    print("Battery (%)   :", battery)
    print("Soil Moisture :", moist)
    print("-----------------------\n")
    
    payload = {
    "device_id": str(CLIENT_ID),
    "timestamp": int(time.time()),
    "node_type": node_type_label,
    "node_id": full_node_id,
    "health_class": health_type_lable,
    "Battery": str(battery),
    "Soil_Moisture": str(moist),
    }

    mqtt_connection.publish(
    topic="farm/sensors",
    payload=json.dumps(payload),
    qos=mqtt.QoS.AT_LEAST_ONCE
    )
    
    print("Published to AWS:", payload)



# ---- Terminal Input ----
if __name__ == "__main__":
    while True:
        user_input = input("Enter received LoRa packet: ")
        decode_lora_packet(user_input)
        
        #AT+SEND=6,8,84564871
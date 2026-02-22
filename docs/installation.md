# Installation Details

> [!CAUTION]
> Disconnect the power to your opener before installation.

### Pico → Relay

| Pico Pin | Relay Pin |
|----------|-----------|
| GP17     | IN2       |
| GP16     | IN1       |
| GND      | GND       |
| VSYS     | VCC (5V)  |

>The "IN" pin corresponds to the relay you use on your board.
Adjust GPIO pins as needed in the code.
Use both IN1 and IN2 when wiring two garage doors. If not, use one.
---

### Relay → Garage Opener

For each door:

| Relay Terminal | Opener Terminal |
|----------------|-----------------|
| COM            | Wall terminal   |
| NO             | Wall terminal   |

- Leave NC unused.
- Keep existing wall button wires connected.
- It doesn't matter which order, but which terminals do. Check where your garage's wall buttons connect.
> [!IMPORTANT]
> Check if your wall buttons still work; stuff happens. Better to be safe.

---

### Optional Vibration Sensor

| Sensor Pin | Pico Pin |
|------------|----------|
| VCC        | 3V3      |
| GND        | GND      |
| DO         | GP14     |

Used only for movement detection, not for triggering the relay.

---

## Software Setup

### 1. Install Thonny
https://thonny.org

### 2. Flash MicroPython on Pico
- In the bottom right corner, click the Interpreter, then Configure interpreter.
- At the top, select the Interpreter "MicroPython (RP2040)"
- Click "Install or update MicroPython"
- Choose your Pico as the Target Volume
- MicroPython Family: RP2
- Variant: Raspberry Pi Pico 2 W
- Install

### 3. Upload Files
- Paste in `garage.py`
- Save it to the Pico as `garage.py`
  
- Paste in `main.py`
- Save it to the Pico as `main.py`
> GarageLink will now auto-run on boot.

## Home Assistant Setup

GarageLink uses MQTT discovery.

>[!IMPORTANT]
>Make a new user in HomeAssistant for MQTT. You will use its details for the MQTT config.

Requirements:
- MQTT broker running
- Home Assistant installed
- MQTT integration enabled

Once connected, the following entities should appear:
- `cover.garage_door`
- Availability sensor (if applicable)
- Sync buttons

---

## Configuration

The table is what setting, and then which variable that setting is.

| Setting    | Variable       |
|------------|----------------|
| WiFi Name     | WIFI_SSID = “” |
| Wifi Password                               | WIFI_PASS = “” |   
| MQTT Host (Usually HomeAssistant IP)        | MQTT_BROKER=""            |
| MQTT Username         | MQTT_USER=""           |
| MQTT Password | MQTT_PASS=""

>[!NOTE]
>Make sure all of the necessary fields have been edited in `garage.py`

---

# Installation

### 1. Find install area
Decide and find the installation area near your garage opener. **Please** don't just put it on top of the door opener. You'll regret it down the line. Ideal to put it on your ceiling, 2-4 feet away. Further = Better (Kinda)

### 2. Install GarageLink Box
Drill or screw or tape or whatever your GarageLink box into your installation area. If you are too cool to print the one I made, make your own. I don't care. Make sure your wire fits before fully installing it.

### 3. Prepare and strip wires.
Strip your low-voltage wire to length and expose both ends on each side. Connect an optional LED to GPIO 12.

### 4. Connect it up
Connect everything up with the outlined wiring instructions above.

### 5. Done!
Plug in GarageLink and yay! If it doesn't work, check logs, and *please* feel free to create an issue on GitHub.

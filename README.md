# GarageLink
**A local, DIY smart garage controller built on the Raspberry Pi Pico 2 W.**

> [!IMPORTANT]
> GarageLink needs an existing HomeAssistant setup to function. You may need additional devices beyond those outlined in the ReadMe.

## Overview

GarageLink is a Home Assistant–integrated garage controller that simulates a wall button press using a relay.  
It connects over WiFi, publishes via MQTT, and adds movement-aware status correction (optional).

It works by momentarily bridging the same two terminals used by the wall button, effectively simulating a button press.

---

## Hardware Requirements

### 1. Raspberry Pi Pico 2 W
- Built-in WiFi
- Controls relays and sensors
- Connects everything

### 2. 5V Relay Module
- Used to simulate a wall button press
- COM and NO terminals only
- Optocoupled boards preferred

### 3. Low-Voltage Wire / Thermostat / Doorbell Wire (18/2 or 22/2 solid copper)
- Pretty cheap on Amazon
- Doorbell, Thermostat, and low-voltage wire are all basically the same.
- Used to connect the relay to the opener terminals
- **Highly** recommended to mount your GarageLink away from the main opener as the WiFi on GarageLink interferes with the RF signal your garage remote uses and your car uses.

### 4. Optional Sensors
- SW-420 vibration sensor
- Used to update the open/close status if an outside entity controls the door. (Wall button, HomeLink, etc.)
- Mark Open and Mark Closed triggers are published to HomeAssistant, too.

## 5. 5V Power Supply
- USB wall adapter works perfectly
- Check if you have a wall outlet near your garage; you probably do. If not, try not to use a battery pack as the voltage is unreliable, and who wants to charge their garage door?

---

## Wiring / Hardware Setup

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
  
- Create `main.py` containing: `import garage.py`
> GarageLink will now auto-run on boot.

## Home Assistant Setup

GarageLink uses MQTT discovery.

Requirements:
- MQTT broker running
- Home Assistant installed
- MQTT integration enabled

Once connected, the following entities should appear:
- `cover.garage_door`
- Availability sensor (if applicable)
- Optional sync buttons

---

## Configuration

The table is what setting, and then which variable that setting is.

| Setting    | Variable       |
|------------|----------------|
| WiFi Name     | WIFI_SSID = “” |
| Wifi Password                               | WIFI_PASS = “” |   
| MQTT Host (Usually HomeAssistant IP)        | MQTT_BROKER=""            |
| MQTT Username         | MQTT_USER=""           |

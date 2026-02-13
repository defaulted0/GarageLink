# GarageLink
**A local, DIY smart garage controller built on the Raspberry Pi Pico 2 W.**

> [!IMPORTANT]
> GarageLink needs an existing HomeAssistant setup to function. You may need additional devices beyond those outlined in the ReadMe.

GarageLink is a Home Assistant–integrated garage controller that simulates a wall button press using a relay.  
It connects over WiFi, publishes via MQTT, and adds movement-aware status correction (optional).

## Overview

GarageLink allows you to control one or more garage doors using a Raspberry Pi Pico 2 W and a relay module.

It works by momentarily bridging the same two terminals used by the wall button, effectively simulating a button press.

Optional sensors (such as vibration detection) can be used to improve state awareness.

---

## Hardware Requirements

### 1. Raspberry Pi Pico 2 W
- Built-in WiFi
- Controls relays and sensors
- Connects everything

### 2. 5V Relay Module (2 Channel Preferred)
- Used to simulate a wall button press
- COM and NO terminals only
- Optocoupled boards preferred

### 3. Low-Voltage Wire (18/2 or 22/2 solid copper)
- Doorbell or thermostat wire recommended
- Used to connect the relay to the opener terminals
- **Highly** recommended to mount your GarageLink away from the main opener as the WiFi on GarageLink interferes with the RF signal your garage remote uses and your car uses.

### 4. Optional Sensors
- SW-420 vibration sensor

## 5. 5V Power Supply
- USB wall adapter
- Check if you have a wall outlet near your garage; you probably do. If not, try not to use a battery pack as the voltage is reliable and run time.

---

## Wiring

> [!CAUTION]
> Always disconnect the power to your opener before installation.

### Pico → Relay

| Pico Pin | Relay Pin |
|----------|-----------|
| GP17     | IN2       |
| GP16     | IN1 (optional) |
| GND      | GND       |
| VSYS     | VCC (5V)  |

The "IN" pin corresponds to the relay you use on your board.
Adjust GPIO pins as needed in the code.

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

### 2. Install MicroPython on Pico
- Select interpreter: MicroPython (RP2040)
- Install/update firmware

### 3. Upload Files
- Upload `garage.py`
- Create `main.py` containing:

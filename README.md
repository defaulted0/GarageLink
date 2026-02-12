# GarageLink
**A local, DIY smart garage controller built on the Raspberry Pi Pico 2 W.**

> [!IMPORTANT]
> GarageLink needs an existing HomeAssistant setup to function. You may need extra devices other than outlined in the ReadME.

GarageLink is a Home Assistant–integrated garage controller that simulates a wall button press using a relay.  
It connects over WiFi, publishes via MQTT, and adds movement-aware status correction.

## Overview

GarageLink allows you to control one or more garage doors using a Raspberry Pi Pico 2 W and a relay module.

It works by momentarily bridging the same two terminals used by the wall button, effectively simulating a button press.

Optional sensors (such as vibration detection) can be used to improve state awareness.

Key Idea: **Have a local, always-available, easy setup, way to open and close a garage door.**

---

# Features

- MQTT auto-discovery for Home Assistant
- Native `cover.*` entity support
- Multi-door capable (depending on relay channels)
- Optional vibration-based movement detection
- Arrival notifications with actionable buttons
- Manual state correction buttons
- Fully local operation

---

# Hardware Requirements

## 1. Raspberry Pi Pico 2 W
- Built-in WiFi
- Runs MicroPython
- Controls relays and sensors

## 2. 5V Relay Module (4-channel recommended)
- Used to simulate wall button press
- COM and NO terminals only
- Optocoupled boards preferred

## 3. Low-Voltage Wire (18/2 or 22/2 solid copper)
- Doorbell or thermostat wire recommended
- Used to connect relay to opener terminals

## 4. Optional Sensors
- SW-420 vibration sensor
- Reed switch (magnetic contact)

## 5. 5V Power Supply
- USB wall adapter
- Do not power from opener logic board

---

# Wiring

## Pico → Relay

| Pico Pin | Relay Pin |
|----------|-----------|
| GP17     | IN2       |
| GP16     | IN1 (optional) |
| GND      | GND       |
| VSYS     | VCC (5V)  |

Adjust GPIO pins as needed in the code.

---

## Relay → Garage Opener

For each door:

| Relay Terminal | Opener Terminal |
|----------------|-----------------|
| COM            | Wall terminal 1 |
| NO             | Wall terminal 2 |

- Leave NC unused.
- Keep existing wall button wires connected.
- You are wiring in parallel.

Polarity does not matter.

---

## Optional Vibration Sensor

| Sensor Pin | Pico Pin |
|------------|----------|
| VCC        | 3V3      |
| GND        | GND      |
| DO         | GP14     |

Used only for movement detection, not for triggering the relay.

---

# Software Setup

## 1. Install Thonny
https://thonny.org

## 2. Install MicroPython on Pico
- Select interpreter: MicroPython (RP2040)
- Install/update firmware

## 3. Upload Files
- Upload `garage.py`
- Create `main.py` containing:

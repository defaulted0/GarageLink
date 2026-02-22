# LED Status Reference

GarageLink includes a single status LED to communicate system state without requiring Home Assistant access.

This LED provides live feedback about:

- WiFi connection
- MQTT connection
- Door position state
- Door movement
- Error or unknown states

This document explains exactly what each LED pattern means.

---

## Quick Reference

| LED Pattern | Meaning |
|------------|----------|
| Solid ON | System healthy, door CLOSED |
| Mostly ON, brief OFF pulse | System healthy, door OPEN |
| Slow blink (0.5s on / 0.5s off) | Door is moving |
| Double blink, pause | Unknown or stopped state |
| OFF | Not connected to MQTT |
| Short flash every ~2s | Reconnecting to MQTT |

---

## Detailed Behavior

### Solid ON

The LED remains continuously ON.

Indicates:
- WiFi connected
- MQTT connected
- System healthy
- Door state is known
- Door is CLOSED

This is the normal idle state.

---

### Mostly ON With Brief OFF Pulse

The LED stays ON but briefly turns OFF every few seconds.

Indicates:
- WiFi connected
- MQTT connected
- Door is OPEN

This subtle pulse acts as a reminder that the garage door is not closed.

---

### Slow Blink (500ms On / 500ms Off)

The LED blinks evenly at a steady rhythm.

Indicates:
- Door is OPENING
- Door is CLOSING

This state occurs:
- After a command is sent
- When movement is detected

---

### Double Blink Pattern

Two quick flashes followed by a pause.

Indicates:
- Door state is UNKNOWN
- Door state is STOPPED
- System recently rebooted
- State synchronization incomplete

This usually resolves once the door state is confirmed.

---

### LED OFF

The LED remains completely OFF.

Indicates:
- Not connected to MQTT
- Broker unreachable
- Network failure
- Device booting but not yet connected

If the LED remains OFF for more than 30 seconds after boot, check:

- WiFi credentials
- MQTT broker IP
- Power supply

---

### Short Flash Every ~2 Seconds

Single short flash at regular intervals.

Indicates:
- Attempting to reconnect to MQTT
- Temporary network interruption

The LED will return to normal state once MQTT reconnects.

---

### Startup Indicators

On boot, the LED provides quick visual confirmation:

- 2 quick flashes → WiFi connected
- 3 quick flashes → MQTT connected

After startup completes, the LED switches to standard operating patterns.

---

### Hardware Wiring

Standard wiring configuration:

- GPIO 12 → 330Ω resistor → LED anode (long leg)
- LED cathode (short leg) → GND

The resistor may be placed on either side of the LED.

---

### Notes

- LED patterns are designed for low visual noise.
- Only one LED is used.
- No RGB or multi-color signaling is implemented.
- System health is primarily reflected by MQTT connectivity.

**Start a discussion or fork if you want to change anything or have any better ideas!**

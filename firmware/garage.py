# GarageLink by default
# ------------------------------------------------
print("[BOOT] Pico garage script starting")

import time
import machine    # type: ignore
import network    # type: ignore
import ubinascii  # type: ignore
import ujson      # type: ignore

# MQTT library (make sure /lib/umqtt/simple.py exists on the Pico)
from umqtt.simple import MQTTClient  # type: ignore


# ================================================================                        EDIT HERE!!!!
# USER SETTINGS  (EDIT THESE)                                                         <-------------
# ================================================================
WIFI_SSID = "YOUR_WIFI_NAME"
WIFI_PASS = "YOUR_WIFI_PASSWORD"

MQTT_BROKER = ""     # <--- usually just the ip of your homeassistant host
MQTT_PORT   = 1883
MQTT_USER   = ""
MQTT_PASS   = ""

BASE_TOPIC  = "pico2w/garage1"

# Relay output (your relay IN2 is on GP17)
RELAY_PIN = 17
RELAY_ACTIVE_LOW = True

# Pulse duration (button press length)
PULSE_MS   = 500
LOCKOUT_MS = 3000

# Estimated travel time (used for opening/closing status)
TRAVEL_MS = 14000
IGNORE_WHILE_MOVING = True

# Status LED
LED_PIN = 12
LED_ACTIVE_HIGH = True

# Door position sensor (reed) - OFF by default
USE_DOOR_SENSOR = False
DOOR_PIN = 14
DOOR_OPEN_WHEN_PIN_LOW = True

# Vibration sensor (SW-420) - OFF by default
USE_VIBRATION = False
VIB_PIN = 14
VIB_ACTIVE_HIGH = True
VIB_MIN_MS = 2000                 # must vibrate this long to count as motion
VIB_IGNORE_AFTER_CMD_MS = 3000    # ignore vibration right after relay press
VIB_NO_MOVE_ALERT_MS = 6000       # publish alert if no vibration after command
VIB_END_QUIET_MS = 1500           # how long of quiet to consider motion ended
# ================================================================


# ----------------------------
# Topics
# ----------------------------
CMD_TOPIC    = BASE_TOPIC + "/command"       # HA -> Pico
SYNC_TOPIC   = BASE_TOPIC + "/sync"          # HA -> Pico (mark open/closed)
STATUS_TOPIC = BASE_TOPIC + "/status"        # Pico -> HA (cover state)
STATE_TOPIC  = BASE_TOPIC + "/door_state"    # Pico -> HA (binary sensor if reed enabled)
AVAIL_TOPIC  = BASE_TOPIC + "/availability"  # online/offline
ALERT_TOPIC  = BASE_TOPIC + "/alert"         

DISCOVERY_PREFIX = "homeassistant"


# LED helpers
wifi_ok = False
mqtt_ok = False
led_state = "UNKNOWN"
led_trying = False
_led_last_ms = 0
_led_phase = 0
_led_on = False

def led_init():
    try:
        return machine.Pin(LED_PIN, machine.Pin.OUT)
    except Exception:
        try:
            return machine.Pin(25, machine.Pin.OUT)
        except Exception:
            return None

def led_set(led, on: bool):
    if led is None:
        return
    val = 1 if on else 0
    if not LED_ACTIVE_HIGH:
        val ^= 1
    led.value(val)

def led_blink(led, count=1, on_ms=120, off_ms=120):
    if led is None:
        return
    for _ in range(count):
        led_set(led, True)
        time.sleep_ms(on_ms)
        led_set(led, False)
        time.sleep_ms(off_ms)

def led_tick(led, est_state_now: str):
    global _led_last_ms, _led_phase, _led_on

    if led is None:
        return

    s = (est_state_now or "UNKNOWN").upper()
    now = time.ticks_ms()

    if not mqtt_ok:
        if not led_trying:
            led_set(led, False)
            _led_on = False
            _led_phase = 0
            _led_last_ms = now
            return

        # trying
        if _led_phase == 0:
            led_set(led, True)
            _led_on = True
            _led_phase = 1
            _led_last_ms = now
        else:
            if _led_on and time.ticks_diff(now, _led_last_ms) >= 120:
                led_set(led, False)
                _led_on = False
            if time.ticks_diff(now, _led_last_ms) >= 2000:
                _led_phase = 0
                _led_last_ms = now
        return

    if s == "CLOSED":
        led_set(led, True)
        _led_on = True
        _led_phase = 0
        _led_last_ms = now
        return

    if s == "OPEN":
        if time.ticks_diff(now, _led_last_ms) >= 3000:
            _led_last_ms = now
            _led_phase = 0
        if _led_phase == 0:
            led_set(led, False)
            _led_on = False
            _led_phase = 1
            _led_last_ms = now
        elif _led_phase == 1 and time.ticks_diff(now, _led_last_ms) >= 120:
            led_set(led, True)
            _led_on = True
            _led_phase = 2
        return

    if s in ("OPENING", "CLOSING"):
        if time.ticks_diff(now, _led_last_ms) >= 500:
            _led_last_ms = now
            _led_on = not _led_on
            led_set(led, _led_on)
        return

    # unknown/stopped
    if _led_phase == 0:
        led_set(led, True)
        _led_on = True
        _led_phase = 1
        _led_last_ms = now
    elif _led_phase == 1 and time.ticks_diff(now, _led_last_ms) >= 120:
        led_set(led, False)
        _led_on = False
        _led_phase = 2
        _led_last_ms = now
    elif _led_phase == 2 and time.ticks_diff(now, _led_last_ms) >= 120:
        led_set(led, True)
        _led_on = True
        _led_phase = 3
        _led_last_ms = now
    elif _led_phase == 3 and time.ticks_diff(now, _led_last_ms) >= 120:
        led_set(led, False)
        _led_on = False
        _led_phase = 4
        _led_last_ms = now
    elif _led_phase == 4 and time.ticks_diff(now, _led_last_ms) >= 2640:
        _led_phase = 0
        _led_last_ms = now


# wifi/mqtt
def wifi_connect(led=None):
    global wifi_ok
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    print("[WIFI] Connecting to:", WIFI_SSID)

    try:
        hostname = "garagelink-" + ubinascii.hexlify(machine.unique_id())[-4:].decode()
        wlan.config(dhcp_hostname=hostname)
    except Exception:
        pass

    if wlan.isconnected():
        ip = wlan.ifconfig()[0]
        print("[WIFI] Already connected, IP:", ip)
        wifi_ok = True
        return wlan

    wlan.connect(WIFI_SSID, WIFI_PASS)
    t0 = time.ticks_ms()
    while not wlan.isconnected():
        if time.ticks_diff(time.ticks_ms(), t0) > 20000:
            raise RuntimeError("WiFi connect timeout")
        time.sleep_ms(250)

    ip = wlan.ifconfig()[0]
    print("[WIFI] Connected, IP:", ip)
    wifi_ok = True
    led_blink(led, count=2)
    return wlan

def mqtt_connect(client_id, will_topic, will_msg, led=None):
    global mqtt_ok
    print("[MQTT] Connecting to broker:", MQTT_BROKER)

    cid = client_id if isinstance(client_id, (bytes, bytearray)) else str(client_id).encode()
    usr = MQTT_USER.encode() if MQTT_USER else None
    pwd = MQTT_PASS.encode() if MQTT_PASS else None

    c = MQTTClient(
        client_id=cid,
        server=MQTT_BROKER,
        port=int(MQTT_PORT),
        user=usr,
        password=pwd,
        keepalive=60
    )
    c.set_last_will(will_topic, will_msg, retain=True, qos=0)
    c.connect()

    mqtt_ok = True
    print("[MQTT] Connected")
    led_blink(led, count=3)
    return c


# Home Assistant Discovery (MQTT)
def publish_discovery(client, unique, device_name):
    # Cover entity
    cover_id = unique + "_cover"
    cover_cfg_topic = f"{DISCOVERY_PREFIX}/cover/{cover_id}/config"
    cover_cfg = {
        "name": "GarageLink",   # just rename in homeassistant
        "unique_id": cover_id,
        "command_topic": CMD_TOPIC,
        "state_topic": STATUS_TOPIC,
        "availability_topic": AVAIL_TOPIC,
        "payload_available": "online",
        "payload_not_available": "offline",
        "payload_open": "OPEN",
        "payload_close": "CLOSE",
        "payload_stop": "STOP",
        "state_open": "OPEN",
        "state_opening": "OPENING",
        "state_closed": "CLOSED",
        "state_closing": "CLOSING",
        "state_stopped": "STOPPED",
        "device": {
            "identifiers": [unique],
            "name": device_name,
            "manufacturer": "Raspberry Pi",
            "model": "Pico 2 W",
        }
    }
    client.publish(cover_cfg_topic, ujson.dumps(cover_cfg), retain=True)
    print("[MQTT] Discovery cover published")

    # Door binary sensor (reed)
    if USE_DOOR_SENSOR:
        sensor_id = unique + "_door"
        sensor_cfg_topic = f"{DISCOVERY_PREFIX}/binary_sensor/{sensor_id}/config"
        sensor_cfg = {
            "name": "Garage Door Open",
            "unique_id": sensor_id,
            "state_topic": STATE_TOPIC,
            "payload_on": "OPEN",
            "payload_off": "CLOSED",
            "device_class": "garage_door",
            "availability_topic": AVAIL_TOPIC,
            "payload_available": "online",
            "payload_not_available": "offline",
            "device": {
                "identifiers": [unique],
                "name": device_name,
                "manufacturer": "Raspberry Pi",
                "model": "Pico 2 W",
            }
        }
        client.publish(sensor_cfg_topic, ujson.dumps(sensor_cfg), retain=True)
        print("[MQTT] Discovery door sensor published")

    # Sync buttons
    sync_open_id = unique + "_sync_open"
    sync_open_cfg_topic = f"{DISCOVERY_PREFIX}/button/{sync_open_id}/config"
    sync_open_cfg = {
        "name": "Garage: Mark Open",
        "unique_id": sync_open_id,
        "command_topic": SYNC_TOPIC,
        "payload_press": "OPEN",
        "availability_topic": AVAIL_TOPIC,
        "payload_available": "online",
        "payload_not_available": "offline",
        "icon": "mdi:garage-open",
        "device": {
            "identifiers": [unique],
            "name": device_name,
            "manufacturer": "Raspberry Pi",
            "model": "Pico 2 W",
        }
    }
    client.publish(sync_open_cfg_topic, ujson.dumps(sync_open_cfg), retain=True)

    sync_closed_id = unique + "_sync_closed"
    sync_closed_cfg_topic = f"{DISCOVERY_PREFIX}/button/{sync_closed_id}/config"
    sync_closed_cfg = {
        "name": "Garage: Mark Closed",
        "unique_id": sync_closed_id,
        "command_topic": SYNC_TOPIC,
        "payload_press": "CLOSED",
        "availability_topic": AVAIL_TOPIC,
        "payload_available": "online",
        "payload_not_available": "offline",
        "icon": "mdi:garage",
        "device": {
            "identifiers": [unique],
            "name": device_name,
            "manufacturer": "Raspberry Pi",
            "model": "Pico 2 W",
        }
    }
    client.publish(sync_closed_cfg_topic, ujson.dumps(sync_closed_cfg), retain=True)
    print("[MQTT] Discovery sync buttons published")
# Relay control
def make_relay(pin_num):
    pin = machine.Pin(pin_num, machine.Pin.IN)  # Hi-Z idle
    print("[RELAY] Idle set to Hi-Z (Pin.IN) on GP", pin_num)
    return pin

def relay_pulse(relay_pin, led=None):
    print("[RELAY] Pulse triggered")
    # optional quick blink to show activity
    led_blink(led, count=2, on_ms=120, off_ms=120)

    if RELAY_ACTIVE_LOW:
        relay_pin.init(machine.Pin.OUT)
        relay_pin.value(0)
        time.sleep_ms(PULSE_MS)
        relay_pin.init(machine.Pin.IN)
    else:
        relay_pin.init(machine.Pin.OUT)
        relay_pin.value(1)
        time.sleep_ms(PULSE_MS)
        relay_pin.init(machine.Pin.IN)

    print("[RELAY] Returned to Hi-Z (Pin.IN)")

# Door sensor (reed) helper
def read_door_state(door_pin):
    v = door_pin.value()
    is_open = (v == 0) if DOOR_OPEN_WHEN_PIN_LOW else (v == 1)
    return "OPEN" if is_open else "CLOSED"

# Vibration helper
def vib_active(vpin):
    v = vpin.value()
    return (v == 1) if VIB_ACTIVE_HIGH else (v == 0)


# ----------------------------
# Main
# ----------------------------
unique = ubinascii.hexlify(machine.unique_id()).decode()
device_name = "GarageLink Controller"

led = led_init()
led_set(led, False)
print("[LED] Status LED init:", bool(led))

relay = make_relay(RELAY_PIN)
print("[RELAY] Initialized on GP", RELAY_PIN, "active_low =", RELAY_ACTIVE_LOW)

door_pin = None
last_door = None
if USE_DOOR_SENSOR:
    door_pin = machine.Pin(DOOR_PIN, machine.Pin.IN, machine.Pin.PULL_UP)
    last_door = read_door_state(door_pin)
    print("[DOOR] Initial:", last_door)

vpin = None
if USE_VIBRATION:
    vpin = machine.Pin(VIB_PIN, machine.Pin.IN)
    print("[VIB] Enabled on GP", VIB_PIN)

# State machine
est_state = "UNKNOWN"  # UNKNOWN/OPENING/CLOSING/OPEN/CLOSED/STOPPED Must open or close first to set state on boot!
move_end_ms = None
last_press_ms = 0

# Vibration logic state
_cmd_ms = None
_expect_motion = False
_vib_start_ms = None
_last_vib_ms = None
_motion_confirmed = False


def publish_status(client, state, retain=True):
    global est_state
    est_state = state
    try:
        client.publish(STATUS_TOPIC, state, retain=retain)
        print("[STATUS] ->", state)
    except Exception as e:
        print("[STATUS] publish failed:", e)

def publish_alert(client, text):
    try:
        client.publish(ALERT_TOPIC, text, retain=False)
        print("[ALERT] ->", text)
    except Exception as e:
        print("[ALERT] publish failed:", e)


def on_mqtt_msg(topic, msg):
    global last_press_ms, est_state, move_end_ms
    global _cmd_ms, _expect_motion, _motion_confirmed

    t = topic.decode() if isinstance(topic, (bytes, bytearray)) else str(topic)
    m = msg.decode().strip().upper()
    now = time.ticks_ms()
    print("[MQTT] RX:", t, m)

    # Sync buttons: correct state without moving
    if t == SYNC_TOPIC:
        if m in ("OPEN", "CLOSED", "UNKNOWN", "STOPPED"):
            move_end_ms = None
            publish_status(client, m, retain=True)
        return

    if t != CMD_TOPIC:
        return

    if m not in ("OPEN", "CLOSE", "STOP", "TRIGGER", "TOGGLE", "PRESS", "ON", "1"):
        return

    # Lockout
    if time.ticks_diff(now, last_press_ms) < LOCKOUT_MS:
        print("[RELAY] Ignored (lockout)")
        return

    # STOP: only meaningful while moving
    if m == "STOP":
        if est_state in ("OPENING", "CLOSING"):
            last_press_ms = now
            relay_pulse(relay, led=led)
            publish_status(client, "STOPPED", retain=True)
        return

    # Ignore while moving (optional)
    if IGNORE_WHILE_MOVING and est_state in ("OPENING", "CLOSING"):
        print("[STATE] Ignored (already moving):", est_state)
        return

    # Trigger relay
    last_press_ms = now
    relay_pulse(relay, led=led)

    # Mark that we "expect" motion soon (for vibration alert logic)
    _cmd_ms = now
    _expect_motion = True
    _motion_confirmed = False

    # Update estimated movement state
    if m == "OPEN":
        publish_status(client, "OPENING", retain=True)
    elif m == "CLOSE":
        publish_status(client, "CLOSING", retain=True)
    else:
        # toggle
        if est_state in ("CLOSED", "CLOSING", "UNKNOWN", "STOPPED"):
            publish_status(client, "OPENING", retain=True)
        else:
            publish_status(client, "CLOSING", retain=True)

    move_end_ms = time.ticks_add(now, TRAVEL_MS)


def safe_sleep_ms(ms):
    step = 50
    remaining = ms
    while remaining > 0:
        time.sleep_ms(step if remaining > step else remaining)
        remaining -= step


# Connect WiFi + MQTT
wifi_connect(led)

client_id = b"garagelink-" + ubinascii.hexlify(machine.unique_id())
client = mqtt_connect(client_id, AVAIL_TOPIC, b"offline", led=led)

client.set_callback(on_mqtt_msg)

client.subscribe(CMD_TOPIC.encode())
client.subscribe(SYNC_TOPIC.encode())
print("[MQTT] Subscribed:", CMD_TOPIC, "and", SYNC_TOPIC)

client.publish(AVAIL_TOPIC, b"online", retain=True)
print("[MQTT] Availability online")

publish_discovery(client, unique, device_name)

# Publish initial states
if USE_DOOR_SENSOR and last_door is not None:
    client.publish(STATE_TOPIC, last_door, retain=True)
    publish_status(client, last_door, retain=True)
else:
    publish_status(client, est_state, retain=True)


# Main loop
while True:
    try:
        client.check_msg()

        # LED tick
        led_tick(led, est_state)

        now = time.ticks_ms()

        # If no door sensor, timer completes OPENING/CLOSING into OPEN/CLOSED
        if (not USE_DOOR_SENSOR) and move_end_ms is not None and time.ticks_diff(now, move_end_ms) >= 0:
            if est_state == "OPENING":
                publish_status(client, "OPEN", retain=True)
            elif est_state == "CLOSING":
                publish_status(client, "CLOSED", retain=True)
            move_end_ms = None

        # Door sensor overrides estimate (true open/closed)
        if USE_DOOR_SENSOR and door_pin is not None:
            current = read_door_state(door_pin)
            if current != last_door:
                last_door = current
                print("[DOOR] Changed:", current)
                client.publish(STATE_TOPIC, current, retain=True)
                move_end_ms = None
                publish_status(client, current, retain=True)

        # Vibration-based movement detection (state correction only)
        if USE_VIBRATION and vpin is not None:
            active = vib_active(vpin)

            if active:
                if _vib_start_ms is None:
                    _vib_start_ms = now
                _last_vib_ms = now

                # Confirm sustained motion
                if time.ticks_diff(now, _vib_start_ms) >= VIB_MIN_MS:
                    _motion_confirmed = True
            else:
                _vib_start_ms = None

            # Ignore vibration shortly after command (relay click / motor startup noise)
            if _cmd_ms is not None and time.ticks_diff(now, _cmd_ms) < VIB_IGNORE_AFTER_CMD_MS:
                pass
            else:
                # If motion confirmed, flip direction based on current state (your rule)
                if _motion_confirmed:
                    if est_state in ("CLOSED", "CLOSING", "UNKNOWN", "STOPPED"):
                        publish_status(client, "OPENING", retain=True)
                    else:
                        publish_status(client, "CLOSING", retain=True)
                    _motion_confirmed = False

            # Motion ended (quiet for a while) -> finalize opposite (estimated)
            if _last_vib_ms is not None and time.ticks_diff(now, _last_vib_ms) > VIB_END_QUIET_MS:
                if est_state == "OPENING":
                    publish_status(client, "OPEN", retain=True)
                elif est_state == "CLOSING":
                    publish_status(client, "CLOSED", retain=True)

                _last_vib_ms = None
                _expect_motion = False

            # If we commanded movement but saw no vibration in time -> alert
            if _expect_motion and _cmd_ms is not None and time.ticks_diff(now, _cmd_ms) > VIB_NO_MOVE_ALERT_MS:
                publish_alert(client, "Command sent but no vibration detected. Door may not have moved.")
                _expect_motion = False

        safe_sleep_ms(100)

    except OSError:
        print("[ERROR] MQTT/WiFi error, reconnecting...")
        mqtt_ok = False
        led_trying = True
        led_tick(led, est_state)

        try:
            client.publish(AVAIL_TOPIC, b"offline", retain=True)
        except Exception:
            pass

        # Reconnect WiFi if needed
        try:
            wlan = network.WLAN(network.STA_IF)
            if not wlan.isconnected():
                wifi_connect(led)
        except Exception:
            pass

        # Reconnect MQTT loop
        while True:
            try:
                client = mqtt_connect(client_id, AVAIL_TOPIC, b"offline", led=led)
                led_trying = False
                mqtt_ok = True

                client.set_callback(on_mqtt_msg)
                client.subscribe(CMD_TOPIC.encode())
                client.subscribe(SYNC_TOPIC.encode())

                client.publish(AVAIL_TOPIC, b"online", retain=True)
                publish_discovery(client, unique, device_name)

                if USE_DOOR_SENSOR and last_door is not None:
                    client.publish(STATE_TOPIC, last_door, retain=True)

                publish_status(client, est_state, retain=True)
                break
            except Exception:
                time.sleep(2)

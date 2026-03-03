"""
tier_classifier.py — Natural-language to MCU tier classifier for Eisla.

Takes a plain-English project description and returns a structured spec:
  - MCU tier (1 / 2 / 3)
  - Suggested MCU family
  - Required peripherals and interfaces
  - Estimated complexity

In production this would call the Claude API.  For the prototype it uses
keyword matching so the pipeline can run without an API key.
"""

from dataclasses import dataclass, field
from typing import Optional


# ── MCU families by tier (mirrors Eisla pricing tiers) ──────────────────────

TIER_1_MCUS = {
    "atmega328p":  {"family": "ATmega",   "core": "AVR",       "flash": "32KB",  "ram": "2KB"},
    "esp8266":     {"family": "ESP8266",  "core": "Xtensa",    "flash": "4MB",   "ram": "80KB"},
    "stm32f030":   {"family": "STM32F0",  "core": "Cortex-M0", "flash": "64KB",  "ram": "8KB"},
}

TIER_2_MCUS = {
    "esp32":       {"family": "ESP32",    "core": "Xtensa",    "flash": "4MB",   "ram": "520KB"},
    "rp2040":      {"family": "RP2040",   "core": "Cortex-M0+","flash": "16MB",  "ram": "264KB"},
    "nrf52840":    {"family": "nRF52840", "core": "Cortex-M4", "flash": "1MB",   "ram": "256KB"},
}

TIER_3_MCUS = {
    "stm32h743":   {"family": "STM32H7",  "core": "Cortex-M7", "flash": "2MB",   "ram": "1MB"},
    "imxrt1062":   {"family": "i.MX RT",  "core": "Cortex-M7", "flash": "ext",   "ram": "1MB"},
}


# ── Keyword → peripheral mapping ───────────────────────────────────────────

PERIPHERAL_KEYWORDS = {
    "wifi":        "wifi",
    "wi-fi":       "wifi",
    "wireless":    "wifi",
    "bluetooth":   "bluetooth",
    "ble":         "bluetooth",
    "usb":         "usb",
    "usb-c":       "usb",
    "uart":        "uart",
    "serial":      "uart",
    "spi":         "spi",
    "i2c":         "i2c",
    "i²c":         "i2c",
    "adc":         "adc",
    "analog":      "adc",
    "pwm":         "pwm",
    "motor":       "pwm",
    "servo":       "pwm",
    "led":         "led",
    "blink":       "led",
    "display":     "display",
    "oled":        "display",
    "lcd":         "display",
    "screen":      "display",
    "sensor":      "i2c",
    "temperature": "i2c",
    "humidity":    "i2c",
    "accelerometer":"i2c",
    "imu":         "spi",
    "gps":         "uart",
    "lora":        "spi",
    "can":         "can",
    "ethernet":    "ethernet",
    "camera":      "camera",
    "sd card":     "spi",
    "microsd":     "spi",
    "audio":       "i2s",
    "dac":         "dac",
    "relay":       "gpio",
    "button":      "gpio",
    "switch":      "gpio",
    "neopixel":    "pwm",
    "ws2812":      "pwm",
    "rgb":         "pwm",
}

# Keywords that push tier upward
TIER_ESCALATION = {
    "wifi":      2,
    "bluetooth": 2,
    "camera":    3,
    "ethernet":  3,
    "dac":       3,
    "i2s":       3,
    "dsp":       3,
    "high speed":3,
    "fast":      2,
    "low power": 2,
    "battery":   2,
}


@dataclass
class BoardSpec:
    """Structured specification extracted from a natural-language request."""
    description: str
    tier: int
    mcu: str
    mcu_info: dict
    peripherals: list[str] = field(default_factory=list)
    has_usb: bool = False
    has_debug: bool = True       # SWD header included by default
    has_power_led: bool = True   # status LED included by default
    power_source: str = "usb"    # "usb" | "barrel" | "battery"
    input_voltage: str = "5V"


def classify(description: str) -> BoardSpec:
    """Parse a natural-language project description into a BoardSpec."""
    text = description.lower()

    # ── Detect peripherals ──────────────────────────────────────────────
    peripherals = set()
    for keyword, peripheral in PERIPHERAL_KEYWORDS.items():
        if keyword in text:
            peripherals.add(peripheral)

    # ── Determine minimum tier ──────────────────────────────────────────
    min_tier = 1
    for keyword, tier in TIER_ESCALATION.items():
        if keyword in text:
            min_tier = max(min_tier, tier)

    # ── Check for explicit MCU mentions ─────────────────────────────────
    chosen_mcu = None
    chosen_info = None

    for mcu_id, info in {**TIER_3_MCUS, **TIER_2_MCUS, **TIER_1_MCUS}.items():
        if mcu_id in text or info["family"].lower() in text:
            chosen_mcu = mcu_id
            chosen_info = info
            # determine tier from which dict it came from
            if mcu_id in TIER_3_MCUS:
                min_tier = max(min_tier, 3)
            elif mcu_id in TIER_2_MCUS:
                min_tier = max(min_tier, 2)
            break

    # ── Default MCU selection per tier ──────────────────────────────────
    if chosen_mcu is None:
        if min_tier == 1:
            chosen_mcu = "atmega328p"
            chosen_info = TIER_1_MCUS[chosen_mcu]
        elif min_tier == 2:
            # prefer ESP32 if wifi requested, else RP2040
            if "wifi" in peripherals or "bluetooth" in peripherals:
                chosen_mcu = "esp32"
            else:
                chosen_mcu = "rp2040"
            chosen_info = TIER_2_MCUS[chosen_mcu]
        else:
            chosen_mcu = "stm32h743"
            chosen_info = TIER_3_MCUS[chosen_mcu]

    # ── Power source heuristics ─────────────────────────────────────────
    power_source = "usb"
    input_voltage = "5V"
    if "battery" in text or "lipo" in text:
        power_source = "battery"
        input_voltage = "3.7V"
    elif "12v" in text or "barrel" in text or "vin" in text:
        power_source = "barrel"
        input_voltage = "12V"

    has_usb = "usb" in peripherals or power_source == "usb"

    return BoardSpec(
        description=description,
        tier=min_tier,
        mcu=chosen_mcu,
        mcu_info=chosen_info,
        peripherals=sorted(peripherals),
        has_usb=has_usb,
        has_debug=True,
        has_power_led=True,
        power_source=power_source,
        input_voltage=input_voltage,
    )

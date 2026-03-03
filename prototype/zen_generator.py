"""
zen_generator.py — Generates a Zener board .zen file from a BoardSpec.

Takes the structured spec produced by tier_classifier and emits a complete
board composition that composes reusable modules (power, USB, debug, LEDs)
around an MCU component.

In the full Eisla pipeline, Claude would generate this directly from the
customer's NL description + the Zener module registry.  This prototype
shows the *shape* of that output so we can validate the architecture.
"""

import os
import textwrap
from datetime import date
from tier_classifier import BoardSpec


# ── MCU symbol definitions ──────────────────────────────────────────────────
# Simplified pin lists — real versions would come from the Zener registry.

MCU_DEFINITIONS = {
    "atmega328p": {
        "symbol_name": "ATmega328P-AU",
        "pins": [
            ("VCC",   ["7", "20"]),
            ("AVCC",  ["18"]),
            ("GND",   ["8", "22"]),
            ("AREF",  ["21"]),
            ("PB0",   ["14"]),
            ("PB1",   ["15"]),
            ("PB2",   ["16"]),
            ("PB3",   ["17"]),
            ("PB4",   ["2"]),
            ("PB5",   ["3"]),
            ("PC0",   ["23"]),
            ("PC1",   ["24"]),
            ("PC2",   ["25"]),
            ("PC3",   ["26"]),
            ("PC4",   ["27"]),
            ("PC5",   ["28"]),
            ("PD0",   ["30"]),
            ("PD1",   ["31"]),
            ("PD2",   ["32"]),
            ("PD3",   ["1"]),
            ("PD4",   ["9"]),
            ("PD5",   ["10"]),
            ("PD6",   ["11"]),
            ("PD7",   ["12"]),
            ("RESET", ["29"]),
            ("XTAL1", ["7"]),
            ("XTAL2", ["8"]),
        ],
        "vcc_pins": ["VCC", "AVCC"],
        "gnd_pins": ["GND"],
        "reset_pin": "RESET",
        "gpio_pins": ["PB0", "PB1", "PB2", "PB3", "PD2", "PD3", "PD4", "PD5", "PD6", "PD7"],
        "uart_tx": "PD1",
        "uart_rx": "PD0",
        "spi_pins": {"MOSI": "PB3", "MISO": "PB4", "SCK": "PB5", "SS": "PB2"},
        "i2c_pins": {"SDA": "PC4", "SCL": "PC5"},
    },
    "esp32": {
        "symbol_name": "ESP32-WROOM-32E",
        "pins": [
            ("3V3",    ["2"]),
            ("EN",     ["3"]),
            ("IO36",   ["4"]),
            ("IO39",   ["5"]),
            ("IO34",   ["6"]),
            ("IO35",   ["7"]),
            ("IO32",   ["8"]),
            ("IO33",   ["9"]),
            ("IO25",   ["10"]),
            ("IO26",   ["11"]),
            ("IO27",   ["12"]),
            ("IO14",   ["13"]),
            ("IO12",   ["14"]),
            ("GND",    ["1", "15", "38"]),
            ("IO13",   ["16"]),
            ("IO9",    ["17"]),
            ("IO10",   ["18"]),
            ("IO11",   ["19"]),
            ("IO6",    ["20"]),
            ("IO7",    ["21"]),
            ("IO8",    ["22"]),
            ("IO15",   ["23"]),
            ("IO2",    ["24"]),
            ("IO0",    ["25"]),
            ("IO4",    ["26"]),
            ("IO16",   ["27"]),
            ("IO17",   ["28"]),
            ("IO5",    ["29"]),
            ("IO18",   ["30"]),
            ("IO19",   ["31"]),
            ("IO21",   ["33"]),
            ("IO3",    ["34"]),
            ("IO1",    ["35"]),
            ("IO22",   ["36"]),
            ("IO23",   ["37"]),
        ],
        "vcc_pins": ["3V3"],
        "gnd_pins": ["GND"],
        "reset_pin": "EN",
        "gpio_pins": ["IO32", "IO33", "IO25", "IO26", "IO27", "IO14", "IO12", "IO13", "IO4", "IO2"],
        "uart_tx": "IO1",
        "uart_rx": "IO3",
        "spi_pins": {"MOSI": "IO23", "MISO": "IO19", "SCK": "IO18", "SS": "IO5"},
        "i2c_pins": {"SDA": "IO21", "SCL": "IO22"},
        "usb_dp": "IO19",
        "usb_dn": "IO18",
    },
    "rp2040": {
        "symbol_name": "RP2040",
        "pins": [
            ("IOVDD",   ["1", "10", "22", "33", "42", "49"]),
            ("DVDD",    ["23", "50"]),
            ("USB_DP",  ["47"]),
            ("USB_DM",  ["46"]),
            ("GND",     ["57"]),
            ("GPIO0",   ["2"]),
            ("GPIO1",   ["3"]),
            ("GPIO2",   ["4"]),
            ("GPIO3",   ["5"]),
            ("GPIO4",   ["6"]),
            ("GPIO5",   ["7"]),
            ("GPIO6",   ["8"]),
            ("GPIO7",   ["9"]),
            ("GPIO8",   ["11"]),
            ("GPIO9",   ["12"]),
            ("GPIO10",  ["13"]),
            ("GPIO11",  ["14"]),
            ("GPIO12",  ["15"]),
            ("GPIO13",  ["16"]),
            ("GPIO14",  ["17"]),
            ("GPIO15",  ["18"]),
            ("GPIO16",  ["27"]),
            ("GPIO17",  ["28"]),
            ("GPIO18",  ["29"]),
            ("GPIO19",  ["30"]),
            ("GPIO20",  ["31"]),
            ("GPIO21",  ["32"]),
            ("GPIO22",  ["34"]),
            ("GPIO23",  ["35"]),
            ("GPIO24",  ["36"]),
            ("GPIO25",  ["37"]),
            ("GPIO26",  ["38"]),
            ("GPIO27",  ["39"]),
            ("GPIO28",  ["40"]),
            ("GPIO29",  ["41"]),
            ("RUN",     ["26"]),
            ("SWDIO",   ["24"]),
            ("SWCLK",   ["25"]),
        ],
        "vcc_pins": ["IOVDD", "DVDD"],
        "gnd_pins": ["GND"],
        "reset_pin": "RUN",
        "gpio_pins": ["GPIO0", "GPIO1", "GPIO2", "GPIO3", "GPIO4", "GPIO5",
                       "GPIO6", "GPIO7", "GPIO8", "GPIO9", "GPIO10"],
        "uart_tx": "GPIO0",
        "uart_rx": "GPIO1",
        "spi_pins": {"MOSI": "GPIO3", "MISO": "GPIO4", "SCK": "GPIO2", "SS": "GPIO5"},
        "i2c_pins": {"SDA": "GPIO4", "SCL": "GPIO5"},
        "usb_dp": "USB_DP",
        "usb_dn": "USB_DM",
        "swdio": "SWDIO",
        "swclk": "SWCLK",
    },
    "stm32h743": {
        "symbol_name": "STM32H743VIT6",
        "pins": [
            ("VDD",    ["11", "19", "28", "50", "75", "100"]),
            ("VSS",    ["10", "27", "49", "74", "99"]),
            ("NRST",   ["14"]),
            ("PA0",    ["23"]),
            ("PA1",    ["24"]),
            ("PA2",    ["25"]),
            ("PA3",    ["26"]),
            ("PA9",    ["68"]),
            ("PA10",   ["69"]),
            ("PA11",   ["70"]),
            ("PA12",   ["71"]),
            ("PB0",    ["35"]),
            ("PB1",    ["36"]),
            ("PB6",    ["92"]),
            ("PB7",    ["93"]),
            ("PB10",   ["47"]),
            ("PB11",   ["48"]),
            ("PC0",    ["15"]),
            ("PC1",    ["16"]),
            ("PC13",   ["7"]),
            ("PD0",    ["81"]),
            ("PD1",    ["82"]),
        ],
        "vcc_pins": ["VDD"],
        "gnd_pins": ["VSS"],
        "reset_pin": "NRST",
        "gpio_pins": ["PA0", "PA1", "PA2", "PA3", "PB0", "PB1", "PC0", "PC1", "PC13"],
        "uart_tx": "PA9",
        "uart_rx": "PA10",
        "spi_pins": {"MOSI": "PB10", "MISO": "PB11", "SCK": "PD0", "SS": "PD1"},
        "i2c_pins": {"SDA": "PB7", "SCL": "PB6"},
        "usb_dp": "PA12",
        "usb_dn": "PA11",
        "swdio": "PA13",
        "swclk": "PA14",
    },
    "nrf52840": {
        "symbol_name": "nRF52840-QIAA",
        "pins": [
            ("VDD",     ["13"]),
            ("VSS",     ["31"]),
            ("P0.00",   ["2"]),
            ("P0.01",   ["3"]),
            ("P0.02",   ["4"]),
            ("P0.03",   ["5"]),
            ("P0.04",   ["6"]),
            ("P0.05",   ["7"]),
            ("P0.06",   ["8"]),
            ("P0.07",   ["9"]),
            ("P0.13",   ["33"]),
            ("P0.14",   ["34"]),
            ("P0.15",   ["35"]),
            ("P0.18",   ["38"]),
            ("P0.20",   ["40"]),
            ("P0.24",   ["44"]),
            ("SWDIO",   ["26"]),
            ("SWDCLK",  ["25"]),
            ("D+",      ["46"]),
            ("D-",      ["47"]),
            ("RESET",   ["18"]),
        ],
        "vcc_pins": ["VDD"],
        "gnd_pins": ["VSS"],
        "reset_pin": "RESET",
        "gpio_pins": ["P0.00", "P0.01", "P0.02", "P0.03", "P0.04", "P0.05",
                       "P0.06", "P0.07", "P0.13", "P0.14"],
        "uart_tx": "P0.06",
        "uart_rx": "P0.07",
        "spi_pins": {"MOSI": "P0.15", "MISO": "P0.14", "SCK": "P0.13", "SS": "P0.18"},
        "i2c_pins": {"SDA": "P0.04", "SCL": "P0.03"},
        "usb_dp": "D+",
        "usb_dn": "D-",
        "swdio": "SWDIO",
        "swclk": "SWDCLK",
    },
    "stm32f030": {
        "symbol_name": "STM32F030C8T6",
        "pins": [
            ("VDD",    ["1", "32", "48"]),
            ("VSS",    ["16", "33", "47"]),
            ("NRST",   ["7"]),
            ("PA0",    ["10"]),
            ("PA1",    ["11"]),
            ("PA2",    ["12"]),
            ("PA3",    ["13"]),
            ("PA5",    ["15"]),
            ("PA6",    ["16"]),
            ("PA7",    ["17"]),
            ("PA9",    ["30"]),
            ("PA10",   ["31"]),
            ("PA13",   ["34"]),
            ("PA14",   ["37"]),
            ("PB0",    ["18"]),
            ("PB1",    ["19"]),
            ("PB6",    ["42"]),
            ("PB7",    ["43"]),
        ],
        "vcc_pins": ["VDD"],
        "gnd_pins": ["VSS"],
        "reset_pin": "NRST",
        "gpio_pins": ["PA0", "PA1", "PA2", "PA3", "PA5", "PA6", "PA7", "PB0", "PB1"],
        "uart_tx": "PA9",
        "uart_rx": "PA10",
        "spi_pins": {"MOSI": "PA7", "MISO": "PA6", "SCK": "PA5", "SS": "PA4"},
        "i2c_pins": {"SDA": "PB7", "SCL": "PB6"},
        "swdio": "PA13",
        "swclk": "PA14",
    },
    "esp8266": {
        "symbol_name": "ESP-12F",
        "pins": [
            ("VCC",    ["8"]),
            ("GND",    ["15"]),
            ("EN",     ["3"]),
            ("RST",    ["1"]),
            ("GPIO0",  ["12"]),
            ("GPIO2",  ["14"]),
            ("GPIO4",  ["16"]),
            ("GPIO5",  ["24"]),
            ("GPIO12", ["10"]),
            ("GPIO13", ["12"]),
            ("GPIO14", ["9"]),
            ("GPIO15", ["16"]),
            ("GPIO16", ["4"]),
            ("TXD0",   ["22"]),
            ("RXD0",   ["21"]),
            ("ADC0",   ["2"]),
        ],
        "vcc_pins": ["VCC"],
        "gnd_pins": ["GND"],
        "reset_pin": "RST",
        "gpio_pins": ["GPIO0", "GPIO2", "GPIO4", "GPIO5", "GPIO12", "GPIO14", "GPIO16"],
        "uart_tx": "TXD0",
        "uart_rx": "RXD0",
        "spi_pins": {"MOSI": "GPIO13", "MISO": "GPIO12", "SCK": "GPIO14", "SS": "GPIO15"},
        "i2c_pins": {"SDA": "GPIO4", "SCL": "GPIO5"},
    },
    "imxrt1062": {
        "symbol_name": "MIMXRT1062DVJ6A",
        "pins": [
            ("VDD_SOC",     ["A1"]),
            ("VSS",         ["A2"]),
            ("GPIO_AD_B0_00", ["A3"]),
            ("GPIO_AD_B0_01", ["A4"]),
            ("GPIO_AD_B0_02", ["A5"]),
            ("GPIO_AD_B0_03", ["A6"]),
            ("USB_OTG1_DP",   ["B1"]),
            ("USB_OTG1_DN",   ["B2"]),
        ],
        "vcc_pins": ["VDD_SOC"],
        "gnd_pins": ["VSS"],
        "reset_pin": None,
        "gpio_pins": ["GPIO_AD_B0_00", "GPIO_AD_B0_01", "GPIO_AD_B0_02", "GPIO_AD_B0_03"],
        "uart_tx": "GPIO_AD_B0_02",
        "uart_rx": "GPIO_AD_B0_03",
        "spi_pins": {},
        "i2c_pins": {},
        "usb_dp": "USB_OTG1_DP",
        "usb_dn": "USB_OTG1_DN",
    },
}


def generate_board_zen(spec: BoardSpec, board_name: str | None = None) -> str:
    """Generate a complete board .zen file from a BoardSpec."""

    if board_name is None:
        board_name = _slugify(spec.description)

    mcu_def = MCU_DEFINITIONS.get(spec.mcu)
    if mcu_def is None:
        raise ValueError(f"No MCU definition for {spec.mcu}")

    lines: list[str] = []

    # ── Header ──────────────────────────────────────────────────────────
    lines.append(f'# {board_name}.zen — Auto-generated by Eisla pipeline')
    lines.append(f'# Source: "{spec.description}"')
    lines.append(f'# MCU: {spec.mcu} ({spec.mcu_info["family"]}) — Tier {spec.tier}')
    lines.append(f'# Date: {date.today().isoformat()}')
    lines.append('')

    # ── Imports ──────────────────────────────────────────────────────────
    lines.append('# ── Imports ─────────────────────────────────────────────────')
    lines.append('load("@stdlib/generics/Capacitor.zen", "Capacitor")')
    lines.append('load("@stdlib/generics/Resistor.zen", "Resistor")')
    lines.append('load("@stdlib/units.zen", "Voltage", "Impedance")')
    lines.append('')

    # Module imports
    if spec.power_source == "barrel" or spec.input_voltage == "12V":
        lines.append('BuckConverter = Module("../../modules/power/BuckConverter5V.zen")')
        lines.append('LDO = Module("../../modules/power/LDO3V3.zen")')
    else:
        lines.append('LDO = Module("../../modules/power/LDO3V3.zen")')

    if spec.has_usb:
        lines.append('USBTypeC = Module("../../modules/usb/USBTypeC.zen")')

    if spec.has_debug:
        lines.append('SWD = Module("../../modules/debug/SWD.zen")')

    if spec.has_power_led:
        lines.append('StatusLED = Module("../../modules/indicators/StatusLED.zen")')

    lines.append('')

    # ── Core nets ────────────────────────────────────────────────────────
    lines.append('# ── Core nets ───────────────────────────────────────────────')

    if spec.power_source == "barrel":
        lines.append('vin  = Net("VIN", voltage = Voltage("7V to 12V"))')
        lines.append('v5   = Net("V5", voltage = Voltage("5V"))')

    lines.append('v3v3 = Net("V3V3", voltage = Voltage("3.3V"))')
    lines.append('gnd  = Net("GND")')
    lines.append('')

    # ── Power section ────────────────────────────────────────────────────
    lines.append('# ── Power ───────────────────────────────────────────────────')

    if spec.power_source == "barrel":
        lines.append('BuckConverter(vin = vin, vout = v5, gnd = gnd)')
        lines.append('LDO(vin = v5, vout = v3v3, gnd = gnd)')
    elif spec.has_usb:
        lines.append('usb = USBTypeC(vbus = Net("VBUS", voltage = Voltage("5V")), gnd = gnd)')
        lines.append('LDO(vin = usb.vbus, vout = v3v3, gnd = gnd)')
    else:
        lines.append('LDO(vin = Net("VIN", voltage = Voltage("5V")), vout = v3v3, gnd = gnd)')

    lines.append('')

    # ── MCU ──────────────────────────────────────────────────────────────
    lines.append('# ── MCU ─────────────────────────────────────────────────────')

    # Build symbol definition
    lines.append(f'MCUSymbol = Symbol(')
    lines.append(f'    name = "{mcu_def["symbol_name"]}",')
    lines.append(f'    definition = [')
    for pin_name, pin_nums in mcu_def["pins"]:
        lines.append(f'        ("{pin_name}", {pin_nums}),')
    lines.append(f'    ],')
    lines.append(f')')
    lines.append('')

    # Build pin connections
    pin_assignments: dict[str, str] = {}
    for vcc_pin in mcu_def["vcc_pins"]:
        pin_assignments[vcc_pin] = "v3v3"
    for gnd_pin in mcu_def["gnd_pins"]:
        pin_assignments[gnd_pin] = "gnd"

    # Reset pin with pull-up
    if mcu_def.get("reset_pin"):
        reset = mcu_def["reset_pin"]
        pin_assignments[reset] = 'Net("nRESET")'

    # Assign peripherals to GPIO
    gpio_idx = 0
    gpio_pins = mcu_def["gpio_pins"]

    if "led" in spec.peripherals and gpio_idx < len(gpio_pins):
        pin_assignments[gpio_pins[gpio_idx]] = 'Net("LED_GPIO")'
        gpio_idx += 1

    if "uart" in spec.peripherals:
        pin_assignments[mcu_def["uart_tx"]] = 'Net("UART_TX")'
        pin_assignments[mcu_def["uart_rx"]] = 'Net("UART_RX")'

    if "spi" in spec.peripherals and mcu_def.get("spi_pins"):
        for func, pin in mcu_def["spi_pins"].items():
            pin_assignments[pin] = f'Net("SPI_{func}")'

    if "i2c" in spec.peripherals and mcu_def.get("i2c_pins"):
        for func, pin in mcu_def["i2c_pins"].items():
            pin_assignments[pin] = f'Net("I2C_{func}")'

    if spec.has_usb and mcu_def.get("usb_dp"):
        pin_assignments[mcu_def["usb_dp"]] = "usb.usb.DP"
        pin_assignments[mcu_def["usb_dn"]] = "usb.usb.DN"

    # Fill remaining pins as NotConnected
    all_pin_names = [p[0] for p in mcu_def["pins"]]
    for p in all_pin_names:
        if p not in pin_assignments:
            pin_assignments[p] = "Net()"

    lines.append('Component(')
    lines.append(f'    name   = "U_MCU",')
    lines.append(f'    symbol = MCUSymbol,')
    lines.append(f'    pins   = {{')
    for pin_name, _ in mcu_def["pins"]:
        val = pin_assignments.get(pin_name, "Net()")
        lines.append(f'        "{pin_name}": {val},')
    lines.append(f'    }},')
    lines.append(f'    mpn = "{mcu_def["symbol_name"]}",')
    lines.append(f')')
    lines.append('')

    # Decoupling caps on VCC pins
    lines.append('# Decoupling capacitors')
    for i, vcc_pin in enumerate(mcu_def["vcc_pins"]):
        lines.append(f'Capacitor(name = "C_MCU{i+1}", value = "100nF", P1 = v3v3, P2 = gnd)')
    lines.append('')

    # Reset pull-up
    if mcu_def.get("reset_pin"):
        lines.append('# Reset pull-up + filter cap')
        lines.append(f'Resistor(name = "R_RST", value = "10k", P1 = v3v3, P2 = Net("nRESET"))')
        lines.append(f'Capacitor(name = "C_RST", value = "100nF", P1 = Net("nRESET"), P2 = gnd)')
        lines.append('')

    # ── Debug header ─────────────────────────────────────────────────────
    if spec.has_debug:
        lines.append('# ── Debug ─────────────────────────────────────────────────────')
        swdio = mcu_def.get("swdio", "SWDIO")
        swclk = mcu_def.get("swclk", "SWCLK")
        lines.append(f'SWD(')
        lines.append(f'    vcc    = v3v3,')
        lines.append(f'    gnd    = gnd,')
        lines.append(f'    swdio  = Net("SWDIO"),')
        lines.append(f'    swclk  = Net("SWCLK"),')
        lines.append(f'    swo    = Net("SWO"),')
        lines.append(f'    nreset = Net("nRESET"),')
        lines.append(f')')
        lines.append('')

    # ── Status LED ───────────────────────────────────────────────────────
    if spec.has_power_led:
        lines.append('# ── Status LED ────────────────────────────────────────────────')
        if "led" in spec.peripherals:
            lines.append('StatusLED(gpio = Net("LED_GPIO"), vcc = v3v3, gnd = gnd)')
        else:
            # Power indicator on a spare GPIO
            spare = gpio_pins[gpio_idx] if gpio_idx < len(gpio_pins) else gpio_pins[-1]
            lines.append(f'StatusLED(gpio = Net("PWR_LED"), vcc = v3v3, gnd = gnd)')
        lines.append('')

    return "\n".join(lines)


def _slugify(text: str) -> str:
    """Convert description to a filesystem-safe board name."""
    import re
    slug = re.sub(r"[^a-zA-Z0-9]+", "_", text.strip())
    slug = slug.strip("_")[:40]
    return slug or "Board"

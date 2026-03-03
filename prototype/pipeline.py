#!/usr/bin/env python3
"""
pipeline.py — Eisla NL-to-Zener pipeline prototype.

End-to-end flow:
  1. Accept a plain-English project description
  2. Classify MCU tier and extract peripheral requirements
  3. Generate a composable Zener board file (.zen)
  4. (Future) invoke `pcb build` to compile to KiCad
  5. (Future) invoke FreeRouting for auto-layout
  6. (Future) run ERC/DRC checks
  7. (Future) export Gerbers and quote from fabs

Usage:
    python pipeline.py "I want an ESP32 board with WiFi and an LED"
    python pipeline.py --interactive
    python pipeline.py --examples
"""

import argparse
import json
import os
import sys
from pathlib import Path

from tier_classifier import classify, BoardSpec
from zen_generator import generate_board_zen


PRICING = {1: 499, 2: 599, 3: 749}

EXAMPLE_REQUESTS = [
    "I want a simple board with an ATmega328P that blinks an LED",
    "Build me a WiFi-enabled sensor hub that reads temperature and humidity over I2C",
    "I need a USB-C dev board with an RP2040, SPI flash, and SWD debug",
    "Design a motor controller board with ESP32, PWM outputs, and Bluetooth",
    "High-performance board with STM32H7, Ethernet, USB, and SPI for an IMU",
]


def run_pipeline(description: str, output_dir: str = "boards/generated") -> dict:
    """Run the full NL → Zener pipeline and return results."""

    # Step 1: Classify
    spec = classify(description)

    # Step 2: Generate Zener board file
    board_name = _make_board_name(spec)
    zen_code = generate_board_zen(spec, board_name)

    # Step 3: Write output
    out_path = Path(output_dir)
    out_path.mkdir(parents=True, exist_ok=True)

    zen_file = out_path / f"{board_name}.zen"
    zen_file.write_text(zen_code)

    # Write board pcb.toml
    board_toml = out_path / "pcb.toml"
    if not board_toml.exists():
        board_toml.write_text(
            f'[package]\nname = "generated-boards"\nversion = "0.1.0"\n'
            f'description = "Auto-generated Eisla boards"\n'
        )

    # Build result summary
    result = {
        "board_name": board_name,
        "zen_file": str(zen_file),
        "tier": spec.tier,
        "price": f"£{PRICING[spec.tier]}",
        "mcu": spec.mcu,
        "mcu_family": spec.mcu_info["family"],
        "peripherals": spec.peripherals,
        "power_source": spec.power_source,
        "has_usb": spec.has_usb,
        "has_debug": spec.has_debug,
        "next_steps": [
            f"pcb build {zen_file}          # compile to KiCad project",
            "freerouting <kicad_project>     # auto-route the PCB",
            "pcb check                      # run ERC/DRC validation",
            "pcb export gerber              # generate manufacturing files",
        ],
    }

    return result


def _make_board_name(spec: BoardSpec) -> str:
    """Generate a board name from the spec."""
    import re
    words = spec.description.lower().split()
    # Take key words, skip articles
    skip = {"i", "a", "an", "the", "with", "and", "for", "that", "to", "me", "my"}
    key_words = [w for w in words if w not in skip and w.isalpha()][:4]
    slug = "_".join(key_words) if key_words else "board"
    slug = re.sub(r"[^a-z0-9_]", "", slug)
    return f"EISLA_{slug.upper()}"


def print_result(result: dict) -> None:
    """Pretty-print pipeline results."""
    print("\n" + "=" * 60)
    print(f"  EISLA PIPELINE — Board Generated")
    print("=" * 60)
    print(f"  Board:        {result['board_name']}")
    print(f"  Zen file:     {result['zen_file']}")
    print(f"  Tier:         {result['tier']} ({result['price']}/project)")
    print(f"  MCU:          {result['mcu']} ({result['mcu_family']})")
    print(f"  Peripherals:  {', '.join(result['peripherals']) or 'none'}")
    print(f"  Power:        {result['power_source']}")
    print(f"  USB:          {'yes' if result['has_usb'] else 'no'}")
    print(f"  Debug (SWD):  {'yes' if result['has_debug'] else 'no'}")
    print()
    print("  Next steps (with pcb CLI installed):")
    for step in result["next_steps"]:
        print(f"    $ {step}")
    print("=" * 60 + "\n")


def interactive_mode() -> None:
    """Interactive REPL for testing the pipeline."""
    print("\nEisla NL-to-Zener Pipeline (prototype)")
    print("Type a project description, or 'quit' to exit.\n")
    while True:
        try:
            desc = input("eisla> ").strip()
        except (EOFError, KeyboardInterrupt):
            print()
            break
        if not desc or desc.lower() in ("quit", "exit", "q"):
            break
        result = run_pipeline(desc)
        print_result(result)


def run_examples() -> None:
    """Run all built-in example requests."""
    print("\nRunning all example requests...\n")
    for i, desc in enumerate(EXAMPLE_REQUESTS, 1):
        print(f"[{i}/{len(EXAMPLE_REQUESTS)}] \"{desc}\"")
        result = run_pipeline(desc)
        print_result(result)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Eisla NL-to-Zener PCB design pipeline",
    )
    parser.add_argument(
        "description",
        nargs="?",
        help="Natural-language project description",
    )
    parser.add_argument(
        "--interactive", "-i",
        action="store_true",
        help="Start interactive mode",
    )
    parser.add_argument(
        "--examples", "-e",
        action="store_true",
        help="Run all built-in examples",
    )
    parser.add_argument(
        "--output-dir", "-o",
        default="boards/generated",
        help="Output directory for generated .zen files",
    )

    args = parser.parse_args()

    if args.examples:
        run_examples()
    elif args.interactive:
        interactive_mode()
    elif args.description:
        result = run_pipeline(args.description, args.output_dir)
        print_result(result)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()

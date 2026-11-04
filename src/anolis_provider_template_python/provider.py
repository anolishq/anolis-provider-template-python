"""The provider: simulated heaters, no hardware.

Start here when writing a provider. Each configured device is a heater with a
first-order thermal model: its temperature moves towards ambient plus the rise
its power level gives, with a fixed time constant, and it counts the energy it
has drawn. Replace the model with calls into your device's driver library and
keep the rest of the shape:

- ``HEATER`` declares the device type: what the runtime can read and call.
- ``config_schema`` declares the config; ``check_config`` refuses what the
  schema cannot say.
- ``read`` and ``call`` serve requests; ``stop`` puts every output in its safe
  state however the provider exits.
"""

from __future__ import annotations

import math
import sys
import time
from collections.abc import Mapping, Sequence
from importlib.metadata import PackageNotFoundError, version
from typing import Any

from anolis_provider_sdk import Arg, Category, Device, DeviceType, Function, Provider, Signal, ValueType, run

try:
    __version__ = version("anolis-provider-template-python")
except PackageNotFoundError:  # a source tree that is not installed
    __version__ = "0.0.0"

TIME_CONSTANT_S = 60.0

HEATER = DeviceType(
    id="heater",
    signals=(
        Signal("temperature", ValueType.DOUBLE, unit="degC", description="Simulated temperature"),
        Signal("power", ValueType.DOUBLE, description="Power level, 0 (off) to 1 (full)"),
        Signal("energy", ValueType.DOUBLE, unit="J", description="Energy drawn since the last reset", default=False),
    ),
    functions=(
        # ACTUATE with a required numeric argument whose 0 is safe: the runtime's
        # zero_is_safe rung can then stop it by calling it with 0.
        Function(
            "set_power",
            args=(Arg("power", ValueType.DOUBLE, min=0.0, max=1.0, description="0 (off) to 1 (full)"),),
            description="Set the power level; 0 turns the heater off",
            category=Category.ACTUATE,
            is_idempotent=True,
        ),
        Function(
            "reset_energy",
            results=(Arg("energy", ValueType.DOUBLE, unit="J", description="The energy count before the reset"),),
            description="Set the energy count to zero",
            category=Category.CONFIG,
        ),
    ),
)

CONFIG_SCHEMA: dict[str, Any] = {
    "title": "anolis-provider-template-python config",
    "type": "object",
    "properties": {
        "devices": {
            "type": "array",
            "minItems": 1,
            "items": {
                "type": "object",
                "properties": {
                    "id": {"type": "string", "pattern": "^[a-z][a-z0-9_]*$", "description": "Device id"},
                    "label": {"type": "string"},
                    "ambient_c": {"type": "number", "default": 20.0, "description": "Ambient temperature, degC"},
                    "max_rise_c": {
                        "type": "number",
                        "exclusiveMinimum": 0,
                        "default": 50.0,
                        "description": "Temperature rise above ambient at full power, degC",
                    },
                    "rated_w": {
                        "type": "number",
                        "exclusiveMinimum": 0,
                        "default": 100.0,
                        "description": "Power drawn at full power, W",
                    },
                },
                "required": ["id"],
                "additionalProperties": False,
            },
        },
    },
    "required": ["devices"],
    "additionalProperties": False,
}


class Heater:
    """The simulated device. Its state advances whenever it is read or set."""

    def __init__(self, ambient_c: float, max_rise_c: float, rated_w: float) -> None:
        self.ambient_c = ambient_c
        self.max_rise_c = max_rise_c
        self.rated_w = rated_w
        self.temperature = ambient_c
        self.power = 0.0
        self.energy = 0.0
        self._at = time.monotonic()

    def advance(self) -> None:
        now = time.monotonic()
        dt = now - self._at
        self._at = now
        target = self.ambient_c + self.power * self.max_rise_c
        self.temperature = target + (self.temperature - target) * math.exp(-dt / TIME_CONSTANT_S)
        self.energy += self.power * self.rated_w * dt


class TemplateProvider(Provider):
    name = "anolis-provider-template-python"
    version = __version__
    conformance_level = 2
    config_schema = CONFIG_SCHEMA

    @classmethod
    def check_config(cls, config: Mapping[str, Any]) -> None:
        """What the schema cannot say: each device id once."""
        seen: set[str] = set()
        for entry in config["devices"]:
            if entry["id"] in seen:
                raise ValueError(f"device id {entry['id']!r} is configured twice")
            seen.add(entry["id"])

    def __init__(self, config: Mapping[str, Any]) -> None:
        super().__init__(config)
        entries = config["devices"]
        self._devices = [Device(e["id"], HEATER, label=e.get("label", e["id"])) for e in entries]
        self._heaters = {
            e["id"]: Heater(e.get("ambient_c", 20.0), e.get("max_rise_c", 50.0), e.get("rated_w", 100.0))
            for e in entries
        }

    def stop(self) -> None:
        """The provider is exiting, however the session ended: turn every heater off."""
        for heater in self._heaters.values():
            heater.advance()
            heater.power = 0.0

    def devices(self) -> Sequence[Device]:
        return self._devices

    def read(self, device: Device, signal_ids: list[str]) -> Mapping[str, Any]:
        heater = self._heaters[device.id]
        heater.advance()
        values = {"temperature": heater.temperature, "power": heater.power, "energy": heater.energy}
        return {sid: values[sid] for sid in signal_ids}

    def call(self, device: Device, function: Function, args: Mapping[str, Any]) -> Mapping[str, Any] | None:
        heater = self._heaters[device.id]
        heater.advance()
        if function.name == "set_power":
            heater.power = args["power"]  # the SDK has already checked it is within 0..1
            return None
        if function.name == "reset_energy":
            energy, heater.energy = heater.energy, 0.0
            return {"energy": energy}
        raise AssertionError(f"undeclared function {function.name}")  # the SDK only passes declared ones


def main() -> None:
    sys.exit(run(TemplateProvider))

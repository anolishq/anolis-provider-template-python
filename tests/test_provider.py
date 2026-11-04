"""The heater model and the provider's own rules. The protocol itself is covered
by the conformance harness (test_conformance.py)."""

from __future__ import annotations

from typing import Any

import pytest

from anolis_provider_template_python import provider as mod
from anolis_provider_template_python.provider import HEATER, Heater, TemplateProvider


class Clock:
    def __init__(self) -> None:
        self.now = 1000.0

    def __call__(self) -> float:
        return self.now


@pytest.fixture
def clock(monkeypatch: pytest.MonkeyPatch) -> Clock:
    c = Clock()
    monkeypatch.setattr("anolis_provider_template_python.provider.time.monotonic", c)
    return c


def started(**options: Any) -> TemplateProvider:
    p = TemplateProvider({"devices": [{"id": "h0", **options}]})
    p.start(1.0)
    return p


def call(p: TemplateProvider, name: str, **args: Any) -> Any:
    function = HEATER.function_by_name(name)
    assert function is not None
    return p.call(p.devices()[0], function, args)


def read(p: TemplateProvider, *signals: str) -> dict[str, Any]:
    return dict(p.read(p.devices()[0], list(signals)))


def test_a_heater_starts_off_at_ambient(clock: Clock) -> None:
    p = started(ambient_c=21.0)
    assert read(p, "temperature", "power", "energy") == {"temperature": 21.0, "power": 0.0, "energy": 0.0}


def test_full_power_approaches_ambient_plus_the_rise(clock: Clock) -> None:
    p = started(ambient_c=20.0, max_rise_c=50.0)
    call(p, "set_power", power=1.0)
    clock.now += mod.TIME_CONSTANT_S
    after_one_tau = read(p, "temperature")["temperature"]
    assert after_one_tau == pytest.approx(20.0 + 50.0 * (1 - 1 / 2.718281828), abs=0.01)
    clock.now += 20 * mod.TIME_CONSTANT_S
    assert read(p, "temperature")["temperature"] == pytest.approx(70.0, abs=0.01)


def test_energy_counts_power_times_rating_and_resets(clock: Clock) -> None:
    p = started(rated_w=100.0)
    call(p, "set_power", power=0.5)
    clock.now += 10.0
    assert read(p, "energy") == {"energy": pytest.approx(500.0)}
    assert call(p, "reset_energy") == {"energy": pytest.approx(500.0)}
    assert read(p, "energy") == {"energy": 0.0}


def test_stop_turns_every_heater_off(clock: Clock) -> None:
    p = TemplateProvider({"devices": [{"id": "h0"}, {"id": "h1"}]})
    p.start(1.0)
    set_power = HEATER.function_by_name("set_power")
    assert set_power is not None
    for d in p.devices():
        p.call(d, set_power, {"power": 1.0})
    p.stop()
    assert [p.read(d, ["power"])["power"] for d in p.devices()] == [0.0, 0.0]


def test_a_device_id_configured_twice_is_refused() -> None:
    with pytest.raises(ValueError, match="configured twice"):
        TemplateProvider.check_config({"devices": [{"id": "h0"}, {"id": "h0"}]})


def test_the_model_tracks_temperature_between_reads(clock: Clock) -> None:
    heater = Heater(ambient_c=10.0, max_rise_c=40.0, rated_w=1.0)
    heater.power = 1.0
    clock.now += 1e6
    heater.advance()
    assert heater.temperature == pytest.approx(50.0)

"""Test dynamic discovery of platforms based on controller categories."""

import ast
import asyncio
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import AsyncMock, Mock

source = (
    Path(__file__)
    .resolve()
    .parents[1]
    .joinpath("custom_components/control4/__init__.py")
    .read_text(encoding="utf-8")
)
tree = ast.parse(source)
func = next(
    n
    for n in tree.body
    if isinstance(n, ast.AsyncFunctionDef) and n.name == "_async_get_active_platforms"
)
func.returns = None
for arg in func.args.args:
    arg.annotation = None
code = compile(
    ast.fix_missing_locations(ast.Module(body=[func], type_ignores=[])),
    "patched_discovery",
    "exec",
)

class Platform:
    LIGHT = "light"
    ALARM_CONTROL_PANEL = "alarm_control_panel"
    BINARY_SENSOR = "binary_sensor"
    LOCK = "lock"
    MEDIA_PLAYER = "media_player"
    SENSOR = "sensor"
    SWITCH = "switch"
    FAN = "fan"
    CLIMATE = "climate"
    COVER = "cover"

PLATFORMS = [
    Platform.LIGHT,
    Platform.ALARM_CONTROL_PANEL,
    Platform.BINARY_SENSOR,
    Platform.LOCK,
    Platform.MEDIA_PLAYER,
    Platform.SENSOR,
    Platform.SWITCH,
    Platform.FAN,
    Platform.CLIMATE,
    Platform.COVER,
]

CATEGORY_TO_PLATFORMS = {
    "lights": [Platform.LIGHT, Platform.FAN],
    "security": [Platform.ALARM_CONTROL_PANEL],
    "sensors": [Platform.BINARY_SENSOR],
    "locks": [Platform.LOCK],
    "comfort": [Platform.CLIMATE],
    "audio_video": [Platform.MEDIA_PLAYER],
    "motorization": [Platform.COVER],
    "blinds": [Platform.COVER],
}

env = {
    "PLATFORMS": PLATFORMS,
    "CATEGORY_TO_PLATFORMS": CATEGORY_TO_PLATFORMS,
    "Platform": Platform,
    "_LOGGER": Mock(),
}
exec(code, env)
_async_get_active_platforms = env["_async_get_active_platforms"]

async def test_lighting_and_av():
    director = SimpleNamespace(
        send_get_request=AsyncMock(
            return_value=[
                "controllers",
                "lights",
                "cameras",
                "audio_video",
                "user_interface",
            ]
        )
    )
    platforms = await _async_get_active_platforms(director)
    assert Platform.LIGHT in platforms
    assert Platform.FAN in platforms
    assert Platform.MEDIA_PLAYER in platforms
    assert Platform.SENSOR in platforms
    assert Platform.SWITCH in platforms
    assert Platform.LOCK not in platforms
    assert Platform.ALARM_CONTROL_PANEL not in platforms
    assert Platform.CLIMATE not in platforms
    print("PASS: test_lighting_and_av correctly enables only active platforms")

async def test_full_system():
    director = SimpleNamespace(
        sendGetRequest=AsyncMock(
            return_value='["lights", "security", "sensors", "locks", "comfort", "audio_video", "motorization"]'
        )
    )
    platforms = await _async_get_active_platforms(director)
    assert set(platforms) == set(PLATFORMS)
    print("PASS: test_full_system enables all supported platforms")

async def test_fallback_on_error():
    director = SimpleNamespace(
        send_get_request=AsyncMock(side_effect=Exception("API error"))
    )
    platforms = await _async_get_active_platforms(director)
    assert platforms == list(PLATFORMS)
    print("PASS: test_fallback_on_error safely defaults to all platforms")

async def main():
    await test_lighting_and_av()
    await test_full_system()
    await test_fallback_on_error()

if __name__ == "__main__":
    asyncio.run(main())

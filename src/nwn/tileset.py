"""A parser for .set files (tilesets configuration)."""

import configparser
from dataclasses import dataclass, field
import re
from typing import BinaryIO


@dataclass
class Terrain:
    name: str = ""
    strref: int = 0


@dataclass
class Crosser:
    name: str = ""
    strref: int = 0


@dataclass
class Rule:
    placed: str
    placedheight: int
    adjacent: str
    adjacentheight: int
    changed: str
    changedheight: int


@dataclass
class Door:
    type: int
    x: float = 0
    y: float = 0
    z: float = 0
    orientation: float = 0


@dataclass
class Tile:
    doors: list[Door]

    model: str
    walkmesh: str = ""
    topleft: str = ""
    topleftheight: int = 0
    topright: str = ""
    toprightheight: int = 0
    bottomleft: str = ""
    bottomleftheight: int = 0
    bottomright: str = ""
    bottomrightheight: int = 0
    top: str = ""
    right: str = ""
    bottom: str = ""
    left: str = ""
    mainlight1: int = 0
    mainlight2: int = 0
    sourcelight1: int = 0
    sourcelight2: int = 0
    animloop1: int = 0
    animloop2: int = 0
    animloop3: int = 0
    sounds: int = 0
    pathnode: str = ""
    orientation: float = 0
    imagemap2d: str = ""


@dataclass
class Group:
    name: str
    rows: int
    columns: int
    tiles: list[int] = field(default_factory=list)


@dataclass
class SetGrass:
    grass: int
    density: float
    height: float
    ambientred: float
    ambientgreen: float
    ambientblue: float
    diffusered: float
    diffusegreen: float
    diffuseblue: float


@dataclass
class Set:
    name: str
    type: str
    version: str
    interior: int
    hasheighttransition: int
    envmap: str
    transition: float
    displayname: int
    border: str
    default: str
    floor: str

    grass: SetGrass = None
    terrains: list[Terrain] = field(default_factory=list)
    crossers: list[Crosser] = field(default_factory=list)
    primary_rules: list[Rule] = field(default_factory=list)
    tiles: list[Tile] = field(default_factory=list)
    groups: list[Group] = field(default_factory=list)


def _dataclass_name(s):
    return "".join(x or "_" for x in s.split("_"))


def _read_value(ty, v):
    if ty == int:
        return int(v)
    if ty == bool:
        return v in {"1"}
    if ty == float:
        return float(v)
    if ty == str:
        return str(v)
    if (hasattr(ty, "__origin__") and ty.__origin__ == list) or ty == list:
        # We manually load these in
        return []
    raise ValueError(f"Unsupported type: {ty}")


def _read_dataclass(cls, **kwargs):
    return cls(
        **{
            field.name: _read_value(field.type, kwargs[_dataclass_name(field.name)])
            for field in cls.__dataclass_fields__.values()
            if _dataclass_name(field.name) in kwargs and not field.name.startswith("_")
        }
    )


def read_set(file: BinaryIO) -> Set:
    """
    Reads a .set file and parses its contents into a Set object.
    """

    general = None

    data = configparser.ConfigParser()
    data.read_file(file)

    for s in data.sections():
        if s == "GENERAL":
            general = _read_dataclass(Set, **data[s])

        if not general:
            raise ValueError("No GENERAL section found")

        if s == "GRASS":
            grass = _read_dataclass(SetGrass, **data[s])
            general.grass = grass

        if ma := re.match(r"^TERRAIN(\d+)$", s):
            tid = int(ma.group(1))
            terrain = _read_dataclass(Terrain, **data[s])
            general.terrains.append(terrain)

        if ma := re.match(r"^CROSSER(\d+)$", s):
            terrain = _read_dataclass(Crosser, **data[s])
            general.crossers.append(terrain)

        if ma := re.match(r"^PRIMARY RULE(\d+)$", s):
            rule = _read_dataclass(Rule, **data[s])
            general.primary_rules.append(rule)

        if ma := re.match(r"^TILE(\d+)$", s):
            tid = int(ma.group(1))
            tile = _read_dataclass(Tile, **data[s])
            general.tiles.append(tile)

        if ma := re.match(r"^TILE(\d+)DOOR(\d+)$", s):
            tid = int(ma.group(1))
            door = _read_dataclass(Door, **data[s])
            tile = general.tiles[tid]
            tile.doors.append(door)

        if ma := re.match(r"^GROUP(\d+)$", s):
            group = _read_dataclass(Group, **data[s])
            count = group.rows * group.columns
            for i in range(count):
                tile = data[s][f"Tile{i}"]
                group.tiles.append(int(tile))
            general.groups.append(group)

    return general

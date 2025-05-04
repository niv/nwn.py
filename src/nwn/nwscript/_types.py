from typing import NamedTuple
from dataclasses import dataclass, field
from enum import Enum


class _ObjectSelf:
    """Use Object.SELF."""

    def __repr__(self):
        return "Object.SELF"


@dataclass(frozen=True)
class Object:
    """
    A Object is a immutable reference to a game object in the world.
    This maps directly to the nwscript ``object`` type.
    """

    INVALID = None
    """Special value: Invalid is 0x7F000000 in nwscript."""

    SELF = _ObjectSelf()
    """
    Special value: SELF is a placeholder for the calling object in a script.

    This has no meaning outside of a script context and is not a real reference.
    """

    id: int = 0x7F000000

    def __post_init__(self):
        if self.id < 0 or self.id > 0x7FFFFFFF:
            raise ValueError(f"Invalid object id: {self.id}")

    def __bool__(self):
        """
        Objects are truthy if they're not INVALID, even if the reference
        itself is dangling in game logic.
        """
        return self.id != 0x7F000000

    def __eq__(self, other):
        if other is None:
            return self is Object.INVALID
        if isinstance(other, Object):
            return self.id == other.id
        raise TypeError(f"Cannot compare Object to {type(other)}")

    def __repr__(self):
        if self is Object.INVALID:
            return "Object.INVALID"
        return f"Object(0x{self.id:X})"


Object.INVALID = Object(0x7F000000)


class Vector(NamedTuple):
    """
    A 3d vector that maps directly to the nwscript ``vector`` type.

    Vectors are always immutable, just like in the game engine.
    """

    x: float = 0.0
    y: float = 0.0
    z: float = 0.0


@dataclass
class Location:
    """
    Maps directly to the nwscript ``location`` type.
    """

    INVALID = None

    position: Vector = field(default_factory=Vector)
    orientation: float = 0.0
    area: Object = field(default_factory=Object.INVALID)


@dataclass
class Effect:
    """
    Maps directly to the NWScript effect type.

    Not fully implemented: This is just a stub for now.
    """

    INVALID = None

    type: int = 0


Effect.INVALID = Effect(type=0)


@dataclass(frozen=True)
class EngineStructure:
    """
    Placeholder type for engst until specific types are implemented.
    """

    vm_type: "VMType"


@dataclass(frozen=True)
class _VMClosure:
    """
    A closure as stored by the VM.
    """

    ip: int
    sp: int
    bp: int


class VMType(Enum):
    """
    All types supported by the NWScript VM as implemented in EE 37.
    """

    VOID = "void"
    INT = "int"
    FLOAT = "float"
    STRING = "string"
    OBJECT = "object"
    VECTOR = "vector"
    LOCATION = "location"
    EFFECT = "effect"
    ITEMPROPERTY = "itemproperty"
    EVENT = "event"
    TALENT = "talent"
    SQLQUERY = "sqlquery"
    CASSOWARY = "cassowary"
    JSON = "json"
    ACTION = "action"

    def python_type(self):
        """
        Returns the python type that the VM uses for this VMType on the VM stack.

        Returns:
            type: The python class/type.
        """

        match self:
            case VMType.INT:
                return int
            case VMType.FLOAT:
                return float
            case VMType.STRING:
                return str
            case VMType.OBJECT:
                return Object
            case VMType.VECTOR:
                return Vector
            case VMType.LOCATION:
                return Location
            case VMType.EFFECT:
                return Effect
            case VMType.ACTION:
                return _VMClosure
            case (
                VMType.ITEMPROPERTY,
                VMType.EVENT,
                VMType.TALENT,
                VMType.SQLQUERY,
                VMType.CASSOWARY,
                VMType.JSON,
            ):
                return EngineStructure(self)
            case _:
                raise NotImplementedError(f"Unknown VMType: {self}")

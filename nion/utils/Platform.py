import enum
import sys


class PlatformEnum(enum.Enum):
    MACOS = "darwin"
    WINDOWS = "win32"
    LINUX = "linux"


def get_platform() -> PlatformEnum:
    if sys.platform == "darwin":
        return PlatformEnum.MACOS
    elif sys.platform == 'win32':
        return PlatformEnum.WINDOWS
    elif sys.platform == 'linux':
        return PlatformEnum.LINUX
    else:
        raise ValueError("Unknown platform")


def is_macos() -> bool:
    return get_platform() == PlatformEnum.MACOS


def is_windows() -> bool:
    return get_platform() == PlatformEnum.WINDOWS


def is_linux() -> bool:
    return get_platform() == PlatformEnum.LINUX

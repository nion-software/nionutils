from __future__ import annotations

import re
import typing


class Color:
    """A color string with conversion methods."""

    def __init__(self, color_str: typing.Optional[typing.Union[Color, str]] = None) -> None:
        self.color_str: typing.Optional[str]
        if isinstance(color_str, str):
            self.color_str = color_str.strip().replace(" ", "")
        elif isinstance(color_str, Color):
            self.color_str = color_str.color_str
        else:
            self.color_str = None

    def __repr__(self) -> str:
        return self.color_str or "NONE"

    @property
    def is_valid(self) -> bool:
        return self.__hex_color(self.color_str) != None

    def matches_without_alpha(self, color: Color) -> bool:
        return self.__hex7_color() == color.__hex7_color()

    def to_hex_color(self) -> Color:
        return Color(self.__hex_color(self.color_str))

    def to_color_without_alpha(self) -> Color:
        color_str = self.color_str
        if not color_str:
            return Color()
        color_str = color_str.strip().replace(" ", "")
        c = re.split("rgba\((\d+),(\d+),(\d+),([\d.]+)\)", color_str)
        if len(c) > 1:
            return Color(f"#{int(c[1]):02x}{int(c[2]):02x}{int(c[3]):02x}")
        c = re.split("rgb\((\d+),(\d+),(\d+)\)", color_str)
        if len(c) > 1:
            return Color(f"#{int(c[1]):02x}{int(c[2]):02x}{int(c[3]):02x}")
        if color_str.startswith("#"):
            if len(color_str) == 9:
                return Color(f"#{color_str.lower()[3:]}")
            if len(color_str) == 7:
                return Color(color_str.lower())
            if len(color_str) == 5:
                return Color(f"#{color_str.lower()[2:]}")
        return Color(color_str)

    @property
    def hex_color_str(self) -> typing.Optional[str]:
        return self.to_hex_color().color_str

    def to_named_color_without_alpha(self) -> Color:
        hex_color_without_alpha = self.to_color_without_alpha().hex_color_str
        return Color(svg_color_reverse_map.get(hex_color_without_alpha, hex_color_without_alpha) if hex_color_without_alpha else None)

    def to_color_with_alpha(self, alpha: float) -> Color:
        hex7_color = self.__hex7_color()
        return Color(f"#{min(255, max(0, int(round(256 * alpha)))):02x}" + hex7_color[1:])

    def to_rgba_255(self) -> typing.Tuple[int, int, int, int]:
        hex_color = self.hex_color_str
        if hex_color and len(hex_color) == 4:
            rgb = tuple(int(hex_color[i:i + 1], 16) * 17 for i in (1, 2, 3))
            return rgb[0], rgb[1], rgb[2], 255
        elif hex_color and len(hex_color) == 5:
            rgba = tuple(int(hex_color[i:i + 1], 16) * 17 for i in (1, 2, 3, 4))
            return rgba[0], rgba[1], rgba[2], rgba[3]
        elif hex_color and len(hex_color) == 7:
            rgb = tuple(int(hex_color[i:i + 2], 16) for i in (1, 3, 5))
            return rgb[0], rgb[1], rgb[2], 255
        elif hex_color and len(hex_color) == 9:
            rgba = tuple(int(hex_color[i:i + 2], 16) for i in (1, 3, 5, 7))
            return rgba[0], rgba[1], rgba[2], rgba[3]
        else:
            return 255, 255, 255, 255

    def to_rgb_255(self) -> typing.Tuple[int, int, int]:
        return self.to_rgba_255()[:-1]

    def __hex_color(self, color_str: typing.Optional[str]) -> typing.Optional[str]:
        if not color_str:
            return None
        c = re.split("rgba\((\d+),(\d+),(\d+),([\d.]+)\)", color_str)
        if len(c) > 1:
            return f"#{int(255 * float(c[4])):02x}{int(c[1]):02x}{int(c[2]):02x}{int(c[3]):02x}"
        c = re.split("rgb\((\d+),(\d+),(\d+)\)", color_str)
        if len(c) > 1:
            return f"#{int(c[1]):02x}{int(c[2]):02x}{int(c[3]):02x}"
        if color_str.startswith("#"):
            if len(color_str) in (9, 7, 5, 4):
                return color_str.lower()
        return svg_color_map.get(color_str, color_str)

    def __hex7_color(self) -> str:
        if not self.color_str:
            return "#000000"
        hex_color_str = self.to_color_without_alpha().hex_color_str or "#000000"
        if len(hex_color_str) == 4:
            return f"#{hex(int(hex_color_str[1], 16) * 16)[2:]}{hex(int(hex_color_str[2], 16) * 16)[2:]}{hex(int(hex_color_str[3], 16) * 16)[2:]}"
        assert len(hex_color_str) == 7
        return hex_color_str


# https://www.w3.org/TR/SVG11/types.html#ColorKeywords

# processed with:

"""
import re

with open("colors.txt", "r") as f:
    while True:
        color_line = f.readline()
        if not color_line:
            break
        color_line = color_line.strip()
        rgb_line = f.readline().strip().replace(" ", "")
        c = re.split("rgb\((\d+),(\d+),(\d+)\)", rgb_line)
        print(f"\t\"{color_line}\": \"#{int(c[1]):02x}{int(c[2]):02x}{int(c[3]):02x}\",")
"""

svg_color_map = {
    "aliceblue": "#f0f8ff",
    "antiquewhite": "#faebd7",
    "aqua": "#00ffff",
    "aquamarine": "#7fffd4",
    "azure": "#f0ffff",
    "beige": "#f5f5dc",
    "bisque": "#ffe4c4",
    "black": "#000000",
    "blanchedalmond": "#ffebcd",
    "blue": "#0000ff",
    "blueviolet": "#8a2be2",
    "brown": "#a52a2a",
    "burlywood": "#deb887",
    "cadetblue": "#5f9ea0",
    "chartreuse": "#7fff00",
    "chocolate": "#d2691e",
    "coral": "#ff7f50",
    "cornflowerblue": "#6495ed",
    "cornsilk": "#fff8dc",
    "crimson": "#dc143c",
    "cyan": "#00ffff",
    "darkblue": "#00008b",
    "darkcyan": "#008b8b",
    "darkgoldenrod": "#b8860b",
    "darkgray": "#a9a9a9",
    "darkgreen": "#006400",
    "darkgrey": "#a9a9a9",
    "darkkhaki": "#bdb76b",
    "darkmagenta": "#8b008b",
    "darkolivegreen": "#556b2f",
    "darkorange": "#ff8c00",
    "darkorchid": "#9932cc",
    "darkred": "#8b0000",
    "darksalmon": "#e9967a",
    "darkseagreen": "#8fbc8f",
    "darkslateblue": "#483d8b",
    "darkslategray": "#2f4f4f",
    "darkslategrey": "#2f4f4f",
    "darkturquoise": "#00ced1",
    "darkviolet": "#9400d3",
    "deeppink": "#ff1493",
    "deepskyblue": "#00bfff",
    "dimgray": "#696969",
    "dimgrey": "#696969",
    "dodgerblue": "#1e90ff",
    "firebrick": "#b22222",
    "floralwhite": "#fffaf0",
    "forestgreen": "#228b22",
    "fuchsia": "#ff00ff",
    "gainsboro": "#dcdcdc",
    "ghostwhite": "#f8f8ff",
    "gold": "#ffd700",
    "goldenrod": "#daa520",
    "gray": "#808080",
    "grey": "#808080",
    "green": "#008000",
    "greenyellow": "#adff2f",
    "honeydew": "#f0fff0",
    "hotpink": "#ff69b4",
    "indianred": "#cd5c5c",
    "indigo": "#4b0082",
    "ivory": "#fffff0",
    "khaki": "#f0e68c",
    "lavender": "#e6e6fa",
    "lavenderblush": "#fff0f5",
    "lawngreen": "#7cfc00",
    "lemonchiffon": "#fffacd",
    "lightblue": "#add8e6",
    "lightcoral": "#f08080",
    "lightcyan": "#e0ffff",
    "lightgoldenrodyellow": "#fafad2",
    "lightgray": "#d3d3d3",
    "lightgreen": "#90ee90",
    "lightgrey": "#d3d3d3",
    "lightpink": "#ffb6c1",
    "lightsalmon": "#ffa07a",
    "lightseagreen": "#20b2aa",
    "lightskyblue": "#87cefa",
    "lightslategray": "#778899",
    "lightslategrey": "#778899",
    "lightsteelblue": "#b0c4de",
    "lightyellow": "#ffffe0",
    "lime": "#00ff00",
    "limegreen": "#32cd32",
    "linen": "#faf0e6",
    "magenta": "#ff00ff",
    "maroon": "#800000",
    "mediumaquamarine": "#66cdaa",
    "mediumblue": "#0000cd",
    "mediumorchid": "#ba55d3",
    "mediumpurple": "#9370db",
    "mediumseagreen": "#3cb371",
    "mediumslateblue": "#7b68ee",
    "mediumspringgreen": "#00fa9a",
    "mediumturquoise": "#48d1cc",
    "mediumvioletred": "#c71585",
    "midnightblue": "#191970",
    "mintcream": "#f5fffa",
    "mistyrose": "#ffe4e1",
    "moccasin": "#ffe4b5",
    "navajowhite": "#ffdead",
    "navy": "#000080",
    "oldlace": "#fdf5e6",
    "olive": "#808000",
    "olivedrab": "#6b8e23",
    "orange": "#ffa500",
    "orangered": "#ff4500",
    "orchid": "#da70d6",
    "palegoldenrod": "#eee8aa",
    "palegreen": "#98fb98",
    "paleturquoise": "#afeeee",
    "palevioletred": "#db7093",
    "papayawhip": "#ffefd5",
    "peachpuff": "#ffdab9",
    "peru": "#cd853f",
    "pink": "#ffc0cb",
    "plum": "#dda0dd",
    "powderblue": "#b0e0e6",
    "purple": "#800080",
    "red": "#ff0000",
    "rosybrown": "#bc8f8f",
    "royalblue": "#4169e1",
    "saddlebrown": "#8b4513",
    "salmon": "#fa8072",
    "sandybrown": "#f4a460",
    "seagreen": "#2e8b57",
    "seashell": "#fff5ee",
    "sienna": "#a0522d",
    "silver": "#c0c0c0",
    "skyblue": "#87ceeb",
    "slateblue": "#6a5acd",
    "slategray": "#708090",
    "slategrey": "#708090",
    "snow": "#fffafa",
    "springgreen": "#00ff7f",
    "steelblue": "#4682b4",
    "tan": "#d2b48c",
    "teal": "#008080",
    "thistle": "#d8bfd8",
    "tomato": "#ff6347",
    "turquoise": "#40e0d0",
    "violet": "#ee82ee",
    "wheat": "#f5deb3",
    "white": "#ffffff",
    "whitesmoke": "#f5f5f5",
    "yellow": "#ffff00",
    "yellowgreen": "#9acd32",
}


svg_color_reverse_map = {v: k for k, v in svg_color_map.items()}

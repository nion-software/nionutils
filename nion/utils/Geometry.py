"""
    Geometry related functions and classes.

    Includes functions for making pretty axis labels.

    Includes IntPoint, IntSize, and IntRect classes.
"""

from __future__ import annotations

# standard libraries
import collections
import math
import typing

# third party libraries
# None


def make_pretty(val, rounding):
    """ Make a pretty number, using algorithm from Paul Heckbert, extended to handle negative numbers. """
    val = float(val)
    if not val > 0.0 and not val < 0.0:
        return 0.0, 0  # make sense of values that are neither greater or less than 0.0
    if math.isfinite(val):
        factor10 = math.pow(10.0, math.floor(math.log10(abs(val))))
    else:
        return 0.0, 0
    val_norm = abs(val) / factor10  # between 1 and 10
    if val_norm < 1.0:
        val_norm = val_norm * 10
        factor10 = factor10 // 10
    if rounding:
        if val_norm < 1.5:
            val_norm = 1.0
        elif val_norm < 3.0:
            val_norm = 2.0
        elif val_norm < 7.0:
            val_norm = 5.0
        else:
            val_norm = 10.0
    else:
        if val_norm <= 1.0:
            val_norm = 1.0
        elif val_norm <= 2.0:
            val_norm = 2.0
        elif val_norm <= 5.0:
            val_norm = 5.0
        else:
            val_norm = 10.0
    return math.copysign(val_norm * factor10, val), factor10


def make_pretty2(val, rounding):
    """ Make a pretty number, using algorithm from Paul Heckbert, extended to handle negative numbers. """
    return make_pretty(val, rounding)[0]


def make_pretty_range2(value_low, value_high, ticks=5, logarithmic=False) -> typing.Tuple[float, float, typing.Sequence[float], float, int, float]:
    """
        Returns minimum, maximum, list of tick values, division, and precision.

        Value high and value low specify the data range.

        Tight indicates whether the pretty range should extend to the data (tight)
            or beyond the data (loose).

        Ticks is the approximate number of ticks desired, including the ends (if loose).

        Useful links:
            http://tog.acm.org/resources/GraphicsGems/gems/Label.c
            https://svn.r-project.org/R/trunk/src/appl/pretty.c
            http://www.mathworks.com/help/matlab/ref/axes_props.html
    """

    # adjust value_low, value_high to be floats in increasing order
    value_low = float(value_low)
    value_high = float(value_high)
    value_low, value_high = min(value_low, value_high), max(value_low, value_high)

    # check for small range
    if value_high == value_low:
        return value_low, value_low, [value_low], 0, 0, 0

    # make the value range a pretty range
    value_range = make_pretty2(value_high - value_low, False)

    # make the tick range a pretty range
    division, factor10 = make_pretty(value_range/(ticks-1), True)

    # calculate the graph minimum and maximum
    if division == 0:
        return 0, 0, [0], 0, 0, 0

    graph_minimum = math.floor(value_low / division) * division
    graph_maximum = math.ceil(value_high / division) * division

    # In logarithmic scale we calculate the ticks from the exponents of the values, so factor10 needs to
    # be adjusted accordingly.
    if logarithmic:
        factor10 = math.pow(10, graph_maximum if abs(graph_maximum) > abs(graph_minimum) else graph_minimum)

    # calculate the precision
    precision = int(max(-math.floor(math.log10(division)), 0))

    # make the tick marks
    tick_values = []

    def arange(start, stop, step):
        return [start + x * step for x in range(math.ceil((stop - start) / step))]

    for x in arange(graph_minimum, graph_maximum + 0.5 * division, division):
        tick_values.append(x)

    return graph_minimum, graph_maximum, tick_values, division, precision, factor10


def make_pretty_range(value_low, value_high, tight=False, ticks=5):
    return make_pretty_range2(value_low, value_high, ticks)[:-1]


class Ticker:

    def __init__(self, value_low: float, value_high: float, *, ticks: int=5):
        self._value_low = value_low
        self._value_high = value_high
        self._ticks = ticks

        self._tick_values: typing.Sequence[float] = []
        self._tick_labels: typing.Sequence[str] = []
        self._minor_tick_indices: typing.List[int] = []
        self._minimum = 0.0
        self._maximum = 0.0
        self._division = 1.0
        self._precision = 0

    def value_label(self, value: float) -> str:
        raise NotImplementedError

    @property
    def ticks(self) -> int:
        return self._ticks

    @property
    def values(self) -> typing.Sequence[float]:
        return self._tick_values

    @property
    def labels(self) -> typing.Sequence[str]:
        return self._tick_labels

    @property
    def minimum(self) -> float:
        return self._minimum

    @property
    def maximum(self) -> float:
        return self._maximum

    @property
    def division(self) -> float:
        return self._division

    @property
    def precision(self) -> int:
        return self._precision

    @property
    def minor_tick_indices(self) -> typing.List[int]:
        return self._minor_tick_indices


class LinearTicker(Ticker):

    def __init__(self, value_low: float, value_high: float, *, ticks: int=5):
        super().__init__(value_low, value_high, ticks=ticks)
        self._minimum, self._maximum, self._tick_values, self._division, self._precision, self._factor10 = make_pretty_range2(value_low, value_high, ticks=ticks)
        self._tick_labels = list(self.value_label(tick_value) for tick_value in self._tick_values)

    def __nice_label(self, value: float, precision: int, factor10: float) -> str:
        f10 = int(math.log10(factor10)) if factor10 > 0 else 0
        if abs(f10) > 5:
            f10x = int(math.log10(value)) if value > 0 else f10
            precision = max(0, f10x - f10)
            return (u"{0:0." + u"{0:d}".format(precision) + "e}").format(value)
        else:
            return (u"{0:0." + u"{0:d}".format(precision) + "f}").format(value)

    def value_label(self, value: float) -> str:
        return self.__nice_label(value, self.precision, self._factor10)


class LogTicker(Ticker):

    def __init__(self, value_low: float, value_high:float, *, ticks: int = 5, base: int = 10):
        super().__init__(value_low, value_high, ticks=ticks)
        self._base = base

        if not all([math.isfinite(val) for val in [value_low, value_high, base]]):
            self._tick_values = [1]
            self._tick_labels = ["0e+00"]
            return

        def arange(start, stop, step):
            return [start + x * step for x in range(math.ceil((stop - start) / step))]

        val_range = abs(self._value_high - self._value_low)
        self._factor_b = math.pow(self.base, math.floor(math.log(val_range, self.base))) if (self._ticks-2)/self._base > val_range > 0 else 1.0
        self._minimum = math.floor(self._value_low / self._factor_b)
        self._maximum = max(math.ceil(self._value_high / self._factor_b), self._minimum + 1)
        self._precision = round(abs(math.log(self._factor_b, self.base)))

        numdec = self._maximum - self._minimum

        while abs(numdec) > 1.5 * val_range and self._factor_b == 1.0 and numdec > 0:
            numdec -= 1

        self._division = max((numdec + 1) // self._ticks, 1)
        decades = arange(self._minimum, self._maximum + self.division, self.division)
        if self._factor_b == 1.0:
            self._maximum = self._minimum + numdec
        # We will get len(decades) * subs ticks, so calculate the number of subs we need
        num_subs = self._ticks / (val_range / self._division) if val_range > 0 else 0.0

        if self._factor_b != 1.0:
           subs = []
        elif num_subs >= (self.base - 2):
            subs = arange(2, self.base, 1)
        elif num_subs >= (self.base - 2) * 0.5:
            subs = arange(2, self.base, 2)
        elif num_subs >= (self.base - 2) * 0.25:
            subs = [round(self.base * 0.5)]
        else:
            subs = []

        if subs and self._value_high >= self._maximum:
            high_floor = math.floor(self._value_high)
            self._maximum = high_floor + math.log(math.floor(math.pow(self.base, self._value_high - high_floor)) + 1, self.base)

        tick_values = list()
        for decade_start in decades:
            decade = math.pow(self.base, decade_start * self._factor_b)
            tick_values.append(decade)
            for sub in subs:
                tick_values.append(sub * decade)
                self._minor_tick_indices.append(len(tick_values) - 1)

        self._tick_labels = [self.value_label(value) for value in tick_values]
        self._tick_values = [math.log(value, self.base) for value in tick_values]

         # Revert maximum to its original value because it is used for auto display limits
        self._maximum *= self._factor_b
        # Set minimum slightly lower than the data minimum because it is used for auto display limits
        self._minimum = self._value_low - (self._maximum - self._value_low) * 0.01

    def value_label(self, value: float) -> str:
        return (u"{0:." + u"{0:d}".format(self.precision) + "e}").format(value)

    @property
    def base(self) -> int:
        return self._base


def fit_to_aspect_ratio(rect, aspect_ratio):
    """ Return rectangle fit to aspect ratio. Returned rectangle will have float coordinates. """
    rect = FloatRect.make(rect)
    aspect_ratio = float(aspect_ratio)
    if rect.aspect_ratio > aspect_ratio:
        # height will fill entire frame
        new_size = FloatSize(height=rect.height, width=rect.height * aspect_ratio)
        new_origin = FloatPoint(y=rect.top, x=rect.left + 0.5 * (rect.width - new_size.width))
        return FloatRect(origin=new_origin, size=new_size)
    else:
        new_size = FloatSize(height=rect.width / aspect_ratio, width=rect.width)
        new_origin = FloatPoint(y=rect.top + 0.5*(rect.height - new_size.height), x=rect.left)
        return FloatRect(origin=new_origin, size=new_size)


def fit_to_size(rect, fit_size):
    """ Return rectangle fit to size (aspect ratio). """
    return fit_to_aspect_ratio(rect, float(fit_size[1])/float(fit_size[0]))


def inset_rect(rect, amount):
    """ Return rectangle inset by given amount. """
    return ((rect[0][0] + amount, rect[0][1] + amount), (rect[1][0] - 2*amount, rect[1][1] - 2*amount))


def distance(pt1, pt2):
    """ Return distance between points as float. """
    return math.sqrt(pow(pt2[0] - pt1[0], 2) + pow(pt2[1] - pt1[1], 2))


def midpoint(pt1, pt2):
    """ Return midpoint between points. """
    return (0.5 * (pt1[0] + pt2[0]), 0.5 * (pt1[1] + pt2[1]))


Margins = collections.namedtuple("Margins", ["top", "left", "bottom", "right"])
"""
    Margins for a canvas item, specified by top, left, bottom, and right.
"""


class IntPoint:

    """ A class representing an integer point (x, y). """

    def __init__(self, y=0, x=0):
        self.__y = int(y)
        self.__x = int(x)

    @classmethod
    def make(cls, value):
        """ Make an IntPoint from a y, x tuple. """
        return IntPoint(y=value[0], x=value[1])

    def __str__(self):
        return "(x={}, y={})".format(self.__x, self.__y)

    def __repr__(self):
        return "{2} (x={0}, y={1})".format(self.__x, self.__y, super(IntPoint, self).__repr__())

    def to_float_point(self) -> FloatPoint:
        return FloatPoint(y=self.y, x=self.x)

    def __get_x(self):
        """ Return the x coordinate. """
        return self.__x
    x = property(__get_x)

    def __get_y(self):
        """ Return the y coordinate. """
        return self.__y
    y = property(__get_y)

    def __eq__(self, other):
        if other is not None:
            other = IntPoint.make(other)
            return self.__x == other.x and self.__y == other.y
        return False

    def __ne__(self, other):
        if other is not None:
            other = IntPoint.make(other)
            return self.__x != other.x or self.__y != other.y
        return True

    def __neg__(self):
        return IntPoint(y=-self.__y, x=-self.__x)

    def __abs__(self):
        return math.sqrt(pow(self.__x, 2) + pow(self.__y, 2))

    def __add__(self, other):
        if isinstance(other, IntPoint):
            return IntPoint(y=self.__y + other.y, x=self.__x + other.x)
        elif isinstance(other, IntSize):
            return IntPoint(y=self.__y + other.height, x=self.__x + other.width)
        elif isinstance(other, IntRect):
            return other + self
        else:
            raise NotImplementedError()

    def __sub__(self, other):
        if isinstance(other, IntPoint):
            return IntPoint(y=self.__y - other.y, x=self.__x - other.x)
        elif isinstance(other, IntSize):
            return IntPoint(y=self.__y - other.height, x=self.__x - other.width)
        elif isinstance(other, IntRect):
            return IntRect.from_center_and_size(self - other.center, other.size)
        else:
            raise NotImplementedError()

    def __getitem__(self, index):
        return (self.__y, self.__x)[index]

    def __iter__(self):
        yield self.__y
        yield self.__x


class IntSize:

    """ A class representing an integer size (width, height). """

    def __init__(self, height=None, width=None, h=None, w=None):
        if height is not None:
            self.__height = int(height)
        elif h is not None:
            self.__height = int(h)
        else:
            self.__height = 0
        if width is not None:
            self.__width = int(width)
        elif w is not None:
            self.__width = int(w)
        else:
            self.__width = 0

    @classmethod
    def make(cls, value):
        """ Make an IntSize from a height, width tuple. """
        return IntSize(value[0], value[1])

    def __str__(self):
        return "(w={}, h={})".format(self.__width, self.__height)

    def __repr__(self):
        return "{2} (w={0}, h={1})".format(self.__width, self.__height, super(IntSize, self).__repr__())

    def to_float_size(self) -> FloatSize:
        return FloatSize(h=self.height, w=self.width)

    def __get_width(self):
        """ Return the width. """
        return self.__width
    width = property(__get_width)

    def __get_height(self):
        """ Return the height. """
        return self.__height
    height = property(__get_height)

    def __eq__(self, other):
        if other is not None:
            other = IntSize.make(other)
            return self.__width == other.width and self.__height == other.height
        return False

    def __ne__(self, other):
        if other is not None:
            other = IntSize.make(other)
            return self.__width != other.width or self.__height != other.height
        return True

    def __neg__(self):
        return IntSize(-self.__height, -self.__width)

    def __abs__(self):
        return math.sqrt(pow(self.__width, 2) + pow(self.__height, 2))

    def __add__(self, other):
        other = IntSize.make(other)
        return IntSize(self.__height + other.height, self.__width + other.width)

    def __sub__(self, other):
        other = IntSize.make(other)
        return IntSize(self.__height - other.height, self.__width - other.width)

    def __mul__(self, multiplicand):
        multiplicand = float(multiplicand)
        return IntSize(self.__height * multiplicand, self.__width * multiplicand)

    def __rmul__(self, multiplicand):
        multiplicand = float(multiplicand)
        return IntSize(self.__height * multiplicand, self.__width * multiplicand)

    def __floordiv__(self, other):
        return IntSize(self.__height / other, self.__width / other)

    def __getitem__(self, index):
        return (self.__height, self.__width)[index]

    def __iter__(self):
        yield self.__height
        yield self.__width

    def __get_aspect_ratio(self):
        """ Return the aspect ratio as a float. """
        return float(self.__width) / float(self.__height) if self.__height != 0 else 1.0
    aspect_ratio = property(__get_aspect_ratio)


class IntRect:

    """
        A class representing an integer rect (origin, size).

        Increasing size goes down and to the right from origin.
    """

    def __init__(self, origin, size):
        self.__origin = IntPoint.make(origin)
        self.__size = IntSize.make(size)

    @classmethod
    def make(cls, value):
        """ Make an IntRect from a origin, size tuple. """
        return IntRect(value[0], value[1])

    @classmethod
    def from_center_and_size(cls, center, size):
        """ Make an IntRect from a center, size. """
        center = IntPoint.make(center)
        size = IntSize.make(size)
        origin = center - IntSize(height=size.height * 0.5, width=size.width * 0.5)
        return IntRect(origin, size)

    @classmethod
    def from_tlbr(cls, top, left, bottom, right):
        """ Make an IntRect from a center, size. """
        origin = IntPoint(y=top, x=left)
        size = IntSize(height=bottom - top, width=right - left)
        return IntRect(origin, size)

    @classmethod
    def from_tlhw(cls, top, left, height, width):
        """ Make an IntRect from a center, size. """
        origin = IntPoint(y=top, x=left)
        size = IntSize(height=height, width=width)
        return IntRect(origin, size)

    def __str__(self):
        return "(o={}, s={})".format(self.__origin, self.__size)

    def __repr__(self):
        return "{2} (o={0}, s={1})".format(self.__origin, self.__size, super(IntRect, self).__repr__())

    def to_float_rect(self) -> FloatRect:
        return FloatRect.from_tlbr(self.top, self.left, self.bottom, self.right)

    def __get_origin(self):
        """ Return the origin as IntPoint. """
        return self.__origin
    origin = property(__get_origin)

    def __get_size(self):
        """ Return the size as IntSize. """
        return self.__size
    size = property(__get_size)

    def __get_width(self):
        """ Return the width. """
        return self.__size.width
    width = property(__get_width)

    def __get_height(self):
        """ Return the height. """
        return self.__size.height
    height = property(__get_height)

    def __get_left(self):
        """ Return the left coordinate. """
        return self.__origin.x
    left = property(__get_left)

    def __get_top(self):
        """ Return the top coordinate. """
        return self.__origin.y
    top = property(__get_top)

    def __get_right(self):
        """ Return the right coordinate. """
        return self.__origin.x + self.__size.width
    right = property(__get_right)

    def __get_bottom(self):
        """ Return the bottom coordinate. """
        return self.__origin.y + self.__size.height
    bottom = property(__get_bottom)

    def __get_top_left(self):
        """ Return the top left point. """
        return IntPoint(y=self.top, x=self.left)
    top_left = property(__get_top_left)

    def __get_top_right(self):
        """ Return the top right point. """
        return IntPoint(y=self.top, x=self.right)
    top_right = property(__get_top_right)

    def __get_bottom_left(self):
        """ Return the bottom left point. """
        return IntPoint(y=self.bottom, x=self.left)
    bottom_left = property(__get_bottom_left)

    def __get_bottom_right(self):
        """ Return the bottom right point. """
        return IntPoint(y=self.bottom, x=self.right)
    bottom_right = property(__get_bottom_right)

    def __get_center(self):
        """ Return the center point. """
        return IntPoint(y=(self.top + self.bottom) // 2, x=(self.left + self.right) // 2)
    center = property(__get_center)

    @property
    def slice(self) -> typing.Tuple[slice, slice]:
        return slice(self.top, self.bottom), slice(self.left, self.right)

    def __eq__(self, other):
        if other is not None:
            other = IntRect.make(other)
            return self.__origin == other.origin and self.__size == other.size
        return False

    def __ne__(self, other):
        if other is not None:
            other = IntRect.make(other)
            return self.__origin != other.origin or self.__size != other.size
        return True

    def __getitem__(self, index):
        return (tuple(self.__origin), tuple(self.__size))[index]

    def __iter__(self):
        yield tuple(self.__origin)
        yield tuple(self.__size)

    def __get_aspect_ratio(self):
        """ Return the aspect ratio as a float. """
        return float(self.width) / float(self.height) if self.height != 0 else 1.0
    aspect_ratio = property(__get_aspect_ratio)

    def contains_point(self, point):
        """
            Return whether the point is contained in this rectangle.

            Left/top sides are inclusive, right/bottom sides are not.
        """
        point = IntPoint.make(point)
        return point.x >= self.left and point.x < self.right and point.y >= self.top and point.y < self.bottom

    def intersects_rect(self, rect):
        """ Return whether the rectangle intersects this rectangle. """
        # if one rectangle is on left side of the other
        if self.left > rect.right or rect.left > self.right:
            return False
        # if one rectangle is above the other
        if self.bottom < rect.top or rect.bottom < self.top:
            return False
        return True

    def translated(self, point):
        """ Return the rectangle translated by the point or size. """
        return IntRect(self.origin + IntPoint.make(point), self.size)

    def inset(self, dx, dy=None):
        """ Returns the rectangle inset by the specified amount. """
        dy = dy if dy is not None else dx
        origin = IntPoint(y=self.top + dy, x=self.left + dx)
        size = IntSize(height=self.height - dy * 2, width=self.width - dx * 2)
        return IntRect(origin, size)

    def intersect(self, rect: IntRect) -> IntRect:
        top = max(self.top, rect.top)
        left = max(self.left, rect.left)
        bottom = min(self.bottom, rect.bottom)
        right = min(self.right, rect.right)
        return IntRect.from_tlbr(top, left, bottom, right)

    def union(self, rect: IntRect) -> IntRect:
        top = min(self.top, rect.top)
        left = min(self.left, rect.left)
        bottom = max(self.bottom, rect.bottom)
        right = max(self.right, rect.right)
        return IntRect.from_tlbr(top, left, bottom, right)

    def __add__(self, other) -> IntRect:
        if isinstance(other, IntPoint):
            return IntRect.from_center_and_size(self.center + other, self.size)
        else:
            raise NotImplementedError()

    def __sub__(self, other) -> IntRect:
        if isinstance(other, IntPoint):
            return IntRect.from_center_and_size(self.center - other, self.size)
        else:
            raise NotImplementedError()


class FloatPoint:

    """ A class representing an float point (x, y). """

    def __init__(self, y=0.0, x=0.0):
        self.__y = float(y)
        self.__x = float(x)

    @classmethod
    def make(cls, value):
        """ Make an FloatPoint from a y, x tuple. """
        return FloatPoint(y=value[0], x=value[1])

    def __str__(self):
        return "(x={}, y={})".format(self.__x, self.__y)

    def __repr__(self):
        return "{2} (x={0}, y={1})".format(self.__x, self.__y, super(FloatPoint, self).__repr__())

    def __get_x(self):
        """ Return the x coordinate. """
        return self.__x
    x = property(__get_x)

    def __get_y(self):
        """ Return the y coordinate. """
        return self.__y
    y = property(__get_y)

    def __eq__(self, other):
        if other is not None:
            other = FloatPoint.make(other)
            return self.__x == other.x and self.__y == other.y
        return False

    def __ne__(self, other):
        if other is not None:
            other = FloatPoint.make(other)
            return self.__x != other.x or self.__y != other.y
        return True

    def __neg__(self):
        return FloatPoint(y=-self.__y, x=-self.__x)

    def __abs__(self):
        return math.sqrt(pow(self.__x, 2) + pow(self.__y, 2))

    def __add__(self, other):
        if isinstance(other, FloatPoint):
            return FloatPoint(y=self.__y + other.y, x=self.__x + other.x)
        elif isinstance(other, FloatSize):
            return FloatPoint(y=self.__y + other.height, x=self.__x + other.width)
        elif isinstance(other, FloatRect):
            return other + self
        else:
            raise NotImplementedError()

    def __sub__(self, other):
        if isinstance(other, FloatPoint):
            return FloatPoint(y=self.__y - other.y, x=self.__x - other.x)
        elif isinstance(other, FloatSize):
            return FloatPoint(y=self.__y - other.height, x=self.__x - other.width)
        elif isinstance(other, FloatRect):
            return FloatRect.from_center_and_size(self - other.center, other.size)
        else:
            raise NotImplementedError()

    def __mul__(self, multiplicand) -> FloatPoint:
        multiplicand = float(multiplicand)
        return FloatPoint(y=self.__y * multiplicand, x=self.__x * multiplicand)

    def __rmul__(self, multiplicand) -> FloatPoint:
        multiplicand = float(multiplicand)
        return FloatPoint(y=self.__y * multiplicand, x=self.__x * multiplicand)

    def __truediv__(self, dividend) -> FloatPoint:
        dividend = float(dividend)
        return FloatPoint(y=self.__y / dividend, x=self.__x / dividend)

    def __getitem__(self, index):
        return (self.__y, self.__x)[index]

    def __iter__(self):
        yield self.__y
        yield self.__x

    def rotate(self, radians: float, origin: typing.Optional[FloatPoint] = None) -> FloatPoint:
        origin = origin or FloatPoint()
        dx = self.x - origin.x
        dy = self.y - origin.y
        cos_rad = math.cos(radians)
        sin_rad = math.sin(radians)
        x = origin.x + cos_rad * dx - sin_rad * dy
        y = origin.y + sin_rad * dx + cos_rad * dy
        return FloatPoint(x=x, y=y)


class FloatSize:

    """ A class representing an float size (width, height). """

    def __init__(self, height=None, width=None, h=None, w=None):
        if height is not None:
            self.__height = float(height)
        elif h is not None:
            self.__height = float(h)
        else:
            self.__height = 0.0
        if width is not None:
            self.__width = float(width)
        elif w is not None:
            self.__width = float(w)
        else:
            self.__width = 0.0

    @classmethod
    def make(cls, value):
        """ Make an FloatSize from a height, width tuple. """
        return FloatSize(value[0], value[1])

    def __str__(self):
        return "(w={}, h={})".format(self.__width, self.__height)

    def __repr__(self):
        return "{2} (w={0}, h={1})".format(self.__width, self.__height, super(FloatSize, self).__repr__())

    def __get_width(self):
        """ Return the width. """
        return self.__width
    width = property(__get_width)

    def __get_height(self):
        """ Return the height. """
        return self.__height
    height = property(__get_height)

    def __eq__(self, other):
        if other is not None:
            other = FloatSize.make(other)
            return self.__width == other.width and self.__height == other.height
        return False

    def __ne__(self, other):
        if other is not None:
            other = FloatSize.make(other)
            return self.__width != other.width or self.__height != other.height
        return True

    def __neg__(self):
        return FloatSize(-self.__height, -self.__width)

    def __abs__(self):
        return math.sqrt(pow(self.__width, 2) + pow(self.__height, 2))

    def __add__(self, other):
        other = FloatSize.make(other)
        return FloatSize(self.__height + other.height, self.__width + other.width)

    def __sub__(self, other):
        other = FloatSize.make(other)
        return FloatSize(self.__height - other.height, self.__width - other.width)

    def __mul__(self, multiplicand):
        multiplicand = float(multiplicand)
        return FloatSize(self.__height * multiplicand, self.__width * multiplicand)

    def __rmul__(self, multiplicand):
        multiplicand = float(multiplicand)
        return FloatSize(self.__height * multiplicand, self.__width * multiplicand)

    def __truediv__(self, dividend) -> FloatSize:
        dividend = float(dividend)
        return FloatSize(self.__height / dividend, self.__width / dividend)

    def __getitem__(self, index):
        return (self.__height, self.__width)[index]

    def __iter__(self):
        yield self.__height
        yield self.__width

    def __get_aspect_ratio(self):
        """ Return the aspect ratio as a float. """
        return float(self.__width) / float(self.__height) if self.__height != 0 else 1.0
    aspect_ratio = property(__get_aspect_ratio)

    def rotate(self, radians: float) -> FloatSize:
        dx = self.width
        dy = self.height
        cos_rad = math.cos(radians)
        sin_rad = math.sin(radians)
        x = cos_rad * dx - sin_rad * dy
        y = sin_rad * dx + cos_rad * dy
        return FloatSize(w=x, h=y)


class FloatRect:

    """
        A class representing an float rect (origin, size).

        Increasing size goes down and to the right from origin.
    """

    def __init__(self, origin, size):
        self.__origin = FloatPoint.make(origin)
        self.__size = FloatSize.make(size)

    @classmethod
    def make(cls, value):
        """ Make a FloatRect from a origin, size tuple. """
        return FloatRect(value[0], value[1])

    @classmethod
    def from_center_and_size(cls, center, size):
        """ Make a FloatRect from a center, size. """
        center = FloatPoint.make(center)
        size = FloatSize.make(size)
        origin = center - FloatSize(height=size.height * 0.5, width=size.width * 0.5)
        return FloatRect(origin, size)

    @classmethod
    def from_tlbr(cls, top, left, bottom, right):
        """ Make an FloatRect from a center, size. """
        origin = FloatPoint(y=top, x=left)
        size = FloatSize(height=bottom - top, width=right - left)
        return FloatRect(origin, size)

    @classmethod
    def from_tlhw(cls, top, left, height, width):
        """ Make an FloatRect from a center, size. """
        origin = FloatPoint(y=top, x=left)
        size = FloatSize(height=height, width=width)
        return FloatRect(origin, size)

    @classmethod
    def unit_rect(cls) -> FloatRect:
        return cls.from_tlhw(0, 0, 1, 1)

    def __str__(self):
        return "(o={}, s={})".format(self.__origin, self.__size)

    def __repr__(self):
        return "{2} (o={0}, s={1})".format(self.__origin, self.__size, super(FloatRect, self).__repr__())

    def __get_origin(self):
        """ Return the origin as FloatPoint. """
        return self.__origin
    origin = property(__get_origin)

    def __get_size(self):
        """ Return the size as FloatSize. """
        return self.__size
    size = property(__get_size)

    def __get_width(self):
        """ Return the width. """
        return self.__size.width
    width = property(__get_width)

    def __get_height(self):
        """ Return the height. """
        return self.__size.height
    height = property(__get_height)

    def __get_left(self):
        """ Return the left coordinate. """
        return self.__origin.x
    left = property(__get_left)

    def __get_top(self):
        """ Return the top coordinate. """
        return self.__origin.y
    top = property(__get_top)

    def __get_right(self):
        """ Return the right coordinate. """
        return self.__origin.x + self.__size.width
    right = property(__get_right)

    def __get_bottom(self):
        """ Return the bottom coordinate. """
        return self.__origin.y + self.__size.height
    bottom = property(__get_bottom)

    def __get_top_left(self):
        """ Return the top left point. """
        return FloatPoint(y=self.top, x=self.left)
    top_left = property(__get_top_left)

    def __get_top_right(self):
        """ Return the top right point. """
        return FloatPoint(y=self.top, x=self.right)
    top_right = property(__get_top_right)

    def __get_bottom_left(self):
        """ Return the bottom left point. """
        return FloatPoint(y=self.bottom, x=self.left)
    bottom_left = property(__get_bottom_left)

    def __get_bottom_right(self):
        """ Return the bottom right point. """
        return FloatPoint(y=self.bottom, x=self.right)
    bottom_right = property(__get_bottom_right)

    def __get_center(self):
        """ Return the center point. """
        return FloatPoint(y=(self.top + self.bottom) * 0.5, x=(self.left + self.right) * 0.5)
    center = property(__get_center)

    def __eq__(self, other):
        if other is not None:
            other = FloatRect.make(other)
            return self.__origin == other.origin and self.__size == other.size
        return False

    def __ne__(self, other):
        if other is not None:
            other = FloatRect.make(other)
            return self.__origin != other.origin or self.__size != other.size
        return True

    def __getitem__(self, index):
        return (tuple(self.__origin), tuple(self.__size))[index]

    def __iter__(self):
        yield tuple(self.__origin)
        yield tuple(self.__size)

    def __get_aspect_ratio(self):
        """ Return the aspect ratio as a float. """
        return float(self.width) / float(self.height) if self.height != 0 else 1.0
    aspect_ratio = property(__get_aspect_ratio)

    def contains_point(self, point):
        """
            Return whether the point is contained in this rectangle.

            Left/top sides are inclusive, right/bottom sides are not.
        """
        point = FloatPoint.make(point)
        return point.x >= self.left and point.x < self.right and point.y >= self.top and point.y < self.bottom

    def intersects_rect(self, rect):
        """ Return whether the rectangle intersects this rectangle. """
        # if one rectangle is on left side of the other
        if self.left > rect.right or rect.left > self.right:
            return False
        # if one rectangle is above the other
        if self.bottom < rect.top or rect.bottom < self.top:
            return False
        return True

    def translated(self, point):
        """ Return the rectangle translated by the point or size. """
        return FloatRect(self.origin + FloatPoint.make(point), self.size)

    def inset(self, dx, dy=None):
        """ Returns the rectangle inset by the specified amount. """
        dy = dy if dy is not None else dx
        origin = FloatPoint(y=self.top + dy, x=self.left + dx)
        size = FloatSize(height=self.height - dy * 2, width=self.width - dx * 2)
        return FloatRect(origin, size)

    def intersect(self, rect: FloatRect) -> FloatRect:
        top = max(self.top, rect.top)
        left = max(self.left, rect.left)
        bottom = min(self.bottom, rect.bottom)
        right = min(self.right, rect.right)
        return FloatRect.from_tlbr(top, left, bottom, right)

    def union(self, rect: FloatRect) -> FloatRect:
        top = min(self.top, rect.top)
        left = min(self.left, rect.left)
        bottom = max(self.bottom, rect.bottom)
        right = max(self.right, rect.right)
        return FloatRect.from_tlbr(top, left, bottom, right)

    def __add__(self, other) -> FloatRect:
        if isinstance(other, FloatPoint):
            return FloatRect.from_center_and_size(self.center + other, self.size)
        else:
            raise NotImplementedError()

    def __sub__(self, other) -> FloatRect:
        if isinstance(other, FloatPoint):
            return FloatRect.from_center_and_size(self.center - other, self.size)
        else:
            raise NotImplementedError()


def map_point(p: FloatPoint, f: FloatRect, t: FloatRect) -> FloatPoint:
    return FloatPoint(y=((p.y - f.top) / f.height) * t.height + t.top,
                      x=((p.x - f.left) / f.width) * t.width + t.left)


def map_size(s: FloatSize, f: FloatRect, t: FloatRect) -> FloatSize:
    return FloatSize(height=(s.height / f.height) * t.height,
                     width=(s.width / f.width) * t.width)


def map_rect(r: FloatRect, f: FloatRect, t: FloatRect) -> FloatRect:
    return FloatRect.from_center_and_size(map_point(r.center, f, t),
                                          map_size(r.size, f, t))

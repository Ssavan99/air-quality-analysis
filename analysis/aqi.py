"""US EPA Air Quality Index, computed from pollutant concentrations.

Breakpoints follow the EPA revision effective 6 May 2024, which lowered the
PM2.5 thresholds (AQI 50 moved from 12.0 to 9.0 ug/m3) and collapsed the old
301-400 and 401-500 bands into a single 301-500 Hazardous band.

The project is called AirQualityAnalysis but never actually computed an AQI --
it worked in raw concentrations throughout. This module supplies it.
"""

import math

# (concentration_low, concentration_high, aqi_low, aqi_high)
PM25_BREAKPOINTS = [
    (0.0, 9.0, 0, 50),
    (9.1, 35.4, 51, 100),
    (35.5, 55.4, 101, 150),
    (55.5, 125.4, 151, 200),
    (125.5, 225.4, 201, 300),
    (225.5, 325.4, 301, 500),
]

PM10_BREAKPOINTS = [
    (0, 54, 0, 50),
    (55, 154, 51, 100),
    (155, 254, 101, 150),
    (255, 354, 151, 200),
    (355, 424, 201, 300),
    (425, 604, 301, 500),
]

# AQI category names, thresholds and the EPA's own colours. These colours are
# read as meaning, not decoration, so they are fixed here and reused verbatim
# by the web front end.
CATEGORIES = [
    (0, 50, "Good", "#00E400"),
    (51, 100, "Moderate", "#FFFF00"),
    (101, 150, "Unhealthy for Sensitive Groups", "#FF7E00"),
    (151, 200, "Unhealthy", "#FF0000"),
    (201, 300, "Very Unhealthy", "#8F3F97"),
    (301, 500, "Hazardous", "#7E0023"),
]

BEYOND_INDEX = "Beyond the AQI scale"


def _truncate(value, decimals):
    factor = 10 ** decimals
    return math.floor(value * factor) / factor


def _piecewise(concentration, breakpoints, decimals):
    """Apply the EPA's piecewise-linear interpolation.

    Returns None when the concentration is above the top breakpoint. The EPA
    does not define an index there, and inventing one would be dishonest --
    Delhi goes past it regularly.
    """
    if concentration is None or concentration < 0:
        return None

    c = _truncate(concentration, decimals)
    for c_low, c_high, aqi_low, aqi_high in breakpoints:
        if c_low <= c <= c_high:
            return round(
                (aqi_high - aqi_low) / (c_high - c_low) * (c - c_low) + aqi_low
            )
    return None


def pm25_to_aqi(concentration):
    """AQI from a PM2.5 concentration in ug/m3. None if beyond the scale."""
    return _piecewise(concentration, PM25_BREAKPOINTS, decimals=1)


def pm10_to_aqi(concentration):
    """AQI from a PM10 concentration in ug/m3. None if beyond the scale."""
    return _piecewise(concentration, PM10_BREAKPOINTS, decimals=0)


def category(aqi):
    """Category name for an AQI value, or the beyond-scale label."""
    if aqi is None:
        return BEYOND_INDEX
    for low, high, name, _colour in CATEGORIES:
        if low <= aqi <= high:
            return name
    return BEYOND_INDEX


def colour(aqi):
    """EPA colour for an AQI value. Beyond-scale keeps the Hazardous maroon."""
    if aqi is None:
        return CATEGORIES[-1][3]
    for low, high, _name, hex_colour in CATEGORIES:
        if low <= aqi <= high:
            return hex_colour
    return CATEGORIES[-1][3]


def overall_aqi(pm25, pm10):
    """Overall AQI is the worst of the sub-indices, per EPA.

    A sub-index of None means that pollutant is *above* the top of the scale,
    so it is the worst one by definition. Dropping it and taking the max of
    what remains would report a lower index than the truth, and would do so
    precisely on the dirtiest hours. If either sub-index is off the scale, the
    overall value is off the scale.
    """
    sub_indices = (pm25_to_aqi(pm25), pm10_to_aqi(pm10))
    if any(value is None for value in sub_indices):
        return None
    return max(sub_indices)

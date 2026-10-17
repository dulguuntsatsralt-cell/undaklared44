"""Areas of interest (AOIs) watched by the nowcast.

IMPORTANT: coordinates are APPROXIMATE starting points. Before pulling a
time series, run `python scripts/preview_aoi.py <name>` and check the saved
image shows the road, yard or mine you expect. Adjust the box here if not.
"""
from dataclasses import dataclass


@dataclass(frozen=True)
class AOI:
    name: str
    lat: float          # box centre latitude
    lon: float          # box centre longitude
    half_km: float      # half the box width, km
    kind: str           # "border", "mine", "rail"
    note: str = ""

    def bbox(self) -> tuple[float, float, float, float]:
        """(min_lon, min_lat, max_lon, max_lat) in degrees."""
        import math
        dlat = self.half_km / 111.0
        dlon = self.half_km / (111.0 * math.cos(math.radians(self.lat)))
        return (self.lon - dlon, self.lat - dlat, self.lon + dlon, self.lat + dlat)


AOIS = {
    a.name: a
    for a in [
        AOI("gashuunsukhait", 42.411285, 107.572502, 4.0, "border",
            "Main coal crossing to China (Ganqimaodu side). Core truck-queue signal. "
            "Centre taken from Google Maps satellite view, 2026-10-13."),
        AOI("coal_road", 42.858, 106.860, 4.0, "road",
            "Open stretch of the paved Ukhaa Khudag - Gashuun Sukhait coal road (OpenStreetMap way "
            "258363586), about 75 km from the border, away from towns. Moving-truck counts."),
        AOI("tavan_tolgoi", 43.60, 105.50, 6.0, "mine",
            "Tavan Tolgoi / Ukhaa Khudag mine area: stockpiles and loading. VERIFY."),
        AOI("shiveekhuren", 42.95, 101.33, 4.0, "border",
            "Western coal crossing (Ceke side). VERIFY."),
        AOI("zamyn_uud", 43.72, 111.90, 4.0, "rail",
            "Zamyn-Uud / Erenhot rail crossing. VERIFY."),
    ]
}

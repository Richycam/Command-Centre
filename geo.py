from __future__ import annotations

import re
from typing import Optional


class GeoIndex:
    LOCATIONS: dict[str, tuple[float, float]] = {
        "usa": (39.8, -98.5), "united states": (39.8, -98.5), "america": (39.8, -98.5), "u.s.": (39.8, -98.5), "washington": (38.9, -77.0),
        "new york": (40.7, -74.0), "los angeles": (34.0, -118.2), "san francisco": (37.8, -122.4),
        "chicago": (41.9, -87.6), "houston": (29.8, -95.4), "miami": (25.8, -80.2), "atlanta": (33.8, -84.4),
        "boston": (42.4, -71.1), "seattle": (47.6, -122.3), "dallas": (32.8, -96.8), "philadelphia": (39.9, -75.2),
        "san jose": (37.3, -121.9), "austin": (30.3, -97.7), "detroit": (42.3, -83.0), "phoenix": (33.4, -112.1),
        "minneapolis": (44.9, -93.3), "denver": (39.7, -104.9), "orlando": (28.5, -81.4), "san antonio": (29.4, -98.5),
        "toronto": (43.7, -79.4), "ottawa": (45.4, -75.7), "montreal": (45.5, -73.6), "vancouver": (49.3, -123.1), "calgary": (51.0, -114.0),
        "edmonton": (53.5, -113.5), "winnipeg": (49.9, -97.1), "halifax": (44.6, -63.6),
        "uk": (54.0, -2.0), "britain": (54.0, -2.0), "london": (51.5, -0.1), "manchester": (53.5, -2.2), "birmingham": (52.5, -1.9),
        "glasgow": (55.9, -4.3), "leeds": (53.8, -1.5), "bristol": (51.5, -2.6), "edinburgh": (55.9, -3.2), "cardiff": (51.5, -3.2), "belfast": (54.6, -5.9),
        "ireland": (53.3, -7.7), "dublin": (53.3, -6.3),
        "france": (46.6, 2.2), "paris": (48.9, 2.3), "marseille": (43.3, 5.4), "lyon": (45.8, 4.8),
        "germany": (51.2, 10.4), "berlin": (52.5, 13.4), "munich": (48.1, 11.6), "frankfurt": (50.1, 8.7),
        "netherlands": (52.1, 5.3), "amsterdam": (52.4, 4.9),
        "belgium": (50.8, 4.3), "brussels": (50.8, 4.4),
        "spain": (40.5, -3.7), "madrid": (40.4, -3.7), "barcelona": (41.4, 2.2),
        "italy": (41.9, 12.6), "rome": (41.9, 12.5), "milan": (45.5, 9.2), "venice": (45.4, 12.3),
        "switzerland": (46.8, 8.2), "zurich": (47.4, 8.5), "geneva": (46.2, 6.1),
        "austria": (47.8, 13.0), "vienna": (48.2, 16.4),
        "sweden": (60.1, 18.6), "stockholm": (59.3, 18.1),
        "norway": (60.5, 8.0), "oslo": (59.9, 10.8),
        "finland": (61.9, 25.7), "helsinki": (60.2, 24.9),
        "denmark": (56.0, 9.9), "copenhagen": (55.7, 12.6),
        "poland": (51.9, 19.1), "warsaw": (52.2, 21.0), "krakow": (50.1, 19.9),
        "czech republic": (49.8, 15.5), "prague": (50.1, 14.4),
        "hungary": (47.2, 19.5), "budapest": (47.5, 19.0),
        "romania": (45.9, 24.8), "bucharest": (44.4, 26.1),
        "greece": (39.1, 21.8), "athens": (37.9, 23.7),
        "portugal": (39.5, -8.0), "lisbon": (38.7, -9.1),
        "russia": (61.5, 105.3), "moscow": (55.7, 37.6), "saint petersburg": (59.9, 30.3),
        "ukraine": (48.4, 31.2), "kyiv": (50.4, 30.5), "odessa": (46.5, 30.7),
        "belarus": (53.7, 27.9), "lithuania": (55.2, 23.9), "latvia": (56.9, 24.1), "estonia": (58.6, 25.0),
        "china": (35.0, 103.0), "beijing": (39.9, 116.4), "shanghai": (31.2, 121.5),
        "hong kong": (22.3, 114.2), "taiwan": (23.7, 121.0), "taipei": (25.0, 121.5),
        "japan": (36.2, 138.3), "tokyo": (35.7, 139.7), "osaka": (34.7, 135.5),
        "south korea": (35.9, 127.7), "seoul": (37.6, 126.9),
        "north korea": (40.3, 127.5), "pyongyang": (39.0, 125.8),
        "india": (20.6, 79.0), "delhi": (28.6, 77.2), "mumbai": (19.1, 72.9),
        "pakistan": (30.4, 69.3), "karachi": (24.9, 67.0), "bangladesh": (23.6, 90.4), "dhaka": (23.8, 90.4),
        "sri lanka": (7.9, 80.7), "colombo": (6.9, 79.9), "nepal": (28.4, 84.1), "kathmandu": (27.7, 85.3),
        "afghanistan": (33.9, 67.7), "iran": (32.4, 53.7), "iraq": (33.3, 44.4), "baghdad": (33.3, 44.4),
        "saudi": (23.9, 45.1), "riyadh": (24.7, 46.7), "uae": (24.5, 54.4), "dubai": (25.1, 55.2), "abu dhabi": (24.5, 54.4),
        "qatar": (25.3, 51.2), "doha": (25.3, 51.5), "oman": (23.6, 58.5), "muscat": (23.6, 58.5),
        "kuwait": (29.4, 47.9), "jordan": (31.9, 35.9), "amman": (31.9, 35.9),
        "lebanon": (33.9, 35.5), "syria": (34.8, 39.0), "turkey": (38.9, 35.2), "istanbul": (41.0, 28.9),
        "israel": (31.0, 34.8), "gaza": (31.5, 34.5), "palestine": (31.8, 35.2),
        "egypt": (26.8, 30.8), "cairo": (30.0, 31.2), "nigeria": (9.1, 8.7), "lagos": (6.5, 3.4),
        "south africa": (-30.6, 22.9), "cape town": (-33.9, 18.4), "johannesburg": (-26.2, 28.0),
        "kenya": (1.3, 36.8), "nairobi": (-1.3, 36.8), "ethiopia": (8.9, 38.7), "addis ababa": (9.0, 38.7),
        "uganda": (1.4, 32.3), "kampala": (0.3, 32.6), "tanzania": (-6.8, 39.2), "dar es salaam": (-6.8, 39.3),
        "morocco": (31.8, -7.9), "rabat": (34.0, -6.8), "algeria": (28.0, 3.1), "algiers": (36.7, 3.2),
        "tunisia": (34.0, 9.0), "tunis": (36.8, 10.2), "libya": (26.8, 17.2), "tripoli": (32.9, 13.2),
        "niger": (17.6, 8.1), "senegal": (14.4, -14.8), "ivory coast": (7.9, -5.7),
        "cameroon": (7.4, 12.4), "ghana": (7.9, -1.0),
        "brazil": (-14.2, -51.9), "brasilia": (-15.8, -47.9), "rio de janeiro": (-22.9, -43.2),
        "argentina": (-34.6, -58.5), "buenos aires": (-34.6, -58.4),
        "chile": (-33.5, -70.7), "santiago": (-33.4, -70.7),
        "peru": (-9.2, -75.0), "lima": (-12.0, -77.0),
        "colombia": (4.6, -74.1), "bogota": (4.7, -74.1),
        "venezuela": (6.4, -66.6), "caracas": (10.5, -66.9),
        "mexico": (23.6, -102.5), "mexico city": (19.4, -99.1),
        "cuba": (21.5, -77.8), "havana": (23.1, -82.4),
        "panama": (8.5, -80.8), "panama city": (8.9, -79.5),
        "dominican republic": (18.7, -70.0), "haiti": (18.5, -72.3),
        "australia": (-25.3, 133.8), "sydney": (-33.9, 151.2), "melbourne": (-37.8, 144.9),
        "new zealand": (-40.9, 174.9), "auckland": (-36.8, 174.8),
        "europe": (54.5, 15.3), "africa": (2.0, 20.0),
        "eu": (50.8, 4.3),
    }

    @classmethod
    def find_all(cls, headline: str) -> list[tuple[str, float, float]]:
        text = headline.lower()
        return [(n, lat, lon) for n, (lat, lon) in cls.LOCATIONS.items()
                if re.search(rf"\b{n}\b", text)]

    @classmethod
    def locate(cls, headline: str) -> Optional[tuple[float, float]]:
        hits = cls.find_all(headline)
        return (hits[0][1], hits[0][2]) if hits else None

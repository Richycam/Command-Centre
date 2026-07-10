# Command Centre


<img width="3397" height="1290" alt="image" src="https://github.com/user-attachments/assets/1c7fa602-a7c8-4255-96da-bddea3f1509e" />



A more fun way to read the news — Command Centre pulls live headlines from major RSS feeds and plots them as animated events on an interactive 3D globe, categorized by type (military, political, financial, disaster, general) with a pulsing, rotating visual style.

## Features

- **Live globe dashboard** — Built with Dash + Plotly, rendering an orthographic (3D) rotating globe.
- **Multi-source RSS aggregation** — Pulls from BBC, Reuters, Al Jazeera, Hacker News, NYT, CNN, AP, The Guardian, FT, Bloomberg, CNBC, MarketWatch, WSJ, and DW, with automatic fallback URLs per source.
- **Automatic geotagging** — Headlines are matched against a built-in gazetteer (`geo.py`) of countries/cities to plot approximate coordinates.
- **Keyword-based event classification** — Each headline is tagged as `military`, `political`, `financial`, `disaster`, or `general` using keyword matching (`classifiers.py`), each with its own marker color and symbol.
- **Military movement arcs** — For military-tagged stories, the app attempts to detect a secondary location (a "target") and draws an animated arc between origin and target.
- **Click-to-inspect detail panel** — Clicking a marker on the globe shows headline, source, coordinates, movement target (if any), and publish time.
- **Deduplication** — Aggregated fetches across sources are deduplicated by title + rounded coordinates.

## Project Structure

| File | Purpose |
|---|---|
| `command_centre.py` | Main entry point. Builds the Dash app, the Plotly globe figure (`GlobeFigureBuilder`), and wires up callbacks (click-to-detail, legend positioning, refresh). |
| `feeds.py` | Defines `NewsSource`/`NewsEvent` dataclasses, the `NEWS_SOURCES` list of RSS feeds, `NewsFeed` (per-source fetch/parse logic), and `FeedManager` (aggregation across all sources with dedupe). |
| `classifiers.py` | `EventCategory` enum, color/symbol maps, keyword lists, and `EventClassifier` for tagging headlines and detecting military "movement" targets. |
| `geo.py` | `GeoIndex` — a static lookup table of country/city names to (lat, lon) coordinates, with `find_all`/`locate` helpers for regex-based headline matching. |
| `requirements.txt` | Python dependencies (`dash`, `plotly`, `feedparser`, `requests`). |
| `setup_command_centre.sh` | Ubuntu bootstrap script: installs system prerequisites, creates a user-owned virtualenv, and installs Python packages. |

## Requirements
- Python 3.10+ 

## Installation

### Linux

```bash
chmod +x setup_command_centre.sh
./setup_command_centre.sh
source venv/bin/activate
python command_centre.py
```



### Windows 

```bash
pip install -r requirements.txt
python command_centre.py
```


Then open your browser to:

```
http://127.0.0.1:8050
```

Click on any marker on the globe to view headline details in the side panel. Deactivate the environment when finished with `deactivate`.

## Event Categories

| Category | Color | Symbol |
|---|---|---|
| Military | Red (`#ff3b3b`) | Triangle-up |
| Political | Yellow (`#ffd23b`) | Square |
| Financial | Green (`#3bff8a`) | Diamond |
| Disaster | Purple (`#c93bff`) | X |
| General | Blue (`#3bc9ff`) | Open circle |

## Notes & Limitations

- Geolocation is based on a static keyword gazetteer, so headlines mentioning unlisted locations won't be plotted.
- Classification uses simple keyword matching, not NLP/ML, so misclassification can occur on ambiguous headlines.
- Some RSS feeds (e.g., Reuters, AP, Bloomberg) may be inconsistently available or rate-limited depending on region and time.




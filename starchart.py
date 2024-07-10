from datetime import datetime
import geopy.adapters
from geopy.geocoders import Nominatim
import geopy.geocoders
from tzwhere import tzwhere
from pytz import timezone, utc

import numpy as np
import matplotlib.pyplot as plt
from matplotlib.collections import LineCollection
from matplotlib.patches import Circle

from skyfield.api import Star, load, wgs84
from skyfield.data import hipparcos
from skyfield.projections import build_stereographic_projection

from timezonefinder import TimezoneFinder

import ssl
import certifi

eph = load('de421.bsp')

with load.open(hipparcos.URL) as f:
    stars = hipparcos.load_dataframe(f)

where = '부산광역시 가야동'
when = '1995-01-15 00:00'

ssl_context = ssl.create_default_context(cafile=certifi.where())
locator = Nominatim(user_agent="tae0y/thatnightsky", ssl_context=ssl_context)
print('[DEBUG] locator.headers - ', locator.headers)

location = locator.geocode(where)
print('[DEBUG] location - ', location)

lat, long = location.latitude, location.longitude

dt = datetime.strptime(when, '%Y-%m-%d %H:%M')

tf = TimezoneFinder()
timezone_str = tf.timezone_at(lat=lat, lng=long)
local = timezone(timezone_str)

local_dt = local.localize(dt, is_dst=None)
utc_dt = local_dt.astimezone(utc)

print(f"[DEBUG] local_dt {local_dt}")
print(f"[DEBUG] utc_dt {utc_dt}")

sun = eph['sun']
earth = eph['earth']

ts = load.timescale()
t = ts.from_datetime(utc_dt)

observer = wgs84.latlon(latitude_degrees=lat, longitude_degrees=long).at(t)

position = observer.from_altaz(alt_degrees=90, az_degrees=0)

ra, dec, distance = observer.radec()
center_object = Star(ra=ra, dec=dec)

center = earth.at(t).observe(center_object)
projection = build_stereographic_projection(center)
field_of_view_degrees = 180.0

star_positions = earth.at(t).observe(Star.from_dataframe(stars))
stars['x'], stars['y'] = projection(star_positions)

chart_size = 10
max_star_size = 100
limiting_magnitude = 10

bright_stars = (stars.magnitude <= limiting_magnitude)
magnitude = stars['magnitude'][bright_stars]

fig, ax = plt.subplots(figsize=(chart_size, chart_size))
    
border = plt.Circle((0, 0), 1, color='black', fill=True)
ax.add_patch(border)

marker_size = max_star_size * 10 ** (magnitude / -2.5)

ax.scatter(stars['x'][bright_stars], stars['y'][bright_stars],
           s=marker_size, color='white', marker='.', linewidths=0, 
           zorder=2)

horizon = Circle((0, 0), radius=1, transform=ax.transData)
for col in ax.collections:
    col.set_clip_path(horizon)

ax.set_xlim(-1, 1)
ax.set_ylim(-1, 1)
plt.axis('off')

results_dir = './results/'
filename = f"{where}__{when}.png".replace(" ", "_").replace(":","_").replace("-","_")
print('[DEBUG] filename - ', filename)
plt.savefig(results_dir + filename)
plt.show()
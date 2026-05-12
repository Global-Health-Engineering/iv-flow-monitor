"""
Strip the bright-green KiCad 3D-render background from dripito-v2-top-raw.png.
Uses HSV hue gating + connected-component labeling so green PCB features
(vias, exposed pads) inside the board aren't accidentally cleared.
"""
from PIL import Image
import numpy as np
from scipy.ndimage import label

import sys

if len(sys.argv) >= 3:
    SRC, DST = sys.argv[1], sys.argv[2]
else:
    SRC = "D:/Dripito/pages-astro/public/pcb/dripito-v2-top-raw.png"
    DST = "D:/Dripito/pages-astro/public/pcb/dripito-v2-top.png"

img = Image.open(SRC).convert("RGBA")
arr = np.array(img)
h, w = arr.shape[:2]

r = arr[..., 0].astype(float)
g = arr[..., 1].astype(float)
b = arr[..., 2].astype(float)

mx = np.maximum(np.maximum(r, g), b)
mn = np.minimum(np.minimum(r, g), b)
delta = mx - mn
delta_safe = np.where(delta > 0, delta, 1)

hue = np.zeros_like(mx)
m_r = (mx == r) & (delta > 0)
m_g = (mx == g) & (delta > 0)
m_b = (mx == b) & (delta > 0)
hue = np.where(m_r, ((g - b) / delta_safe) % 6, hue)
hue = np.where(m_g, ((b - r) / delta_safe) + 2, hue)
hue = np.where(m_b, ((r - g) / delta_safe) + 4, hue)
hue *= 60  # 0–360°

sat = np.where(mx > 0, delta / np.maximum(mx, 1), 0)
val = mx / 255.0

# Greenish background: hue ~120°, high saturation, decent value.
# Generous hue band + lower sat threshold so we catch anti-aliased edges,
# but the connected-component step prevents bleeding into the PCB.
green_mask = (hue > 70) & (hue < 170) & (sat > 0.25) & (val > 0.2)

# Find connected components and keep only those touching the image border.
labels, n = label(green_mask)
border_ids = set()
border_ids.update(np.unique(labels[0, :]).tolist())
border_ids.update(np.unique(labels[-1, :]).tolist())
border_ids.update(np.unique(labels[:, 0]).tolist())
border_ids.update(np.unique(labels[:, -1]).tolist())
border_ids.discard(0)

bg = np.isin(labels, list(border_ids))

arr[bg, 3] = 0

# Soften the alpha edge by 1-px feather where alpha just dropped to 0
# but the original pixel was very saturated green — light cleanup of fringe.
fringe = green_mask & ~bg & (sat > 0.4) & (hue > 80) & (hue < 160)
arr[fringe, 3] = (arr[fringe, 3].astype(int) // 3).astype(np.uint8)

result = Image.fromarray(arr, "RGBA")
result.save(DST, "PNG", optimize=True)

print(f"Removed background pixels: {bg.sum():,} of {h*w:,}")
print(f"Saved: {DST}")
print(f"Image size: {w}×{h}")
print(f"Aspect ratio: {w/h:.4f}")

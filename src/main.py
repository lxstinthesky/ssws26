import snowmicropyn
from snowmicropyn.parameterizations.calonne_richter2020 import CalonneRichter2020
from matplotlib import pyplot as plt
import numpy as np
from pathlib import Path
import re

# guarantee ordering of files
def natural_sort_key(s):
    return [int(text) if text.isdigit() else text.lower() for text in re.split(r'(\d+)', s.stem)]

DATA_DIR = Path("src/data/2026-02-25")
files = sorted(DATA_DIR.glob('*.PNT'), key=natural_sort_key)

# parametrization for alpine snowpacks
param = CalonneRichter2020()
lamb=0 # not needed, needs to provided anyway
f0=0 # not needed, needs to provided anyway
delta=0 # not needed, needs to provided anyway

WINDOW_SIZE = 5 # in mm
PIT_HEIGHT = 820 # in mm

fig, ax = plt.subplots(2, 5, figsize=(15, 8), sharex=True, sharey=True)

for n, file in enumerate(files):
    print(f"processing file {file}")

    p = snowmicropyn.Profile.load(file)

    # extract the measured properties
    distance = p.samples.distance
    force = p.samples.force

    print(distance.iloc[1])

     # find the surface, set the marker
    surface = p.detect_surface()
    # did not bottom out, use the lowest
    bottom = distance.iloc[-1]
    
    # cut the force
    snowpit_mask = distance.between(surface, bottom)

    distance = distance[snowpit_mask]
    force = force[snowpit_mask]

    # set distance to zero at surface of snowpit
    distance -= distance.iloc[0]

    # Bin the data 
    bin_edges = np.arange(0, distance.max() + WINDOW_SIZE, WINDOW_SIZE)
    bin_centers = bin_edges[:-1] + WINDOW_SIZE / 2
    force_binned = []
    for i in range(len(bin_edges) - 1):
        mask = (distance >= bin_edges[i]) & (distance < bin_edges[i+1])
        if np.any(mask):
            force_binned.append(force[mask].mean())
        else:
            force_binned.append(np.nan)
    force_binned = np.array(force_binned)
    binned_distance = bin_centers

    LL = np.full_like(force_binned, WINDOW_SIZE)

    # in kg/m³
    density = param.density(F_m=force_binned, LL=LL, lamb=lamb, f0=f0, delta=delta)
    # in m²/kg
    ssa = param.ssa(density=density, F_m=force_binned, LL=LL, lamb=lamb, f0=f0, delta=delta)

    # for plotting, we prefer 0 at the top (surface), increasing downward (height)
    binned_height = binned_distance - binned_distance.max()  # 0 at top, positive downward
    binned_height += PIT_HEIGHT

    # convert to cm
    binned_height /= 10

    binned_height = np.flip(binned_height)

    row = n // 5
    col = n % 5
    ax[row, col].plot(density, binned_height)
    ax[row, col].set_title(p.name)
    ax[row, col].set_xlabel('Density [kg/m³]')
    ax[row, col].set_ylabel('Depth [cm]')
    ax[row, col].hlines(y=[PIT_HEIGHT / 10], xmin=density.min(), xmax=density.max(), label="Snowpit surface", color="C1")
    ax[row, col].hlines(y=[74, 62, 49, 33, 20], xmin=density.min(), xmax=density.max(), label="Top of each layer", color="C1", ls="dotted")

plt.tight_layout()
plt.show()
import snowmicropyn
from snowmicropyn.parameterizations.calonne_richter2020 import CalonneRichter2020
from matplotlib import pyplot as plt
import numpy as np
from scipy.stats import mode
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

for n, file in enumerate(files):
    print(f"processing file {file}")

    p = snowmicropyn.Profile.load(file)

    # extract the measured properties
    distance = p.samples.distance
    force = p.samples.force

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

    # Bin the data: for each bin, collect force values from all measurements
    if n == 0:
        bin_edges = np.arange(0, distance.max() + WINDOW_SIZE, WINDOW_SIZE)
        bin_centers = bin_edges[:-1] + WINDOW_SIZE / 2
        binned_distance = bin_centers
        # Create a list of lists, one for each bin
        force_bins = [[] for _ in range(len(bin_edges) - 1)]

    for i in range(len(bin_edges) - 1):
        mask = (distance >= bin_edges[i]) & (distance < bin_edges[i+1])
        # Add all force values in this bin to the corresponding list
        force_bins[i].extend(force[mask].tolist())

# Now force_bins is a list of lists: force_bins[bin] = [all force values from all measurements in that bin]
# You can now process each bin as needed, e.g.:
# force_bin_means = [np.mean(bin) if len(bin) > 0 else np.nan for bin in force_bins]
force_binned = []
err_low = []
err_high = []
for bin in force_bins:
    bin_np = np.array(bin)
    val = mode(bin_np, nan_policy='omit').mode
    low, high = np.percentile(bin_np, [2.5, 97.5])
    err_low.append(val - low)
    err_high.append(high - val)
    force_binned.append(val)

force_binned = np.array(force_binned)
err_low = np.array(err_low)
err_high = np.array(err_high)

LL = np.full_like(force_binned, WINDOW_SIZE)

# for plotting, we prefer 0 at the top (surface), increasing downward (height)
binned_height = binned_distance - binned_distance.max()  # 0 at top, positive downward
binned_height += PIT_HEIGHT

# convert to cm
binned_height /= 10

binned_height = np.flip(binned_height)

plt.xlabel('Force [N]')
plt.ylabel('Depth [cm]')
#plt.hlines(y=[PIT_HEIGHT / 10], xmin=density.min(), xmax=density.max(), label="Snowpit surface", color="C1")
#plt.hlines(y=[74, 62, 49, 33, 20], xmin=density.min(), xmax=density.max(), label="Top of each layer", color="C1", ls="dotted")

# Calculate lower and upper bounds for the fill
force_binned = force_binned.flatten() if force_binned.ndim > 1 else force_binned
err_low = err_low.flatten() if err_low.ndim > 1 else err_low
err_high = err_high.flatten() if err_high.ndim > 1 else err_high
lower = force_binned - err_low
upper = force_binned + err_high

plt.fill_betweenx(binned_height, lower, upper, color='lightgray', alpha=0.7, label='95% CI')
plt.plot(force_binned, binned_height, color='C0', label='Mode')
plt.legend()
plt.show()
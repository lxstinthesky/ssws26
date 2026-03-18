import snowmicropyn
from snowmicropyn.parameterizations.calonne_richter2020 import CalonneRichter2020
from snowmicropyn.loewe2012 import calc
import matplotlib
matplotlib.use("Agg")
from matplotlib import pyplot as plt
import numpy as np
from pathlib import Path
import re
from scipy.interpolate import interp1d

# guarantee ordering of files
def natural_sort_key(s):
    return [int(text) if text.isdigit() else text.lower() for text in re.split(r'(\d+)', s.stem)]

DATE = "2026-02-26"
if "-25" in DATE:
    SITE = "Valley"
    depth = [78.5, 68.5, 56, 43.5, 26.5, 10]

    x2 = [557, 250, 233, 264, 248, 254]
    x2_r = list(reversed(x2))

    x3 = [212, 160, 181, 213, 180, 205]
    x3_r = list(reversed(x3)) 

else:
    SITE = "Mountain"

DATA_DIR = Path(f"src/data/{DATE}")
files = sorted(DATA_DIR.glob('*.PNT'), key=natural_sort_key)

# parametrization for alpine snowpacks
param = CalonneRichter2020()
lamb=0 # not needed, needs to provided anyway
f0=0 # not needed, needs to provided anyway
delta=0 # not needed, needs to provided anyway

# parameters for density and ssa computation
WINDOW_SIZE = 1 # in mm
OVERLAP = 50 # in percent

BIN_SIZE = 5 # in mm, for statistics

if "-25" in DATE:
    PIT_HEIGHT = 820 # in mm
    LAYERS = [74, 62, 49, 33, 20] # in cm
else:
    PIT_HEIGHT = 1750 # in mm
    LAYERS = [125, 91, 78, 59, 14] # in cm

all_density = []
all_ssa = []

for n, file in enumerate(files):
    print(f"processing file {file}")

    p = snowmicropyn.Profile.load(file)


    # Extract and cut measured properties, set distance to zero at surface
    distance = p.samples.distance
    force = p.samples.force
    surface = p.detect_surface()
    bottom = distance.iloc[-1]
    snowpit_mask = distance.between(surface, bottom)
    df = (
        p.samples.loc[snowpit_mask, ['distance', 'force']]
        .assign(distance=lambda d: d['distance'] - d['distance'].iloc[0])
        .reset_index(drop=True)
    )

    # calculate length between ruptures, same as Calonne et al 2020
    result = calc(df, WINDOW_SIZE, OVERLAP)
    distance = result['distance']
    force = result['force_median']
    LL = result['L2012_L']

    # calculate density and SSA
    # in kg/m³
    density = param.density(F_m=force, LL=LL, lamb=lamb, f0=f0, delta=delta)

    # in m²/kg
    ssa = param.ssa(density=density, F_m=force, LL=LL, lamb=lamb, f0=f0, delta=delta)


    bin_edges = np.arange(0, distance.max() + BIN_SIZE, BIN_SIZE)
    bin_centers = bin_edges[:-1] + BIN_SIZE / 2
    force_binned = []
    density_binned = []
    ssa_binned = []
    for i in range(len(bin_edges) - 1):
        mask = (distance >= bin_edges[i]) & (distance < bin_edges[i+1])
        if np.any(mask):
            force_binned.append(force[mask].mean())
            density_binned.append(density[mask].mean())
            ssa_binned.append(ssa[mask].mean())
        else:
            print("nothing to append")
            force_binned.append(np.nan)
            density_binned.append(np.nan)
            ssa_binned.append(np.nan)

    force_binned = np.array(force_binned)
    density_binned = np.array(density_binned)
    ssa_binned = np.array(ssa_binned)

    binned_distance = bin_centers

    # rescale to match other recordings
    binned_height = binned_distance - binned_distance.max()
    binned_height += PIT_HEIGHT

    # convert to cm
    binned_height /= 10

    # flip for plotting
    binned_height = np.flip(binned_height)

    # convert to 1/mm
    #ssa_binned *= 0.916

    all_density.append((density_binned, binned_height))
    all_ssa.append((ssa_binned, binned_height))




# Define the common height grid based on the first profile, from PIT_HEIGHT to 10 cm
height_grid = all_density[0][1]

# Interpolate (and extrapolate) all density profiles onto this grid
interpolated_densities = []
for density, binned_height in all_density:
    
    interp_density = interp1d(binned_height, density, fill_value="extrapolate")

    d = interp_density(height_grid)

    interpolated_densities.append(d)

interpolated_ssa = []
for ssa, binned_height in all_ssa:
    
    interp_ssa = interp1d(binned_height, ssa, fill_value="extrapolate")

    s = interp_ssa(height_grid)

    interpolated_ssa.append(s)

interpolated_densities = np.array(interpolated_densities)
interpolated_ssa = np.array(interpolated_ssa)

mean_density = np.mean(interpolated_densities, axis=0)
low_density_95 = np.percentile(interpolated_densities, 2.5, axis=0)
high_density_95 = np.percentile(interpolated_densities, 97.5, axis=0)
low_density_67 = np.percentile(interpolated_densities, 16, axis=0)
high_density_67 = np.percentile(interpolated_densities, 84, axis=0)

mean_ssa = np.mean(interpolated_ssa, axis=0)
low_ssa_95 = np.percentile(interpolated_ssa, 2.5, axis=0)
high_ssa_95 = np.percentile(interpolated_ssa, 97.5, axis=0)
low_ssa_67 = np.percentile(interpolated_ssa, 16, axis=0)
high_ssa_67 = np.percentile(interpolated_ssa, 84, axis=0)


#############################################################
## DENSITY PLOT 
#############################################################

plt.figure()
plt.fill_betweenx(height_grid, low_density_95, high_density_95, color='lightgray', alpha=0.5, label='95% Percentile')
plt.fill_betweenx(height_grid, low_density_67, high_density_67, color='lightgray', alpha=0.9, label='67% Percentile')
plt.plot(mean_density, height_grid, 'C0-', label='Mean density')
plt.xlabel('Density [kg/m³]')
plt.ylabel('Depth [cm]')
plt.hlines(y=[PIT_HEIGHT / 10], xmin=low_density_95.min(), xmax=high_density_95.max(), label="Snowpit surface", color="C1")

if "-25" in DATE:
    plt.hlines(y=LAYERS, xmin=low_density_95.min(), xmax=high_density_95.max(), label="Top of each layer", color="C1", ls="dotted")
    plt.scatter(x2, depth, label="Density cutter", color="turquoise", marker="o")
    plt.scatter(x3, depth, label="Denoth", color="magenta", marker=".")

else:
    plt.hlines(y=LAYERS, xmin=low_density_95.min(), xmax=high_density_95.max(), label="Top of each layer", color="C1", ls="dotted")


plt.legend()
plt.title(f"SMP Mean Density Profile ({SITE})")
plt.savefig(f"smp_density_{SITE}.png")
#plt.show()



plt.cla()
#############################################################
## SSA PLOT 
#############################################################

plt.fill_betweenx(height_grid, low_ssa_95, high_ssa_95, color='lightgray', alpha=0.5, label='95% Percentile')
plt.fill_betweenx(height_grid, low_ssa_67, high_ssa_67, color='lightgray', alpha=0.9, label='67% Percentile')
plt.plot(mean_ssa, height_grid, 'C2-', label='Mean SSA')
plt.xlabel('SSA [m²/kg]')
plt.ylabel('Depth [cm]')
plt.hlines(y=[PIT_HEIGHT / 10], xmin=low_ssa_95.min(), xmax=high_ssa_95.max(), label="Snowpit surface", color="C1")

if "-25" in DATE:
    plt.hlines(y=LAYERS, xmin=low_ssa_95.min(), xmax=high_ssa_95.max(), label="Top of each layer", color="C1", ls="dotted")
else:
    plt.hlines(y=LAYERS, xmin=low_ssa_95.min(), xmax=high_ssa_95.max(), label="Top of each layer", color="C1", ls="dotted")

plt.legend()
plt.title(f"SMP Mean SSA Profile ({SITE})")
plt.savefig(f"smp_ssa_{SITE}.png")
#plt.show()

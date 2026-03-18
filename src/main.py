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
    PIT_HEIGHT = 820 # in mm
    LAYERS = [74, 62, 49, 33, 20] # in cm

    depth = [78.5, 68.5, 56, 43.5, 26.5, 10] # of density cutter measurements

    x2 = [557, 250, 233, 264, 248, 254]
    x2_r = list(reversed(x2))

    x3 = [212, 160, 181, 213, 180, 205]
    x3_r = list(reversed(x3)) 

    x_lim_density = (0, 600) # density limits

    depth_temp = [82, 78.5, 68.5, 56, 43.5, 26.5, 10]
    temp = [-5.6, -5.3, -1.1, 0, -0.1, -0.1, 0]

    #PLOTTING THE DEPTH at which SSA taken (surface each layer)
    depth_ssa = [82, 79, 74, 62, 49, 33, 20]
    depth_r = list(reversed(depth_ssa))

    #ADDING THE SSA VALUES FROM DIFFERENT INSTRUMENTS 
    #Infrasnow
    xI = [5.1, 8.6, 26.2, 31.8, 25.4, 24.7, 13.5]
    xI_r = list(reversed(xI))

    xI1 = [5.3, 11.5, 22.3, 39.8, 27.4, 26.2, 18.3]
    xI1_r = list(reversed(xI1))


    depth_miss = [82, 79, 74, 62, 49, 33]
    depth_r_miss = list(reversed(depth_miss))
    xI2 = [7.3, 10.6, 29.4, 28.3, 31.4, 22.2]
    xI2_r = list(reversed(xI2))

    #Icecube
    ic = [11.5, 9.9, 31, 31.5, 28.2, 13.7, 9.1]
    ic_r = list(reversed(ic)) 

    ssa_x_lim = (0, 60)

else:
    SITE = "Mountain"

    PIT_HEIGHT = 1750 # in mm
    LAYERS = [125, 91, 78, 59, 14] # in cm

    depth = [148.5, 108, 84.5, 69.5, 36.5, 7]

    #ADDING THE DENSITY VALUES FROM DIFFERENT INSTRUMENTS 
    #Density cutter
    x2 = [262, 230, 305, 332, 275, 309]
    x2_r = list(reversed(x2))

    #Denoth
    x3 = [212, 160, 181, 213, 180, 205]
    x3_r = list(reversed(x3)) 

    x_lim_density = (100, 400)
    depth_temp = [175, 148.5, 108, 84.5, 69.5, 36.5, 7]
    temp = [-1.5, -6.6, -4, -3.1, -2.8, -1.7, -0.3]

    depth_ssa = [175, 172, 125, 91, 78, 59, 14]
    depth_r = list(reversed(depth_ssa))

    midpoints = [148.5, 108, 84.5, 69.5, 36.5, 7]

    #ADDING THE SSA VALUES FROM DIFFERENT INSTRUMENTS 
    #Infrasnow
    xI = [6.9, 13.7, 34.7, 23, 17.9, 20.8, 13.4]
    xI_r = list(reversed(xI))

    xI1 = [23.4, 18.4, 31.1, 24.5, 16, 16.3, 11]
    xI1_r = list(reversed(xI1))

    xI2 = [11.6, 18.6, 33.6, 25.6, 19.1, 23.3, 11]
    xI2_r = list(reversed(xI2))

    #Icecube
    ic = [28.5, 36.3, 33.1, 27.7, 15.2, 12.3, 8.4]
    ic_r = list(reversed(ic)) 

    ssa_x_lim = (0, 70)

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
    ssa_binned /= 0.916

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

fig, ax = plt.subplots(figsize=(10, 6))
line4 = ax.fill_betweenx(height_grid, low_density_95, high_density_95, color='lightgray', alpha=0.5, label='SMP 95% Percentile')
line5 = ax.fill_betweenx(height_grid, low_density_67, high_density_67, color='lightgray', alpha=0.9, label='SMP 67% Percentile')
line6 = ax.plot(mean_density, height_grid, 'C0-', label='SMP Mean density')
ax.set_xlabel('Density [kg/m³]')
ax.set_ylabel('Depth [cm]')

ax2 = ax.twiny() # Create the second X-axis
line3, = ax2.plot(temp, depth_temp, color='red', label='Temperature', marker="x", linewidth=1.5, alpha=0.8)
ax2.set_xlabel('Temperature (°C)', color='black')
ax2.tick_params(axis='x', colors='black')

line7 = ax.hlines(y=[PIT_HEIGHT / 10], xmin=x_lim_density[0], xmax=x_lim_density[1], label="Snowpit surface", color="C1")
line8 = ax.hlines(y=LAYERS, xmin=x_lim_density[0], xmax=x_lim_density[1], label="Top of each layer", color="C1", ls="dotted")
line1 = ax.scatter(x2, depth, label="Density cutter", color="turquoise", marker="o")
line2 = ax.scatter(x3, depth, label="Denoth", color="magenta", marker=".")
ax.set_xlim(*x_lim_density)


lines = [line1, line2, line3, line4, line5, line6[0], line7, line8]

labels = [l.get_label() for l in lines]
ax.legend(lines, labels, loc='lower left', fontsize='small')

ax.set_title(f"Density Profile ({SITE} Site)")
fig.savefig(f"smp_density_{SITE}.png")
#plt.show()



plt.cla()
#############################################################
## SSA PLOT 
#############################################################

lines = []

fig, ax = plt.subplots()

#CREATING SCATTER PLOTS 

line5 = ax.fill_betweenx(height_grid, low_ssa_95, high_ssa_95, color='lightgray', alpha=0.5, label='SMP 95% Percentile')
line6 = ax.fill_betweenx(height_grid, low_ssa_67, high_ssa_67, color='lightgray', alpha=0.9, label='SMP 67% Percentile')
line7 = ax.plot(mean_ssa, height_grid, 'C2-', label='SMP Mean SSA')

line8 = ax.hlines(y=[PIT_HEIGHT / 10], xmin=ssa_x_lim[0], xmax=ssa_x_lim[1], label="Snowpit surface", color="C1")

line9 = ax.hlines(y=LAYERS, xmin=ssa_x_lim[0], xmax=ssa_x_lim[1], label="Top of each layer", color="C1", ls="dotted")

line1= ax.scatter(xI_r, depth_r, color='turquoise', label='Infrasnow 1', marker='P')
line2= ax.scatter(xI1_r, depth_r, color='red', label='Infrasnow 2', marker='P')

if "-25" in DATE: # we missed one measurement there ...
    line3= ax.scatter(xI2_r, depth_r_miss, color='green', label='Infrasnow 3', marker='P')

else:
    line3= ax.scatter(xI2_r, depth_r, color='green', label='Infrasnow 3', marker='P')
line4= ax.scatter(ic_r, depth_r, color='darkviolet', label='Icecube', marker='o')

ax.set_xlabel('SSA [1/mm]')
ax.set_xlim(*ssa_x_lim)
ax.set_ylabel('Depth [cm]')


lines = [line1, line2, line3, line4, line5, line6, line7[0], line8, line9]

labels = [l.get_label() for l in lines]
ax.legend(lines, labels, loc='lower right', fontsize='small')

ax.set_title(f"SSA Profile ({SITE} Site)")
fig.savefig(f"smp_ssa_{SITE}.png")
#plt.show()

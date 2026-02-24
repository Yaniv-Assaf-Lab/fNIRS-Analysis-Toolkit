#!/usr/bin/python
import mne
import numpy as np
import sys
import snirf as sn
import matplotlib.pyplot as plt

# 1. Load the SNIRF file
snirf_file = sys.argv[1]
snirf_data = sn.Snirf(snirf_file)
raw_intensity = mne.io.read_raw_snirf(snirf_file, preload=True)

# 2. Convert Raw Intensity to Optical Density (OD)
# This calculates -log(I / I_baseline)
raw_od = mne.preprocessing.nirs.optical_density(raw_intensity)

# 3. Convert OD to Hemoglobin Concentration (MBLL)
# ppf is the Partial Pathlength Factor (DPF * Partial Volume Correction).
# Standard DPF is roughly 6.0 for adults.
dpf = float(snirf_data.nirs[0].metaDataTags.DPF)
raw_haemo = mne.preprocessing.nirs.beer_lambert_law(raw_od, ppf=dpf)

# --- CRITICAL STEP FOR UNITS ---
# MNE outputs concentration in Molar (M, which is mol/L).
# You requested micromolar (µmol/L).
# 1 M = 1,000,000 µM.

# Access the underlying data array and multiply by 1e6
# raw_haemo._data is (n_channels, n_times)
# raw_haemo.apply_function(lambda x: x * 1e6)

# Verify the unit change in the channel info (optional but good practice)
# for ch in raw_haemo.info['chs']:
#     ch['unit'] = 'µM'

# 4. View/Export Data
# Plot the first few seconds
raw_haemo.plot()

# Extract data as a numpy array for further use
# shape: (channels, timepoints)
data_uM = raw_haemo.get_data()

plt.show()

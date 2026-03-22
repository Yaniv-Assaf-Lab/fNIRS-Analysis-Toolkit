#!/usr/bin/python
import mne
import numpy as np
import sys
import snirf as sn
import matplotlib.pyplot as plt

# Load the SNIRF file
snirf_file = sys.argv[1]
snirf_data = sn.Snirf(snirf_file)
raw_intensity = mne.io.read_raw_snirf(snirf_file, preload=True)

# Convert Raw Intensity to Optical Density (OD)
# This calculates -log(I / I_baseline)
raw_od = mne.preprocessing.nirs.optical_density(raw_intensity)

# Convert OD to Hemoglobin Concentration (MBLL)
# ppf is the Partial Pathlength Factor (DPF * Partial Volume Correction).
# Standard DPF is roughly 6.0 for adults.
dpf = float(snirf_data.nirs[0].metaDataTags.DPF)
raw_haemo = mne.preprocessing.nirs.beer_lambert_law(raw_od, ppf=dpf)


# View/Export Data
raw_haemo.plot()
plt.show()

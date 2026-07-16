import numpy as np
import snirf as sn
import mne
import pandas as pd
import xml.etree.ElementTree as ET
import os
import lib.models as models
import lib.strings as strings

def load_artinis_xml(file_path):
    """Parse Artinis XML export and return dataframe + marker indices."""
    tree = ET.parse(file_path)
    root = tree.getroot()

    # Extract sample rate
    sample_rate = float(root.find("device").find("samplerate").text)

    # Extract column names from <columns>
    column_names = [strings.column_names(i) for i in range(16)]

    # Extract data matrix
    rows = []
    for sdata in root.find("data").findall("sdata"):
        row = [float(gdata.text) for gdata in sdata.findall("gdata")]
        rows.append(row) # Each row is a row of samples taken in the same time.

    df = pd.DataFrame(rows, columns=column_names)

    # Extract event markers (sample indices)
    markers = [int(ev.attrib["s"]) for ev in root.find("events").findall("event")]
    markers = [-1] + markers + [len(df)]  # include start and end
    return df, markers, sample_rate


def load_snirf_file(file_path):
    mne.set_log_level('ERROR')
    result = sn.validateSnirf(file_path)
    assert result, 'Invalid SNIRF file!\n' + result.display()  # Crash and display issues if the file is invalid.

    snirf_data = sn.Snirf(file_path)
    sample_rate = float(snirf_data.nirs[0].metaDataTags.SampleRate)
    dpf = float(snirf_data.nirs[0].metaDataTags.DPF)

    raw_intensity = mne.io.read_raw_snirf(file_path, preload=True)
    raw_od = mne.preprocessing.nirs.optical_density(raw_intensity)
    sci = np.min(mne.preprocessing.nirs.scalp_coupling_index(raw_od) )
    if(sci < 0.5):
        subject_id = strings.subject_id_from_filename(file_path)
        trial_num = strings.trial_num_from_filename(file_path)
        print(f"Warning: Low SCI for subject {subject_id}, trial {trial_num} ({(sci*100):.01f}%)")
    raw_haemo = mne.preprocessing.nirs.beer_lambert_law(raw_od, ppf=dpf) # ppf = 4.49 + 0.067 * age ** 0.814
    data_micromolar = raw_haemo.get_data() * 1e6
    column_names = [strings.column_names(i) for i in range(16)]
    events = []
    for array in snirf_data.nirs[0].stim:
        events.extend(map(lambda x: int(x*sample_rate), array.data[:, 0]))

    events.extend([data_micromolar.shape[1], -1])
    events.sort()
    for i in range(0, 16):
        source = snirf_data.nirs[0].data[0].measurementList[i].sourceIndex
        detector = snirf_data.nirs[0].data[0].measurementList[i].detectorIndex
        if(source >= 2):
            source += 1
    df = pd.DataFrame(data_micromolar, index=column_names).transpose()
    snirf_data.close()
    return df, events, sample_rate


def load_file(file_path, tddr = False):
    trial_data = models.fNIRSTrial()
    _, extension = os.path.splitext(file_path)
    extension.lower()
    if(extension == ".snirf"):   
        df, event_indices, sample_rate = load_snirf_file(file_path)
    elif(extension == ".xml"):     
        df, event_indices, sample_rate = load_artinis_xml(file_path)
    else:
        # Let error handling happen outside
        trial_data.trial_num = -1 
        return trial_data 

    # Remove motion noise if flagged
    mne.set_log_level('WARNING')
    column_names = [strings.column_names(i) for i in range(16)]
    types = [('hbr' if i % 2 else 'hbo') for i in range (len(column_names))]
    info = mne.create_info(column_names, sample_rate, types)
    raw_df = mne.io.RawArray(df.to_numpy().transpose(), info)
    if(tddr):
        repaired = mne.preprocessing.nirs.temporal_derivative_distribution_repair(raw_df)
    else:
        repaired = raw_df
    df = pd.DataFrame(repaired[:][0].transpose())

    trial_data.data = df
    trial_data.sample_rate = sample_rate
    trial_data.event_indices = event_indices

    return trial_data
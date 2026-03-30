import pandas as pd
import snirf as sn
import mne
import pandas as pd
import xml.etree.ElementTree as ET
import os

def load_artinis_xml(file_path):
    """Parse Artinis XML export and return dataframe + marker indices."""
    tree = ET.parse(file_path)
    root = tree.getroot()

    # Extract sample rate
    sample_rate = float(root.find("device").find("samplerate").text)

    # Extract column names from <columns>
    column_names = []
    for col in root.findall(".//columns/column"):
        column_names.append(col.text.strip())

    # Extract data matrix
    rows = []
    for sdata in root.find("data").findall("sdata"):
        row = [float(gdata.text) for gdata in sdata.findall("gdata")]
        rows.append(row) # Each row is a row of samples taken in the same time.

    df = pd.DataFrame(rows, columns=column_names)

    # Extract event markers (sample indices)
    markers = [int(ev.attrib["s"]) for ev in root.find("events").findall("event")]
    markers = [-1] + markers + [len(df)]  # include start and end
    return df, markers, column_names, sample_rate


def load_snirf_file(file_path):
    mne.set_log_level('ERROR')
    result = sn.validateSnirf(file_path)
    assert result, 'Invalid SNIRF file!\n' + result.display()  # Crash and display issues if the file is invalid.

    snirf_data = sn.Snirf(file_path)
    sample_rate = float(snirf_data.nirs[0].metaDataTags.SampleRate)
    dpf = float(snirf_data.nirs[0].metaDataTags.DPF)

    raw_intensity = mne.io.read_raw_snirf(file_path, preload=True)
    raw_od = mne.preprocessing.nirs.optical_density(raw_intensity)
    sci = mne.preprocessing.nirs.scalp_coupling_index(raw_od)
    if(sci < 0.5):
        print(f"Warning: Low scalp coupling index ({sci*100}%)")
    raw_haemo = mne.preprocessing.nirs.beer_lambert_law(raw_od, ppf=dpf) # ppf = 4.49 + 0.067 * age ** 0.814
    data_micromolar = raw_haemo.get_data() * 1e6
    column_names = []
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
        column_names.append(f"Rx{detector} - Tx{source}")
    df = pd.DataFrame(data_micromolar, index=column_names).transpose()
    snirf_data.close()
    return df, events, column_names, sample_rate


def load_file(file_path):
    _, extension = os.path.splitext(file_path)
    extension.lower()
    if(extension == ".snirf"):   
        df, marker_indices, column_names, sample_rate = load_snirf_file(file_path)
        
    elif(extension == ".xml"):     
        df, marker_indices, column_names, sample_rate = load_artinis_xml(file_path)
    else:
        df, marker_indices, column_names, sample_rate = (0,0,0,0)

    # Standardize channel names: Sx_Dx {hbr/hbo}, Where S is for Source and D is for Detector
    column_names = [f'S{column[2]}_D{column[8]}' for column in column_names][::2]
    types = [('hbr' if i % 2 else 'hbo') for i in range (len(column_names * 2))]
    column_names = [f"{cn} {channel}" for cn in column_names for channel in ['hbo', 'hbr']]

    # Remove motion noise
    info = mne.create_info(column_names, sample_rate, types)
    raw_df = mne.io.RawArray(df.to_numpy().transpose(), info)
    repaired = mne.preprocessing.nirs.temporal_derivative_distribution_repair(raw_df)
    df = pd.DataFrame(repaired[:][0].transpose())

    return df, marker_indices, column_names, sample_rate
from pathlib import Path

def column_names(ch, num_channels = 16):
    tx = [1, 2, 3, 4]
    rx = [1, 3, 4, 5]
    types = ["hbo", "hbr"]
    if (num_channels == 16):
        types_idx = ch % 2
        rx_idx = 2 * (ch // 8) + (ch // 2) % 2
        tx_idx = ch // 4
        return f"S{tx[tx_idx]}_D{rx[rx_idx]} {types[types_idx]}"
    if (num_channels == 8):
        rx_idx = 2 * (ch // 4) + ch % 2
        tx_idx = ch // 2
        return f"S{tx[tx_idx]}_D{rx[rx_idx]} diff"


def subject_id_from_filename(file_name):
    return Path(file_name).stem.split(" ")[0]

def trial_num_from_filename(file_name):
    split_name = Path(file_name).stem.split(" ")
    if(len(split_name) == 1):
        return 1
    else:
        return split_name[1]
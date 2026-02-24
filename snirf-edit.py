#!/usr/bin/python
import os
import sys
from snirf import Snirf
import numpy as np


def load_snirf(path):
    print(f"Loading: {path}")
    snirf = Snirf(path, 'r')

    # Required method
    sample_rate = float(snirf.nirs[0].metaDataTags.SampleRate)

    # Extract events with direct indexing
    # events list contains tuples: (stim_id, row_id, sample_index)
    events = []
    for stim_id, stim in enumerate(snirf.nirs[0].stim):
        onsets = stim.data[:, 0]
        for row_id, onset_time in enumerate(onsets):
            sample_idx = int(onset_time * sample_rate)
            events.append((stim_id, row_id, sample_idx))

    # Sort events by sample index
    events.sort(key=lambda x: x[2])

    # Create working copy and close the original file
    snirf2 = snirf.copy()
    snirf.close()

    return snirf2, events, sample_rate


def list_events(events, sample_rate):
    if not events:
        print("No events found.")
        return

    print("\n=== EVENTS ===")
    prev_time = None

    for i, (_, _, sample_idx) in enumerate(events):
        t = sample_idx / sample_rate
        delta = "—" if prev_time is None else f"{t - prev_time:.4f} s"
        print(f"[{i}] sample={sample_idx:8d}  time={t:9.4f} s   Δt={delta}")
        prev_time = t

    print()


def remove_event(snirf2, events, index):
    """Remove an event using direct stim/block indexing (no float matching)."""

    if index < 0 or index >= len(events):
        print("Invalid index")
        return

    stim_id, row_id, sample_idx = events[index]

    stim = snirf2.nirs[0].stim[stim_id]

    # Delete that specific row
    stim.data = np.delete(stim.data, row_id, axis=0)

    # Remove event from list
    events.pop(index)

    # Fix row indexes for remaining events from the same stim block
    for i, (s, r, samp) in enumerate(events):
        if s == stim_id and r > row_id:
            events[i] = (s, r - 1, samp)

    print(f"Removed event: stim={stim_id}, row={row_id}, sample={sample_idx}")


def main():
    path = sys.argv[1]
    if not os.path.exists(path):
        print("File not found.")
        return

    snirf2, events, sample_rate = load_snirf(path)
    print("\nSNIRF loaded (copy created). Original file will not be modified.\n")

    while True:
        print("""
=== MENU ===
1. List events
2. Remove event
3. Save modified SNIRF as new file
4. Quit (without saving)
""")
        choice = input("Select: ").strip()

        if choice == "1":
            list_events(events, sample_rate)

        elif choice == "2":
            list_events(events, sample_rate)
            idx = input("Enter event index to remove: ").strip()
            if idx.isdigit():
                remove_event(snirf2, events, int(idx))
            else:
                print("Invalid input")

        elif choice == "3":
            save_path = input("Save as: ").strip()
            snirf2.save(save_path)
            print(f"Saved to {save_path}")

        elif choice == "4":
            print("Exiting without saving.")
            break

        else:
            print("Invalid option.")


if __name__ == "__main__":
    main()

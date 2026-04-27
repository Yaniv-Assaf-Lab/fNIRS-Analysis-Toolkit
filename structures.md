# Structures

This document outlines the data structures used in this project, so there will be no need to guess what goes where.

## Analysis:

```
fNIRS_Data{
    trials[
        trial{
            subject_id
            subject
            index
            stacks              # Fully processed, 8/16 channel data
            separate_stacks     # Only filtered, 16 channels
            offset              # If no template is found - Default to 0
        },
        ...
    ]

    analysis{
        transform
        factor
        filters
        phase_locked
    }

    column_names ["Sx_Dx hbx", ...]
}

```
## Template: 
```
Data{
    stacks              # Fully processed, 8/16 channel data
    separate_stacks     # Only filtered, 16 channels

    analysis{
        transform
        factor
        filters
    }

    column_names ["Sx_Dx hbx", ...]
}
```
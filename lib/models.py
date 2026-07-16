from enum import Enum
from dataclasses import dataclass, field
from typing import List, Any
import pandas as pd



class Belt(Enum):
    unkn = 0
    whte = 1
    blue = 2
    prpl = 3
    brwn = 4
    blck = 5

class Gender(Enum):
    m = 0
    f = 1

class Handedness(Enum):
    u = 0
    r = 1
    l = 2

@dataclass
class fNIRSTrial():
    # Trial data
    data: pd.DataFrame = field(default_factory=pd.DataFrame) 
    analysis_hash = 0
    trial_num: int = 0 # 0 is unlabeled, -1 is invalid, any other positive integer is a valid trial number
    sample_rate: int = 0
    event_indices: list[int] = field(default_factory=list)

    # Subject data
    subject_id: str = ""
    subject_age: int = 0
    subject_train_time: int = 0
    subject_belt: Belt = Belt.unkn
    subject_gender: Gender = Gender.m
    subject_handedness: Handedness = Handedness.u

    def hydrate_subject_data(self, row: pd.Series):
        """
        An instance method that reaches into a Pandas row
        and updates the attributes of this object.
        """
        def get_enum(enum_class: type[Enum], value: Any):
            try:
                if isinstance(value, str):
                    return enum_class[value.lower()]
                return enum_class(int(value))
            except (KeyError, ValueError):
                return Belt.unkn if enum_class is Belt else list(enum_class)[0]

        # We update 'self' directly
        self.subject_id = str(row['subject_id'].iloc[0])
        self.subject_age = int(row['age'].iloc[0])
        self.subject_train_time = int(row['train_time'].iloc[0])
        self.subject_belt = get_enum(Belt, row['belt'].iloc[0])
        self.subject_gender = get_enum(Gender, row['gender'].iloc[0])
        self.subject_handedness = get_enum(Handedness, row['handedness'].iloc[0])
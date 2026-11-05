from dataclasses import dataclass, field
from pathlib import Path

@dataclass
class CohortConfig:
    api_url: str = "https://api.vitaldb.net"
    required_tracks: list[str] = field(
        default_factory=lambda: ["SNUADC/ART", "Solar8000/ART_MBP"]
    )
    min_age: int = 18
    min_duration_min: int = 60
    output_path: Path = Path("data/cohort.csv")

@dataclass
class FeatureConfig:
    static_numeric: list[str] = field(default_factory=lambda: [
        "age", "weight", "bmi", "asa",
        "preop_hb", "preop_alb", "preop_cr", "preop_na",
    ])
    static_binary: list[str] = field(default_factory=lambda: [
        "emop", "preop_htn", "preop_dm",
    ])
    static_categorical: list[str] = field(default_factory=lambda: [
        "sex", "department", "optype", "approach", "position",
    ])
    # Jamais comme features : totaux de fin de chirurgie ou devenir (fuite de données)
    forbidden: list[str] = field(default_factory=lambda: [
        "intraop_ebl", "intraop_uo", "intraop_rbc", "intraop_ffp",
        "intraop_crystalloid", "intraop_colloid", "intraop_ppf", "intraop_mdz",
        "intraop_ftn", "intraop_rocu", "intraop_vecu", "intraop_eph",
        "intraop_phe", "intraop_epi", "intraop_ca",
        "icu_days", "death_inhosp", "dis",
    ])

@dataclass
class DownloadConfig:
    cohort_path : Path = Path("data/cohort.csv")
    output_numerics_path : Path = Path("data/numerics")
    required_track_1Hz: list[str] = field(
        default_factory=lambda: ["Solar8000/ART_MBP", "Solar8000/ART_SBP", "Solar8000/ART_DBP", "Solar8000/NIBP_MBP", "Solar8000/HR",
        "Solar8000/PLETH_SPO2", "Solar8000/ETCO2", "Solar8000/BT" , "BIS/BIS" , "Primus/MAC", "Primus/PEEP_MBAR", 
        "Primus/TV" , "Orchestra/PPF20_CE", "Orchestra/RFTN20_CE", "Orchestra/PHEN_RATE", "Orchestra/NEPI_RATE"]
    )
    required_track_100Hz: list[str] = field(
        default_factory=lambda:  ["SNUADC/ART", "SNUADC/ECG_II", "SNUADC/PLETH"]
    )
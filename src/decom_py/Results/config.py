STD_DIM_NAMES = {
    "group": "Group",
    "env_group": "Group",
    "time": "Time",
    "scenario": "Scenario",
    "fleet": "Fleet",
    "prey": "Prey",
    "predator": "Predator"
}

CATEGORY_CONFIG = {
    "ECOSYSTEM_STATS": {
        "dims": [STD_DIM_NAMES[s] for s in ["scenario", "time"]]
    },
    "GROUP_STATS": {
        "dims": [STD_DIM_NAMES[s] for s in ["scenario", "group", "time"]]
    },
    "FISHING_STATS": {
        "dims": [STD_DIM_NAMES[s] for s in ["scenario", "fleet", "group", "time"]]
    }
}

VARIABLE_CONFIG = {
    "Concentration": {
        "variable_name": "Concentration",
        "dims": ["scenario", "env_group", "time"],
        "category": "GROUP_STATS",
        "unit": "t/t",
        "extractor_name": "create_conc_extractor",
        "extractor_input": "", # only for packed variables
        "save_filename": "Concentration"
    },
    "Concentration Biomass": {
        "variable_name": "Concentration_Biomass",
        "dims": ["scenario", "env_group", "time"],
        "category": "GROUP_STATS",
        "unit": "unknown",
        "extractor_name": "create_conc_biomass_extractor",
        "extractor_input": "",
        "save_filename": "Concentration_Biomass"
    },
}

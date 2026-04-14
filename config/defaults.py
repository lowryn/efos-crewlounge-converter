AC_TYPE_MAP = {
    "737 800": {"model": "B737", "variant": "800", "make": "Boeing", "rating": "B737-6/7/8/900", "engtype": "Turbofan"},
}

DEFAULT_CONFIG = {
    "self_name_preference": "SELF",
    "operator": "Jet2",
    "output_format": "csv",          # "csv" or "xlsx"
    "last_efos_directory": "",
    "last_globalog_directory": "",
    "last_output_directory": "",
    "ac_type_mapping": AC_TYPE_MAP,
}

# CrewLounge PIW output columns in order (semicolon-delimited)
OUTPUT_COLUMNS = [
    "PILOTLOG_DATE", "IS_PREVEXP", "AC_ISSIM", "FLIGHTNUMBER", "PAIRING",
    "AF_DEP", "DEP_RWY", "AF_ARR", "ARR_RWY",
    "TIME_DEP", "TIME_DEPSCH", "TIME_ARR", "TIME_ARRSCH",
    "TIME_TO", "TIME_LDG", "TIME_AIR", "TIME_MODE", "TIME_TOTAL", "TIME_TOTALSIM",
    "TIME_PIC", "TIME_SIC", "TIME_DUAL", "TIME_PICUS", "TIME_INSTRUCTOR",
    "TIME_EXAMINER", "TIME_NIGHT", "TIME_XC", "TIME_IFR", "TIME_HOOD",
    "TIME_ACTUAL", "TIME_RELIEF", "TIME_USER1", "TIME_USER2", "TIME_USER3", "TIME_USER4",
    "CAPACITY", "OPERATOR",
    "PILOT1_ID", "PILOT1_NAME", "PILOT1_PHONE", "PILOT1_EMAIL",
    "PILOT2_ID", "PILOT2_NAME", "PILOT2_PHONE", "PILOT2_EMAIL",
    "PILOT3_ID", "PILOT3_NAME", "PILOT3_PHONE", "PILOT3_EMAIL",
    "PILOT4_ID", "PILOT4_NAME", "PILOT4_PHONE", "PILOT4_EMAIL",
    "TO_DAY", "TO_NIGHT", "LDG_DAY", "LDG_NIGHT", "LIFT", "PF",
    "HOLDING", "TAG_APP", "TAG_OPS", "TAG_LAUNCH",
    "INSTRUCTION/TRAINING", "REMARKS", "CREWLIST", "FLIGHTLOG",
    "PAX", "FUEL", "FUELPLANNED", "FUELUSED", "TAG_DELAY", "DEICE",
    "USER_NUMERIC", "USER_TEXT", "USER_YESNO",
    "AC_MAKE", "AC_MODEL", "AC_VARIANT", "AC_REG", "AC_FIN", "AC_RATING",
    "AC_SP", "AC_MP", "AC_ME", "AC_SPSE", "AC_SPME", "AC_CLASS",
    "AC_GLIDER", "AC_ULTRALIGHT", "AC_SEA", "AC_ENGINES", "AC_ENGTYPE",
    "AC_TAILWHEEL", "AC_COMPLEX", "AC_TMG", "AC_HEAVY", "AC_HIGHPERF",
    "AC_AEROBATIC", "AC_SEATS",
]

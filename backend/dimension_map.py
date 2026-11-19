
DIMENSION_MAP = {

    "month": {
        "synonyms": ["month", "monthly", "month wise"],
        "reference": "'Calender'[Month]",
        "display_name": "Month",
        "filterable": True,
        "groupable": True
    },

    "year": {
        "synonyms": ["year", "yearly"],
        "reference": "'Calender'[Year]",
        "display_name": "Year",
        "filterable": True,
        "groupable": True
    },

    "date": {
        "synonyms": ["date", "daily", "day wise"],
        "reference": "'Calender'[Date]",
        "display_name": "Date",
        "filterable": True,
        "groupable": True
    },

    "district": {
        "synonyms": ["district", "district wise"],
        "reference": "'Districts & Regions'[District]",
        "display_name": "District",
        "filterable": True,
        "groupable": True
    },

    "region": {
        "synonyms": ["region", "region wise"],
        "reference": "'Districts & Regions'[Region]",
        "display_name": "Region",
        "filterable": True,
        "groupable": True
    },

    "vehicle": {
        "synonyms": ["vehicle", "vehicle wise"],
        "reference": "'Vehicles Master Database'[Vehicle Number]",
        "display_name": "Vehicle",
        "filterable": True,
        "groupable": True
    },

    "base_location": {
        "synonyms": [
            "base",
            "base location",
            "base location wise"
        ],
        "reference": "'Segments'[Base Location]",
        "display_name": "Base Location",
        "filterable": True,
        "groupable": True
    }
}

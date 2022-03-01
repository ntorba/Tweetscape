from pathlib import Path

with open(Path().cwd() / "scientist_fields.txt") as f:
    SCIENTIST_CATEGORIES = [i.strip("\n") for i in f.readlines()]

with open(Path().cwd() / "languages.txt") as f:
    LANGUAGES = [i.strip("\n") for i in f.readlines()]

with open(Path().cwd() / "racial_background.txt") as f:
    BACKGROUNDS = [i.strip("\n") for i in f.readlines()]

with open(Path().cwd() / "match_groups.txt") as f:
    DO_NOT_MATCH_GROUPS = [i.strip("\n") for i in f.readlines()]

with open(Path().cwd() / "discovery_mediums.txt") as f:
    DISCOVERY_MEDIUMS = [i.strip("\n") for i in f.readlines()]

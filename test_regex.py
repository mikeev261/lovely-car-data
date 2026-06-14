import re
print(re.sub(r'\s*//.*$', '', '"4": { "redline": 7740, "step": 130 }, //X\n"5": {}', flags=re.MULTILINE))

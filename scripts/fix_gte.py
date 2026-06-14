import glob
import os

files = glob.glob(r'C:\Code\lovely-car-data-mgmt\lovely_data_to_simhub\lovely-car-data\src_data\lmu\gte-*.jsonc')

replacements = {
    '"AF Corse GTE"': '"GTE_AF Corse"',
    '"JMW Motorsport"': '"GTE_JMW Motorsport"',
    '"Kessel Racing"': '"GTE_Kessel Racing"',
    '"Walkenhorst Motorsport"': '"GTE_Walkenhorst Motorsport"',
    
    '"Dempsey-Proton Racing"': '"GTE_Dempsey-Proton Racing"',
    '"GR Racing"': '"GTE_GR Racing"',
    '"Iron Dames"': '"GTE_Iron Dames"',
    '"Iron Lynx"': '"GTE_Iron Lynx"',
    '"Project 1 - AO"': '"GTE_Project 1 - AO"',
    '"Proton Competition GTE"': '"GTE_Proton Competition"',
    
    '"D\'station Racing"': '"GTE_D\'station Racing"',
    '"GMB Motorsport"': '"GTE_GMB Motorsport"',
    '"Northwest AMR"': '"GTE_Northwest AMR"',
    '"ORT by TF"': '"GTE_ORT by TF"',
    '"TF Sport"': '"GTE_TF Sport"',
    '"The Heart of Racing"': '"GTE_The Heart of Racing"',
    
    '"Corvette Racing"': '"GTE_Corvette Racing"',
}

for f in files:
    with open(f, 'r', encoding='utf-8') as file:
        content = file.read()
    
    for old, new in replacements.items():
        content = content.replace(old, new)
        
    with open(f, 'w', encoding='utf-8') as file:
        file.write(content)

print("Done fixing GTE ids!")

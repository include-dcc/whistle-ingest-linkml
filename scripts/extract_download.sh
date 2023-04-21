
# This assumes we have valid links for each of the tables inside data that point
# to wherever we extracted those tables
scripts/split_dataset.py

# Build a harmony file containing contents of the Data Dictionary and terms 
# found inside the cohort condition file.

scripts/build_harmony_file.py -c data/tables/ABC-DS/condition.csv data/dd/condition.csv data/dd/participant.csv data/dd/specimen.csv data/dd/datafile.csv
mv harmony/data-harmony.csv harmony/abcds

scripts/build_harmony_file.py -c data/tables/BRI-DSR/condition.csv data/dd/condition.csv data/dd/participant.csv data/dd/specimen.csv data/dd/datafile.csv
mv harmony/data-harmony.csv harmony/bri-dsr

scripts/build_harmony_file.py -c data/tables/DSC/condition.csv data/dd/condition.csv data/dd/participant.csv data/dd/specimen.csv data/dd/datafile.csv
mv harmony/data-harmony.csv harmony/dsc

scripts/build_harmony_file.py -c data/tables/DS-Sleep/condition.csv data/dd/condition.csv data/dd/participant.csv data/dd/specimen.csv data/dd/datafile.csv
mv harmony/data-harmony.csv harmony/ds-sleep

scripts/build_harmony_file.py -c data/tables/DS-Sleep/condition.csv data/dd/condition.csv data/dd/participant.csv data/dd/specimen.csv data/dd/datafile.csv
mv harmony/data-harmony.csv harmony/ds-sleep

scripts/build_harmony_file.py -c data/tables/HTP/condition.csv data/dd/condition.csv data/dd/participant.csv data/dd/specimen.csv data/dd/datafile.csv
mv harmony/data-harmony.csv harmony/htp

scripts/build_harmony_file.py -c data/tables/X01-deSmith/condition.csv data/dd/condition.csv data/dd/participant.csv data/dd/specimen.csv data/dd/datafile.csv
mv harmony/data-harmony.csv harmony/x01-desmith

scripts/build_harmony_file.py -c data/tables/X01-Hakon/condition.csv data/dd/condition.csv data/dd/participant.csv data/dd/specimen.csv data/dd/datafile.csv
mv harmony/data-harmony.csv harmony/x01-hakon

python scripts/extract_encounters.py abcds.yaml  
python scripts/extract_family_details.py abcds.yaml  

python scripts/extract_encounters.py bri-dsr.yaml  
python scripts/extract_family_details.py bri-dsr.yaml  

python scripts/extract_encounters.py dsc.yaml  
python scripts/extract_family_details.py dsc.yaml  

python scripts/extract_encounters.py dssleep.yaml  
python scripts/extract_family_details.py dssleep.yaml  

python scripts/extract_encounters.py htp.yaml  
python scripts/extract_family_details.py htp.yaml  

python scripts/extract_encounters.py x01-desmith.yaml  
python scripts/extract_family_details.py x01-desmith.yaml  

python scripts/extract_encounters.py x01-hakon.yaml
python scripts/extract_family_details.py x01-hakon.yaml


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


import os
import datetime
import time

root_dir = "D:\\Projects-D\\pepsi-final3\\rag_new"
twelve_hours_ago = datetime.datetime.now() - datetime.timedelta(hours=12)
cutoff_timestamp = int(twelve_hours_ago.timestamp())

modified_files = []
for dirpath, dirnames, filenames in os.walk(root_dir):
    for filename in filenames:
        full_path = os.path.join(dirpath, filename)
        try:
            mod_timestamp = int(os.path.getmtime(full_path))
            if mod_timestamp >= cutoff_timestamp:
                modified_files.append(full_path)
        except Exception:
            pass

for f in modified_files:
    print(f)

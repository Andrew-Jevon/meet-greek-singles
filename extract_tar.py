"""Extract a tar file to a target dir. Called once per chunk."""
import sys, tarfile, os

tar_path = sys.argv[1]
target   = sys.argv[2]
os.makedirs(target, exist_ok=True)
with tarfile.open(tar_path) as t:
    members = t.getmembers()
    t.extractall(target)
print(f"OK {len(members)} members -> {target}")

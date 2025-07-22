print("Testing Python execution...")
import os
print(f"Current directory: {os.getcwd()}")
print("Files in directory:")
for f in os.listdir("."):
    print(f"  {f}")

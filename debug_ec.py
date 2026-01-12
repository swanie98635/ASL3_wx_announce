import env_canada
print("Contents of env_canada:")
print(dir(env_canada))
try:
    from env_canada import ECData
    print("ECData found!")
except ImportError:
    print("ECData NOT found.")

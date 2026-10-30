try:
    open("/w/x.txt", "w")
except OSError as e:
    print("mount write denied:", e)
else:
    raise SystemExit("MOUNT WRITABLE")
try:
    open("/etc/x.txt", "w")
except OSError as e:
    print("root fs write denied:", e)
else:
    raise SystemExit("ROOT FS WRITABLE")

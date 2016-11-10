import bluetooth

btdev = bluetooth.discover_devices(duration=5, lookup_names=True)

print "Available devices:"

for dev in btdev:
    print dev

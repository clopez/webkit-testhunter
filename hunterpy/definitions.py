NOERROR="NOERROR"
UNKNOWN="UNKNOWN"

bots = { # The reason to have more than one entry per bot is that some bots where renamed along the history.
    'gtk-release' : ["GTK-Linux-64-bit-Release", "GTK-Linux-64-bit-Release-WK2-Tests", "GTK-Linux-64-bit-Release-Tests"],
    'gtk-debug' : ["GTK-Linux-64-bit-Debug-Tests"],
    'gtk-release-wayland' : ["GTK-Linux-64-bit-Release-Wayland-Tests"],
    'gtk-release-gtk4' : ["GTK-Linux-64-bit-Release-GTK4-Tests"],
    'gtk-release-skip-failing': ["GTK-Linux-64-bit-Release-Skip-Failing-Tests"],
    'wpe-release' : ["WPE-Linux-64-bit-Release-Tests"],
    'wpe-debug' : ["WPE-Linux-64-bit-Debug-Tests"]
}

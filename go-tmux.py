#!/usr/bin/env python3

# more fiddling with libtmux 
# https://libtmux.git-pull.com/index.html
# davep 20240415

import sys
import libtmux

#session_name = "foo"

location = sys.argv[1]
window_name = None
if len(sys.argv) >= 3:
        window_name = sys.argv[2]

server = libtmux.Server()

# previously created with "tmux new-session -t foo"
#session = server.find_where({"session_name":"foo"})

session = server.sessions[0]

if window_name:
    window = session.new_window(window_name=window_name)
else:
    window = session.new_window()

# make 4 panes by splitting 3x
window.split_window()
window.split_window()
window.split_window()

window.select_layout(layout="tiled")

for p in window.panes:
    p.send_keys(f"cd {location}")



import sys
import io
import base64

# decode a base64 encoded file
# cat file.b64 | python3 b64.py > file
while True:
    line = sys.stdin.readline()
    if not line or not len(line):
        break
    buf = base64.b64decode(line.strip(), validate=True)
    # https://docs.python.org/3/library/sys.html#sys.stdout
    sys.stdout.buffer.write(buf)

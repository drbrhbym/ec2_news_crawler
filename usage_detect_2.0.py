import os
from aws_linenotify import lineNotify

if os.path.exists("usage_output.txt"):
    with open("usage_output.txt", "r", encoding="utf-8") as f:
        output = f.read().split(" ")[8]
        #print(output)
        lineNotify("Disk usage " + output + " used!")






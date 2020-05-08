#detect the crop in the first 2 minutes
ffmpeg -ss 0 -i $1 -t 120  -vf fps=2,cropdetect -f null - 2>&1|awk '/crop/ { print $NF }'

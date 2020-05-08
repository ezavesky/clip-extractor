import sys

if __name__ == '__main__':

    threshold = float(sys.argv[1])
    is_header = True
    for line in sys.stdin:
        line = line.strip()
        if is_header:
            is_header = False
            print(line)
            continue
        fields = line.split('|')
        frame_width = int(fields[-4])
        frame_height = int(fields[-3])
        cropped_frame_width = int(fields[-2])
        cropped_frame_height = int(fields[-1])

        width_diff = abs(frame_width - cropped_frame_width)
        height_diff = abs(frame_height - cropped_frame_height)
        if ( width_diff > threshold ) or (height_diff > threshold ):
            print(line.strip())

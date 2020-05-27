import sys

def filter_crop_dims(list_cropped, threshold, return_list=True):
    is_header = True
    list_results = []
    for line in list_cropped:
        line = line.strip()
        if is_header:
            is_header = False
            if return_list:
                list_results.append(line)
            else:
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
            if return_list:
                list_results.append(line.strip())
            else:
                print(line.strip())
    return list_results


if __name__ == '__main__':
    filter_crop_dims(sys.stdin, float(sys.argv[1]), False)

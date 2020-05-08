import sys

def get_frame_height_width(crop_str):
    _, crop_info  = crop_str.split('=')
    width, height, x, y = crop_info.split(':')
    return int(width), int(height), int(x), int(y)

is_header = True
for line in sys.stdin:
    line = line.strip()
    if is_header:
        is_header = False
        print(line)
        continue
    fields = line.strip().split('|')
    video_width = int(fields[-4])
    video_height = int(fields[-3])
    ratio = float(video_width)/video_height
    #Here we assume that width is greater than height (16:9). cut left and right border
    width, height, x, y = get_frame_height_width(fields[1])
    new_width = int(height * ratio)
    new_x = (video_width - new_width) // 2
    crop_str = 'crop={}:{}:{}:{}'.format(new_width, height, new_x, y)
    print('{}|{}|{}|{}|{}|{}'.format(fields[0], crop_str, video_width, video_height, new_width, height))

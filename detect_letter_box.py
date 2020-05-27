import sys
import os
import subprocess
import json
import numpy as np


def get_video_width_and_height(video_file):
    cmd="ffprobe -v quiet -select_streams v:0  -print_format json -show_format -show_streams {}".format(video_file)
    result = subprocess.check_output(cmd, shell=True)
    rec = json.loads(result)
    width = rec["streams"][0]["width"]
    height= rec["streams"][0]["height"]
    return width, height


def get_new_frame_height_width(crop_str):
    _, crop_info  = crop_str.split('=')
    width, height, x, y = crop_info.split(':')
    return int(width), int(height), int(x), int(y)


def estimate_cropped_height_and_width(ffmpeg_crop_msgs):
    width = []
    height =[]
    x = []
    y = []
    if type(ffmpeg_crop_msgs) != list:
        ffmpeg_crop_msgs = ffmpeg_crop_msgs.split("\n")
    for line in ffmpeg_crop_msgs:
        crop_str = line.strip()
        if crop_str == '':
            continue

        width_, height_, x_, y_ = get_new_frame_height_width(crop_str)
        width.append(width_)
        height.append(height_)
        x.append(x_)
        y.append(y_)

    if len(x) == 0:
        return 0, 0, 0, 0

    width = np.array(width, dtype='int32')
    height = np.array(height, dtype='int32')
    x = np.array(x, dtype='int32')
    y = np.array(y, dtype='int32')
    
    cropped_width = int(np.median(width))
    cropped_height = int(np.median(height))
    cropped_x = int(np.median(x))
    cropped_y = int(np.median(y))

    return cropped_width, cropped_height, cropped_x, cropped_y 


def sample_letter_box(path_source):
    #detect the crop in the first 2 minutes
    cmd_list = ["ffmpeg", "-ss", "0", "-i", path_source, "-t", "120", "-vf", "fps=2,cropdetect", "-f", "null", "-"]

    # res = subprocess.check_output(" ".join(cmd_list), shell=True, universal_newlines=True)
    # modified for subprocess - https://stackoverflow.com/a/16516701 (5/27)
    proc = subprocess.Popen(cmd_list, shell=False, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    list_results = []

    # Read line from stdout, break if EOF reached, append line to output
    for line in proc.stdout:
        line = line.decode().strip()
        if "crop" in line:
            line_parts = line.split(" ")
            list_results.append(line_parts[-1])
    return list_results


def detect_letter_box(list_sources, path_result=None):
    """list of sources, list of results (or output path); future may change this to dataframe?"""
    list_result = []
    str_header = "video_name|crop_info|video_width|video_height|cropped_frame_width|cropped_frame_height\n"
    if path_result is not None:
        o_f = open(path_result, 'wt')
        o_f.write(str_header)
    else:
        list_result.append(str_header)

    for line in list_sources:
        video_file = line.strip()
        sys.stderr.write('{}\n'.format(video_file))

        video_width, video_height = get_video_width_and_height(video_file)
        # cmd = "sh cropdetect.sh {}".format(video_file)
        # result = subprocess.check_output(cmd, shell=True, universal_newlines=True)
        result = sample_letter_box(video_file)
        new_frame_width, new_frame_height, x, y = estimate_cropped_height_and_width(result)
        if new_frame_width == 0:
            continue
        
        crop_str = 'crop={}:{}:{}:{}'.format(new_frame_width, new_frame_height, x, y)
        str_result = '{video_file}|{crop_str}|{video_width}|{video_height}|{new_frame_width}|{new_frame_height}\n'.format(**locals())
        if path_result is not None:
            o_f.write(str_result)
            o_f.flush()
        else:
            list_result.append(str_result)

    if path_result is None:
        return list_result
    o_f.close()


if __name__ == '__main__':
    detect_letter_box(sys.stdin, sys.argv[1])


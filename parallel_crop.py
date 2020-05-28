from multiprocessing import Pool
import sys
import os
import argparse

def ffmpeg_crop(crop_info):
    src_video = crop_info[0]
    ffmpeg_crop_str = crop_info[1]
    output_dir = crop_info[2]
    dst_file  = os.path.join(output_dir, os.path.basename(src_video))
    cmd="ffmpeg -i {} -vf {} {}".format(src_video, ffmpeg_crop_str, dst_file )
    retcode = os.system(cmd)
    if retcode != 0:
        return "{}\tFailure".format(src_video)
    else:
        return "{}\tSuccess".format(src_video)


def load_video_cropped_list(list_crop):
    """load cropping from a list or list-like iterator (e.g. an open file)"""
    video_cropped_info=[]
    is_header = True
    for line in list_crop:
        #skip the header
        if is_header:
            is_header = False
            continue
        fields = line.strip().split('|')
        video_cropped_info.append((fields[0], fields[1]))
    return video_cropped_info


def load_video_cropped_info(filename):
    video_cropped_info=[]
    with open(filename, 'rt') as f:
        return load_video_cropped_list(f)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="run crop in multi processes")
    parser.add_argument('-i', action="store", help="video cropped file", required=True)
    parser.add_argument('-n', help="number of parallel processes", type=int, required=True)    
    parser.add_argument('-o', action="store", help="output directory", required=True)

    args = parser.parse_args()
    output_dir = args.o
    video_cropped = load_video_cropped_info(args.i)
    video_cropped = [(e[0], e[1], output_dir) for e in video_cropped]
    num_cores = args.n
    with Pool(num_cores) as p:
         msgs = p.map(ffmpeg_crop, video_cropped)
         for e in msgs:
             print(e)

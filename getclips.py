import os
import logging

from parallel_crop import load_video_cropped_info
from detect_letter_box import detect_letter_box 
from adjust_crop import adjust_crop 
from filter import filter_crop_dims

logger = logging.getLogger()

ClipProfiles = {}
ClipProfiles["default"]   = "-y -c copy"
ClipProfiles["popcorn"]   = "-y -vf yadif -c:v libx264 -refs 4 -b:v 5M -coder 1 -preset ultrafast -acodec aac -ac 2 -ar 44100  -ab 128k -f mp4"
ClipProfiles["small"]     = "-y -vf yadif -c:v libx264 -refs 4 -b:v 2M -coder 1 -preset ultrafast -acodec aac -ac 2 -ar 44100  -ab 128k -f mp4"
ClipProfiles["letterbox"] = "-y -vf yadif {} -c:v libx264 -refs 4 -b:v 5M -coder 1 -acodec aac -ac 2  -ar 44100  -ab 128k -f mp4"


def find_crop_coordinates (filename):
    list_crop = detect_letter_box([filename])
    list_crop_filter = filter_crop_dims(list_crop, 20)
    list_adjusted = adjust_crop(list_crop_filter)
    crop_info = load_video_cropped_list(list_adjusted)
    if len(crop_info) == 0 or len(crop_info[0]) < 2:
        return ""
    return "-vf " + crop_info[0][1]


def video_cut (source, start, stop, dest, profile):
    dur = stop - start
    cmd = f"ffmpeg -v quiet -ss {start} -i {source} -t {dur} {profile} {dest} "
    #print (cmd)
    return os.system(cmd)


def thumb(name):
    return os.path.splitext(name)[0] + '.jpg'


def make_thumbnail (fname, posn=1):
    success = True
    try:
        th_name = thumb(fname)
        os.system (f"ffmpeg -v quiet -y -ss {posn} -i {fname} -vframes 1 -q:v 2 {th_name}")
    except Exception as err:
        logger.error (f"make_thumbnail {fname}: {err}")
        success = False
    return success


# from https://stackoverflow.com/questions/1131220/get-md5-hash-of-big-files-in-python
def videofile_md5(filename, chunk_size=65536):
    import hashlib
    with open(filename, "rb") as f:
        file_hash = hashlib.md5()
        while True:
            chunk = f.read(chunk_size)
            if len(chunk) < 1:
                break
            file_hash.update(chunk)
    return file_hash.hexdigest()


def get_clips (input_video, scene_list, output_dir, overwrite=False, profile="default"):
    try:
        hashed_name = videofile_md5(input_video) 
    except Exception as err:
        logger.error (f"get_clips {input_video}: {err}")
        return None
    outdirname = os.path.join (output_dir, hashed_name)
    if not os.path.exists(outdirname):
        os.makedirs(outdirname, exist_ok=True)

    profile_str = ClipProfiles[profile]
    if profile == 'letterbox':
        mod = find_crop_coordinates (input_video)  # returns ffmpeg syntax
        profile_str = profile_str.format(mod)
  
    ext = os.path.splitext(input_video)[1]
    for start,stop in scene_list:
        clipname = os.path.join (outdirname, f"video.{start:.2f}-{stop:.2f}{ext}")
        if overwrite or not os.path.exists (clipname):
            video_cut (input_video, start, stop, clipname, profile_str)
            make_thumbnail (clipname)
        else:
            logger.info (f"already exists: {clipname}")
    return hashed_name


def get_duration (input_video):
    import subprocess
    res = subprocess.check_output(f'ffprobe -i {input_video} -show_entries format=duration -v quiet -of csv="p=0"',shell=True)
    return float(res)




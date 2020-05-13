import os
import logging
from parallel_crop import load_video_cropped_info


logger = logging.getLogger()

ClipProfiles = {}
ClipProfiles["default"] = "-y -c copy"
ClipProfiles["popcorn0"] = "-vf yadif -c:v libx264 -refs 4 -b:v 5M -coder 1 -preset photo -acodec aac -ac 2  -ar 44100  -ab 128k -f mp4"    #preset doesn't work
ClipProfiles["popcorn"] = "-y -vf yadif -c:v libx264 -refs 4 -b:v 5M -coder 1 -acodec aac -ac 2  -ar 44100  -ab 128k -f mp4"
ClipProfiles["letterbox"] = "-y -vf yadif {} -c:v libx264 -refs 4 -b:v 5M -coder 1 -acodec aac -ac 2  -ar 44100  -ab 128k -f mp4"



def find_crop_coordinates (filename):
    os.system (f"echo {filename} > video_list.txt")
    os.system("cat video_list.txt | python detect_letter_box.py crop_info.txt")
    os.system("cat crop_info.txt | python filter.py 20 > crop_filtered.txt")
    os.system("cat crop_filtered.txt | python adjust_crop.py > crop_adjusted.txt")
    crop_info = load_video_cropped_info("crop_adjusted.txt")
    return "-vf " + crop_info[0][1]


def video_cut (source, start, stop, dest, profile):
    dur = stop - start
    cmd = f"ffmpeg -v quiet -ss {start} -i {source} -t {dur} {profile} {dest} < /dev/null"
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
    elif not overwrite:
        logger.info (f"already exists: {hashed_name}")
        return hashed_name

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



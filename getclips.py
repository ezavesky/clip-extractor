import os.path
import logging
logger = logging.getLogger()


# Easily replaced with alternate versions

from moviepy.editor import VideoFileClip
from moviepy.video.io.ffmpeg_tools import ffmpeg_extract_subclip

def make_one_clip (input_video_name, start_time, end_time, output_file):
    from moviepy.video.io.ffmpeg_tools import ffmpeg_extract_subclip
    success = True
    try:
        ffmpeg_extract_subclip(input_video_name, start_time, end_time, output_file)
    except Exception as err:
        logger.error (f"get_clip {input_video_name}:", err)
        success = False
    return success



def get_thumbnail (input_clip_name, thumb_name):
    success = True
    try:
        vid = VideoFileClip(input_clip_name)
        vid.save_frame(thumb_name, 1)
        vid.close()
    except Exception as err:
        logger.error (f"get_thumbnail {input_clip_name}:", err)
        success = False
    return success



def thumb(name):
    return os.path.splitext(name)[0] + '.jpg'



def make_thumbnail (fname):
    success = True
    try:
        th_name = thumb(fname)
        vid = VideoFileClip(fname)
        vid.save_frame(th_name, 1)
        vid.close()
    except Exception as err:
        logger.error (f"make_thumbnail {fname}:", err)
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



def get_clips (input_video, scene_list, output_dir):
    try:
        hashed_name = videofile_md5(input_video) 
    except Exception as err:
        logger.error (f"get_clips {input_video}: {err}")
        return None
    ext = os.path.splitext(input_video)[1]
    for start,stop in scene_list:
        clipname = os.path.join (output_dir, f"{hashed_name}_{start}-{stop}{ext}")
        if not os.path.exists (clipname):
            make_one_clip (input_video, start, stop, clipname)
            make_thumbnail (clipname)
        else:
            logger.info ("already exists: {clipname}")
    return hashed_name



















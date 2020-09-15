#! python
# ===============LICENSE_START=======================================================
# clip_extractor Apache-2.0
# ===================================================================================
# Copyright (C) 2017-2020 AT&T Intellectual Property. All rights reserved.
# ===================================================================================
# This software file is distributed by AT&T 
# under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# This file is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
# ===============LICENSE_END=========================================================
# -*- coding: utf-8 -

from os import getenv
import sys
from pathlib import Path
import argparse
import pandas as pd
from datetime import datetime
import json

import logging

logger = logging.getLogger()
logger.setLevel(logging.INFO)

import contentaiextractor as contentai
import _version

from getclips import get_clips, get_duration, validate_profile
from event_retrieval import parse_results, event_rle, load_scenes, event_alignment

import bisect

def do_alignment (metadata_path, align_type, time_tuples, list_of_extractors=None):
    print("metadata_path: " + str(metadata_path))
    print("align_type: " + str(align_type))
    print("time_tuples: " + str(time_tuples))
    print("list_of_extractors: " + str(list_of_extractors))
    bounds = parse_results(metadata_path, verbose=True, parser_type=align_type)
    print("type of bounds is" + str(type(bounds)))
    if list_of_extractors is not None and len(list_of_extractors) > 0:
        bounds = bounds[bounds['extractor'].isin(list_of_extractors)]
    starts = sorted(bounds['time_begin'])       # start and stop must be sorted separately b/c of possible overlap
    stops = sorted(bounds['time_end'])
    output = []
    for t_begin, t_end in time_tuples:
        left = bisect.bisect_left(starts, t_begin) - 1
        new_begin = starts[left] if left >= 0 else starts[0]
        right = bisect.bisect_right(stops, t_end)
        new_end = stops[right] if right < len(stops) else stops[-1]
        output.append((new_begin, new_end))
    return output


def clip(input_params=None, args=None):
    # extract data from contentai.content_url
    # or if needed locally use contentai.content_path
    # after calling contentai.download_content()

    print("Downloading content from ContentAI")
    contentai.download_content()

    parser = argparse.ArgumentParser(
        description="""A script to launch a clip extraction and transcode process...""",
        epilog="""
        (*) Certain tag types expand to special multi-tag classes....
            tag:face -> search among tag_type 'tag' but tag name must contain 'face'
            identity:speaker_ -> search among tag_type 'identity' but tag name must contain 'speaker_'
            identity:^speaker_ -> search among tag_type 'identity' but tag name must *NOT* contain 'speaker_'

        Example execution patterns...
            # detect scenes from transcript output (max of 90s), then apply standard trimming 
            python main.py --path_content results-witch/video.mp4 \
                --path_result results-witch/test --duration_max 90 --alignment_type transcript --profile popcorn 

            # using an existing video, bootstrap a scene boundary from 15s from the start and 15s from the end
            #   align using tags of type 'tag' containing the word 'face'; write CSV output and uniquely tag each output
            python main.py --path_content results-witch/video.mp4 --profile popcorn --snack_id 12 --csv_file output.csv\
                --path_result results-witch/test --clip_bounds 15 -15 --duration_max 90 --alignment_type "tag:face" 

            # using an existing video, bootstrap a scene boundary from 15s from the start and 15s from the end
            #   align using tags of type 'identity' NOT containing the word 'speaker_'
            python main.py --path_content results-witch/video.mp4 --profile popcorn \
                --path_result results-witch/test --clip_bounds 15 -15 --duration_max 90 --alignment_type "identity:^speaker_" 

            # using an existing video, bootstrap a scene boundary from 15s from the start and 15s from the end, apply a
            #   maximum duration of 90s and trim with transcrips, generate video on completion
            python main.py --path_content results-witch/video.mp4 --profile popcorn \
                --path_result results-witch/test --clip_bounds 15 -15 --duration_max 90 --alignment_type transcript 

            # using an existing video, bootstrap a scene boundary from 15s from the start and 15s from the end, apply a
            #   maximum duration of 90s and trim with transcrips
            python main.py --path_content results-witch/video.mp4 --finalize_type tag \
                --path_result results-witch/test --clip_bounds 15 -15 --duration_max 90 --alignment_type transcript 

            # using an existing video, bootstrap a scene bonudary from 5s from the start and 5s from the end, trim with 
            #   detected identity tags and do not encode a resultant video or frame (no profile provided)
            python main.py --path_content results-witch/HBO_20200222_114000_000803_00108_season_of_the_witch.mp4/video.mp4 \
                --path_result results-witch/test --clip_bounds 5 -5 --alignment_type identity
    """, formatter_class=argparse.RawTextHelpFormatter)
    submain = parser.add_argument_group('main execution and evaluation functionality')
    submain.add_argument('--path_content', type=str, default=contentai.content_path, 
                            help='input video')
    submain.add_argument('--path_result', type=str, default=contentai.result_path, 
                            help='output path for generated videos')
    submain.add_argument('--path_scenes', type=str, default="", 
                            help='FILE to specify scene begin,end or DIRECTORY with extractor event outputs')
    submain.add_argument('--quiet', dest='quiet', default=False, action='store_true', help='do not verbosely print operations')
    submain.add_argument('--csv_file', dest='csv_file', default='', type=str, help='also write output records to this CSV file (in the result dir)')
    submain.add_argument('--snack_id', type=int, default=-10, help='append unique identifier to the row')

    submain = parser.add_argument_group('encoding/output specifications')
    submain.add_argument('--profile', type=str, default='none', help='processing profile to use (specify "list" for available list)')
    submain.add_argument('--overwrite', default=False, action='store_true', help='force overwrite of existing files')

    submain = parser.add_argument_group('overall boundary modifications')
    # submain.add_argument('--time_smudge', type=float, default=0.5, help='time in seconds to rewind/ffwd final scene boundaries (0=off, default %(default)s)')
    submain.add_argument('--finalize_type', type=str, default='shot', help='what tag_type* should be used for clip alignment (as a finalize timing, default %(default)s)')
    submain.add_argument('--duration_max', type=float, default=-1, help='max duration in seconds from scene selction or clip specification (-1 disables)')
    submain.add_argument('--duration_min', type=float, default=10, help='minimum length in seconds for event scene selection (default %(default)s)')

    submain = parser.add_argument_group('scene detection specifications')
    submain.add_argument('--event_type', type=str, default='transcript', help='what tag_type* should be used to identify clips')
    submain.add_argument('--event_expand_length', type=float, default=5, help='expand instant events to a minimum of this length (default %(default)s)')
    submain.add_argument('--event_min_score', type=float, default=0.8, help='min confidence for new event to be considered in a scene (default %(default)s)')
    submain.add_argument('--clip_bounds', type=float, nargs=2, metavar=('start', 'stop'), help='fixed scene timing (instead of events); start/stop (10 36) or negative stop trims from end (10 -10)', default=None)

    submain = parser.add_argument_group('final alignment specifications')
    submain.add_argument('--alignment_type', type=str, default=None, help='what tag_type* should be used for clip alignment (default %(default)s)')
    submain.add_argument('--alignment_extractors', nargs='+', default=None, help='use shots only from these extractors during alignment')
    submain.add_argument('--alignment_min_score', type=float, default=0.6, help='min confidence for new event to be use in trim (default %(default)s)')
    submain.add_argument('--alignment_no_shrink', default=False, action='store_true', help='forbid shrinking alignment during processing')
    
    input_vars = contentai.metadata
    if args is not None:
        input_vars.update(vars(parser.parse_args(args)))
    else:
        input_vars.update(vars(parser.parse_args()))
    if input_params is not None:
        input_vars.update(input_params)

    version_info = _version.version()
    logger.info(f"Received parameters: {input_vars}")
    logger.info(f"Running Version: {version_info}")

    path_video = Path(input_vars['path_content'])   # path to a video file
    path_result = Path(input_vars['path_result'])   # destination dir
    path_scenes = Path(input_vars['path_scenes'] if len(input_vars['path_scenes']) else "/INVALID_FILE")   # alternate scenes data (could be file or dir)

    def meta_path ():       # metadata path is only calculated when needed
        if path_scenes.is_dir() and path_scenes.exists():
            meta = path_scenes
        else:
            meta = path_video.parent
        return str(meta)

    if not validate_profile(input_vars['profile']):
        return None

    if not input_vars['quiet']:
        logger.info("*p1* (asset extraction) ffmpeg operation to pull out clips; provide specific processing profiles")

    duration_video = get_duration(path_video)  # attempt to get duration, 0 if not available
    if not input_vars['quiet']:
        logger.info("*p2* (clip specification) peak detection and alignment to various input components (e.g. shots, etc)")
    if input_vars['clip_bounds'] is not None:       # this overrides any other scene designations
        if input_vars['clip_bounds'][1] < 0.0:
            input_vars['clip_bounds'][1] += duration_video
        if input_vars['duration_max'] > 0.0:   # if max duration passed, hard-limit response
            input_vars['clip_bounds'][1] = min(input_vars['clip_bounds'][0] + input_vars['duration_max'],  input_vars['clip_bounds'][1])
        df_scenes = pd.DataFrame([input_vars['clip_bounds']], columns=["time_begin", "time_end"])
    else:
        df_scenes = load_scenes(str(path_scenes))
        if df_scenes is None:
            df_event = parse_results(meta_path(), input_vars['event_type'], verbose=not input_vars['quiet'])
            df_scenes = event_rle(df_event, score_threshold=input_vars['event_min_score'], 
                                    duration_threshold=input_vars['duration_min'], 
                                    duration_expand=input_vars['event_expand_length'], peak_method='rle')
    if df_scenes is None or not len(df_scenes):
        logger.error(f"Error: No scene sources were provided ('{input_vars['path_scenes']}') or found with events, aborting.")
        return
    if not input_vars['quiet']:
        logger.info(f"Found {len(df_scenes)} scenes with average length {(df_scenes['time_end']-df_scenes['time_begin']).mean()}s from source file...")

    if not input_vars['quiet']:
        logger.info("*p3a* (quality assessment) quality evaluation of frames or video for refined boundaries")

    if not input_vars['quiet']:
        logger.info("*p3b* (moderation assessment) quality evaluation of frames or video for refined boundaries")

    if not input_vars['quiet']:
        logger.info("*p3* (trimming refinement) refinement based on quality requirements (if any)")

    if input_vars['alignment_type'] is None:  # if no alignment type specified, use faullback
        if len(input_vars['finalize_type']):
            logger.warning(f"Upgrading 'finalize' event type '{input_vars['finalize_type']}' to primary alignment type (which was empty).")
            input_vars['alignment_type'] = input_vars['finalize_type']

    if input_vars['alignment_type'] != None:  # if we had an alignment type
        df_event = parse_results(meta_path(), input_vars['alignment_type'], 
                                 verbose=not input_vars['quiet'], 
                                 extractor_list=input_vars['alignment_extractors'])
        if df_event is None or len(df_event) == 0:
            logger.warning(f"Warning: Requested specific alignment type '{input_vars['alignment_type']}' but no events found, trimming may have no effect.")
        df_events_fallback = None
        if len(input_vars['finalize_type']) and input_vars['finalize_type'] != input_vars['alignment_type']:   # had additional fallback type
            df_events_fallback = parse_results(meta_path(), input_vars['finalize_type'], verbose=not input_vars['quiet'])
            if not input_vars['quiet']:
                logger.info(f"(alignment boundaries include {len(df_events_fallback)} fallback events of type '{input_vars['finalize_type']}')")

        if not input_vars['quiet']:
            for idx, row in df_scenes.iterrows():
                logger.info(f"[PRE-Scene {idx}]: START {row['time_begin']} - END {row['time_end']} ")

        df_scenes = event_alignment(df_event, df_scenes, input_vars['duration_max'], input_vars['duration_min'], 
                                    df_events_fallback=df_events_fallback, score_threshold=input_vars['alignment_min_score'],
                                    allow_flip=not input_vars['alignment_no_shrink'])
        if not input_vars['quiet']:
            for idx, row in df_scenes.iterrows():
                logger.info(f"[POST-Scene {idx}]: START {row['time_begin']} ({row['event_begin']}) - END {row['time_end']} ({row['event_end']})")

    list_clips = []
    if len(df_scenes):
        # if input_vars['time_smudge'] > 0.0:
        #     t_smudge = input_vars['time_smudge']
        #     df_scenes["time_begin"] = df_scenes["time_begin"].apply(lambda x: 0 if x - t_smudge < 0 else x - t_smudge)            
        #     df_scenes["time_end"] = df_scenes["time_end"].apply(lambda x: 0 if x + t_smudge > duration_video else x + t_smudge)

        if not input_vars['quiet']:
            logger.info(f"Trimmed to {len(df_scenes)} scenes with average length {(df_scenes['time_end']-df_scenes['time_begin']).mean()}s from source file...")

        if not input_vars['quiet']:
            logger.info("*p4* (previous input) processing input for regions")
        time_tuples = df_scenes[["time_begin", "time_end"]].values.tolist()
        list_clips = get_clips(str(path_video), time_tuples, path_result, 
                                profile=input_vars['profile'], overwrite=input_vars['overwrite'])
        df_scenes["path"] = ""
    if len(list_clips):
        logger.info(f"Clipped video files stored as: '{list_clips}'... ")
        df_scenes["path"] = list_clips

    if not input_vars['quiet']:
        logger.info("*p5* (clip publishing) push of clips to result directory, an S3 bucket, hadoop, azure, etc")

    # write output of each class and segment
    version_dict = _version.version()
    dict_result = {'config': {'version':version_dict['version'], 'extractor':version_dict['package'],
                            'input':str(path_video.resolve()), 'timestamp': str(datetime.now()) }, 'results':[] }
    # enrich each row with event type info
    logger.info(f"Trimmed to {len(list_clips)} scenes...")
    df_scenes["alignment_type"] = input_vars['alignment_type']
    df_scenes["event_type"] = input_vars['event_type']    
    if input_vars['snack_id'] >= 0:
        df_scenes["snack_id"] = input_vars['snack_id']
    dict_result['results'] = df_scenes.to_dict(orient='records')

    # write out data if completed
    logger.info("*p6* exporting cut times to csv/json files file")
    if len(input_vars['path_result']) > 0:
        if not path_result.exists():
            path_result.mkdir(parents=True)
        path_output = path_result.joinpath("data.json")
        with path_output.open('wt') as f:
            json.dump(dict_result, f)
        logger.info(f"Written JSON to '{path_output.resolve()}'...")

        if len(input_vars['csv_file']):
            path_output = path_result.joinpath(input_vars['csv_file'])
            if not path_output.parent.exists():
                path_output.parent.mkdir(parents=True)
            if "event_begin" in df_scenes.columns:
                df_scenes = df_scenes.drop(columns=['event_begin', 'event_end'])
            df_scenes.to_csv(str(path_output), index=False)
            logger.info(f"Written CSV records to '{path_output.resolve()}'...")

    # done writing results, just return
    return dict_result


if __name__ == "__main__":
    clip()


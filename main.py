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
# -*- coding: utf-8 -*-

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

import contentai
import _version

from getclips import get_clips, get_duration, validate_profile
from event_retrieval import parse_results, event_rle, load_scenes, event_alignment


def clip(input_params=None, args=None):
    # extract data from contentai.content_url
    # or if needed locally use contentai.content_path
    # after calling contentai.download_content()

    print("Downloading content from ContentAI")
    contentai.download_content()

    parser = argparse.ArgumentParser(
        description="""A script to launch a clip extraction and transcode process...""",
        epilog="""
        Launch with extractor output directory...
            python -u main.py --path_scenes testing/data/1ZaLRGW9bwk3pN7R6VWpbIBbKZL 
        Launch with environment variable for ContentAI testing...
            EXTRACTOR_METADATA='{"quiet":trie,"path_scenes":"/here"}' python -u main.py
        Launch with command-line parmaeters
            python -u main.py --path_scenes /here --quiet
    """, formatter_class=argparse.RawTextHelpFormatter)
    submain = parser.add_argument_group('main execution and evaluation functionality')
    submain.add_argument('--path_content', type=str, default=contentai.content_path, 
                            help='input video')
    submain.add_argument('--path_result', type=str, default=contentai.result_path, 
                            help='output path for generated videos')
    submain.add_argument('--path_scenes', type=str, default="", 
                            help='FILE to specify scene begin,end or DIRECTORY with extractor event outputs')
    submain.add_argument('--quiet', dest='quiet', default=False, action='store_true', help='do not verbosely print operations')
    submain.add_argument('--csv_file', dest='csv_file', default='', type=str, help='also write output records to this CSV file')

    submain = parser.add_argument_group('encoding/output specifications')
    submain.add_argument('--profile', type=str, default='default', help='processing profile to use (specify "list" for available list)')
    submain.add_argument('--overwrite', default=False, action='store_true', help='force overwrite of existing files')

    submain = parser.add_argument_group('scene detection specifications')
    submain.add_argument('--event_type', type=str, default='face', help='what tag_type should be used to identify clips')
    submain.add_argument('--event_min_score', type=float, default=0.8, help='minimum score for encoding')
    submain.add_argument('--event_expand_length', type=float, default=3, help='expand instant events to a minimum of this length')
    submain.add_argument('--event_min_length', type=float, default=10, help='minimum length in seconds for event scene selection')
    submain.add_argument('--clip_bounds', type=float, nargs=2, metavar=('start', 'stop'), help='fixed scene timing (instead of events); start/stop (10 36) or negative stop trims from end (10 -10)', default=None)
    submain.add_argument('--max_duration', type=float, default=-1, help='max duration in seconds from scene selction or clip specification (-1 disables)')

    submain = parser.add_argument_group('final alignment specifications')
    submain.add_argument('--alignment_type', type=str, default=None, help='what tag_type should be used for clip alignment')
    submain.add_argument('--alignment_extractors', nargs='+', default=None, help='use shots only from these extractors during alignment')

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
    path_scenes = Path(input_vars['path_scenes'])   # alternate scenes data (could be file or dir)

    def meta_path ():       # metadata path is only calculated when needed
        if path_scenes.is_dir():
            meta = path_scenes
        else:
            meta = path_video.parent
        return str(meta)

    if not validate_profile(input_vars['profile']):
        return None

    if not input_vars['quiet']:
        logger.info("*p1* (asset extraction) ffmpeg operation to pull out clips; provide specific processing profiles")

    if not input_vars['quiet']:
        logger.info("*p2* (clip specification) peak detection and alignment to various input components (e.g. shots, etc)")
    if input_vars['clip_bounds'] is not None:       # this overrides any other scene designations
        if input_vars['clip_bounds'][1] < 0.0:
            input_vars['clip_bounds'][1] += get_duration(path_video)
        if input_vars['max_duration'] > 0.0:   # if max duration passed, hard-limit response
            input_vars['clip_bounds'][1] = min(input_vars['clip_bounds'][0] + input_vars['max_duration'],  input_vars['clip_bounds'][1])
        df_scenes = pd.DataFrame([input_vars['clip_bounds']], columns=["time_begin", "time_end"])
    else:
        df_scenes = load_scenes(str(path_scenes))
        if df_scenes is None:
            df_event = parse_results(meta_path(), verbose=not input_vars['quiet'], 
                                     parser_type=input_vars['event_type'])
            df_scenes = event_rle(df_event, score_threshold=input_vars['event_min_score'], 
                                    duration_threshold=input_vars['event_min_length'], 
                                    duration_expand=input_vars['event_expand_length'], peak_method='rle',
                                    max_duration=input_vars['max_duration'])
    if df_scenes is None:
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
    if input_vars['alignment_type'] != None:
        df_event = parse_results(meta_path(), verbose=not input_vars['quiet'], 
                                 parser_type=input_vars['alignment_type'], 
                                 extractor_list=input_vars['alignment_extractors'])
        if df_event is None or len(df_event) == 0:
            logger.warning(f"Warning: Requested specific alignment type '{input_vars['alignment_type']}' but no events found, skipipng trim.")
        else:
            df_scenes = event_alignment(df_event, df_scenes, input_vars['max_duration'])
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

    # write out data if completed
    if len(input_vars['path_result']) > 0:
        if not path_result.exists():
            path_result.mkdir(parents=True)
        path_output = path_result.joinpath("data.json")
        dict_result['results'] = df_scenes.to_dict(orient='records')
        with path_output.open('wt') as f:
            json.dump(dict_result, f)
        print(f"Written JSON to '{path_output.resolve()}'...")

        if len(input_vars['csv_file']):
            path_output = Path(input_vars['csv_file'])
            if not path_output.parent.exists():
                path_output.parent.mkdir(parents=True)
            df_scenes.to_csv(str(path_output), index=False)
            print(f"Written CSV records to '{path_output.resolve()}'...")

    # done writing results, just return
    return dict_result


if __name__ == "__main__":
    clip()


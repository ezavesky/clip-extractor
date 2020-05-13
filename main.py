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

import logging

logger = logging.getLogger()
logger.setLevel(logging.INFO)


import contentai
import _version

from getclips import get_clips
from event_retrieval import parse_results, event_rle, load_scenes


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
            python -u main.py --path_scenes testing/data/1ZaLRGW9bwk3pN7R6VWpbIBbKZL --verbose
        Launch with environment variable for ContentAI testing...
            EXTRACTOR_METADATA='{"verbose":true,"path_scenes":"/here"}' python -u main.py
        Launch with command-line parmaeters
            python -u main.py --path_scenes /here --verbose
    """, formatter_class=argparse.RawTextHelpFormatter)
    submain = parser.add_argument_group('main execution and evaluation functionality')
    submain.add_argument('--path_content', type=str, default=contentai.content_path, 
                            help='input video video (also nested metadata if locally run)')
    submain.add_argument('--path_result', type=str, default=contentai.result_path, 
                            help='output path for generated videos')
    submain.add_argument('--path_scenes', type=str, default="", 
                            help='FILE to specify scene begin,end or DIRECTORY with extractor event outputs')
    submain.add_argument('--verbose', dest='verbose', default=False, action='store_true', help='verbosely print operations')

    submain = parser.add_argument_group('encoding specifications')
    submain.add_argument('--profile', type=str, default='default', help='processing profile to use')

    submain = parser.add_argument_group('what tags and score requirments should be utilized')
    submain.add_argument('--event_type', type=str, default='face', help='what tag_type should be used to identify clips')
    submain.add_argument('--event_min_score', type=float, default=0.8, help='minimum score for encoding')
    submain.add_argument('--event_expand_length', type=float, default=3, help='expand instant events to a minimum of this length')
    submain.add_argument('--event_min_length', type=float, default=10, help='minimum length in seconds for scene selection')


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

    path_content = Path(input_vars['path_content'])   # start with dir of content
    path_result = Path(input_vars['path_result'])   # destination dir

    df_scenes = load_scenes(input_vars['path_scenes'])
    if df_scenes is None:
        df_event = parse_results(input_vars['path_scenes'], verbose=True, parser_type=input_vars['event_type'])
        df_scenes = event_rle(df_event, score_threshold=input_vars['event_min_score'], 
                                duration_threshold=input_vars['event_min_length'], 
                                duration_expand=input_vars['event_expand_length'], peak_method='rle')

    if df_scenes is None:
        logger.error(f"Error: No scene sources were provided {input_vars['path_scenes']}, aborting.")
        return

    logger.info("*p1* (clip extraction) ffmpeg operation to pull out clips; provide specific processing profiles")
    time_tuples = df_scenes[["time_begin", "time_end"]].to_dict(orient='split')['data']

    logger.info("*p2* (clip specification) peak detection and alignment to various input components (e.g. shots, etc)")

    logger.info("*p3* (quality assessment) quality evaluation of frames or video for refined boundaries")
    logger.info("*p3* (moderation assessment) quality evaluation of frames or video for refined boundaries")

    logger.info("*p3* (trimming refinement) refinement based on quality requirements (if any)")

    logger.info("*p4* (previous input) processing input for regions")

    logger.info("*p5* (clip publishing) push of clips to result directory, an S3 bucket, hadoop, azure, etc")
    rootname = get_clips (path_content, df_scenes[["time_begin", "time_end"]].values.tolist(), path_result, profile=input_vars['profile'])
    logger.info(f"Results in: {rootname}")


if __name__ == "__main__":
    clip()


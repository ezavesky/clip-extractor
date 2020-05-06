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
logger.setLevel(logging.DEBUG)
logging.basicConfig()


import contentai
import _version


def clip(input_params=None, args=None):
    # extract data from contentai.content_url
    # or if needed locally use contentai.content_path
    # after calling contentai.download_content()

    print("Downloading content from ContentAI")
    contentai.download_content()

    parser = argparse.ArgumentParser(
        description="""A script to launch a clip docker""",
        epilog="""
        Launch with classes and model server on default port 
            ....
    """, formatter_class=argparse.RawTextHelpFormatter)
    submain = parser.add_argument_group('main execution and evaluation functionality')
    submain.add_argument('--path_video', type=str, default=contentai.content_path, 
                            help='input video path')
    submain.add_argument('--path_result', type=str, default=contentai.result_path, 
                            help='output path for samples')
    submain.add_argument('--profile', type=str, default='default', help='processing profile to use')
    submain.add_argument('--verbose', dest='verbose', default=False, action='store_true', help='verbosely print operations')

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

    path_video = Path(input_vars['path_video'])   # start with dir of content
    path_scenes = Path(input_vars['path_scenes'])   # file containing list of scenes e.g. 0,100\n 100,200\n etc
    path_result = Path(input_vars['path_result'])   # destination dir


    def pair(line):
        items = line.split(",")
        if len(items) != 2:
            items = line.split()
            assert len(items) == 2, "Expected a pair of numbers"
        return float(items[0]), float(items[1])

    # Read the list of scenes -- one start,stop pair per line
    scenes = [pair(x.strip()) for x in open(path_scenes).readlines() if len(x) > 1]

    from getclips import get_clips
    rootname = get_clips (path_video, scenes, path_result, profile=input_vars['profile'])
    logger.info(f"Results in: {rootname}")

    logger.info("---- AFTER THIS THE ACTION HAPPENS -----")

    logger.info("*p4* (previous input) processing input for regions")

    logger.info("*p4* (clip collection) if not available from download, connect to other services to read")

    logger.info("*p2* (clip specification) peak detection and alignment to various input components (e.g. shots, etc)")

    logger.info("*p1* (clip extraction) ffmpeg operation to pull out clips; provide specific processing profiles")

    logger.info("*p3* (quality assessment) quality evaluation of frames or video for refined boundaries")

    logger.info("*p3* (trimming refinement) refinement based on quality requirements (if any)")

    logger.info("*p1* (clip publishing) push of clips to result directory, an S3 bucket, hadoop, azure, etc")




if __name__ == "__main__":
    inputs = {'path_scenes':getenv('EXTRACTOR_SCENES_PATH') }   # other variables are auto-populated
    if None in inputs.values():
        main()
    else:
        clip(input_params=inputs)


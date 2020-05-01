#! python
# ===============LICENSE_START=======================================================
# vinyl-tools Apache-2.0
# ===================================================================================
# Copyright (C) 2017-2019 AT&T Intellectual Property. All rights reserved.
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

import contentai
import os
import sys

import logging

logger = logging.getLogger()
logger.setLevel(logging.DEBUG)

def main(input_vars=None):
    if input_vars is None:   # allow direct call of this module 
        import argparse


        # extract data from contentai.content_url
        # or if needed locally use contentai.content_path
        # after calling contentai.download_content()
        logger.info("Downloading content from ContentAI")
        contentai.download_content()
        contentai.result_path = os.path.dirname(contentai.content_path)


        parser = argparse.ArgumentParser(
            description="""A script to launch a clip docker""",
            epilog="""
            Launch with classes and model server on default port 
                ....
        """, formatter_class=argparse.RawTextHelpFormatter)
        submain = parser.add_argument_group('main execution and evaluation functionality')
        submain.add_argument('--path_video', type=str, default=contentai.content_path, 
                                help='input video path')
        submain.add_argument('--path_result', dest='path_result', type=str, default=contentai.result_path, 
                                help='output path for samples')
        submain.add_argument('--verbose', dest='verbose', default=False, action='store_true', help='verbosely print operations')

        input_vars = vars(parser.parse_args())

        # allow injection of parameters from environment
        if contentai.metadata is not None:  # see README.md for more info
            input_vars.update(contentai.metadata)

    logger.info (f"Received parameters: {input_vars}")

    path_video = os.path.abspath(input_vars['path_video'])   # start with dir of content
    path_scenes = os.path.abspath(input_vars['path_scenes'])   # file containing list of scenes e.g. 0,100\n 100,200\n etc
    path_result = os.path.abspath(input_vars['path_result'])   # destination dir


    def pair(line):
        items = line.split(",")
        if len(items) != 2:
            items = line.split()
            assert len(items) == 2, "Expected a pair of numbers"
        return float(items[0]), float(items[1])

    # Read the list of scenes -- one start,stop pair per line
    scenes = [pair(x.strip()) for x in open(path_scenes).readlines() if len(x) > 1]

    from getclips import get_clips
    rootname = get_clips (path_video, scenes, path_result)

    


    logger.info(f"Input argments: {input_vars}")
    logger.info("---- AFTER THIS THE ACTION HAPPENS -----")

    logger.info("*p4* (previous input) processing input for regions")

    logger.info("*p4* (clip collection) if not available from download, connect to other services to read")

    logger.info("*p2* (clip specification) peak detection and alignment to various input components (e.g. shots, etc)")

    logger.info("*p1* (clip extraction) ffmpeg operation to pull out clips; provide specific processing profiles")

    logger.info("*p3* (quality assessment) quality evaluation of frames or video for refined boundaries")

    logger.info("*p3* (trimming refinement) refinement based on quality requirements (if any)")

    logger.info("*p1* (clip publishing) push of clips to result directory, an S3 bucket, hadoop, azure, etc")




if __name__ == "__main__":
    logging.basicConfig()
    inputs = {'path_video':os.getenv('EXTRACTOR_CONTENT_PATH'),'path_scenes':os.getenv('EXTRACTOR_SCENES_PATH'),'path_result':os.getenv('EXTRACTOR_RESULT_PATH') }
    if None in inputs.values():
        main()
    else:
        main(inputs)


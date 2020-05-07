#! python
# ===============LICENSE_START=======================================================
# clip-extractor Apache-2.0
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

import pandas as pd
from pathlib import Path
import glob  # for model listing
from datetime import datetime
import json

import logging

logger = logging.getLogger()
logger.setLevel(logging.DEBUG)

from metadata_flatten.parsers import get_by_type as parser_get_by_type  # parse other extractor inputs

def parse_video(dir_content, verbose=False, extractor=None, parser_type=None):
    if parser_type is None:
        parser_type = ["identity"]

    # TODO: open this up for other input types (see other entries under 'tag_type' 
    #       in https://gitlab.research.att.com/turnercode/metadata-flatten-extractor/blob/master/docs/README.rst#getting-started)
    list_parser_modules = parser_get_by_type(parser_type)

    if extractor is not None:   # given a specific name? if so, search with just that one
        list_parser_modules = [x for x in list_parser_modules if extractor in x["name"]]
    
    for parser_obj in list_parser_modules:  # iterate through auto-discovered packages
        parser_instance = parser_obj['obj'](dir_content)   # create instance
        df = parser_instance.parse({"verbose": verbose})  # attempt to process
        if df is not None:
            df = df[df["tag_type"].isin(parser_type)]   # subselect only shots
        if df is not None and len(df):
            if verbose:
                logger.critical(f"Found  {len(df)} shots with total duration {df['time_end'].max()}...")
            df.reset_index(drop=True, inplace=True)   # drop other index for straight number
            return df
    logger.critical(f"Could not find shots from extractors {[x['name'] for x in list_parser_modules]}, aborting.")
    return None



if __name__ == "__main__":
    # TODO: erase this when further developed
    path_execute = Path(__file__).parent
    path_content = path_execute.joinpath("testing", "data", "1bJREax4oIOcfS87S01mNxYZ5di")  # assumes under local dir
    df_test = parse_video(str(path_content.resolve()), verbose=True)

    # TODO: run length encoding or grouping for similar items 
    
    print(df_test)

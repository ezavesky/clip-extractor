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

import math
from pathlib import Path
import glob  # for model listing
from datetime import datetime
import json
import bisect
import logging

import pandas as pd
import numpy as np


logger = logging.getLogger()
logger.setLevel(logging.DEBUG)

from metadata_flatten.parsers import get_by_type as parser_get_by_type  # parse other extractor inputs
from metadata_flatten.parsers import empty_dataframe


def load_scenes(path_scenes, dir_content=None, parser_type=None, verbose=False):
    path_scenes = Path(path_scenes).resolve()   # file containing list of scenes e.g. 0,100\n 100,200\n etc
    def pair(line):
        items = line.split(",")
        if len(items) != 2:
            items = line.split()
            assert len(items) == 2, "Expected a pair of numbers"
        return float(items[0]), float(items[1])

    scenes = []
    if not path_scenes.exists() or path_scenes.is_dir():
        return None

    # if not path_scenes.exists():
    #     return None
    # if path_scenes.is_dir():
    #     df_events = parse_results(path_scenes, verbose=verbose, parser_type=parser_type)
    #     time_max = df_events["time_end"].max()
    #     time_min = df_events["time_begin"].min()
    #     scenes = [[time_min, time_max]]
    else:   # Read the list of scenes -- one start,stop pair per line
        scenes = [pair(x.strip()) for x in open(path_scenes).readlines() if len(x) > 1]

    return pd.DataFrame(scenes, columns=["time_begin", "time_end"])


def parse_results(dir_content, parser_type, verbose=False, extractor_list=None):
    if type(parser_type) is str:
        parser_type = [parser_type]
    path_content = Path(dir_content)
    if not path_content.exists() or not path_content.is_dir:
        return empty_dataframe()
    parser_sub_incl = ""
    parser_sub_excl = ""
    parser_new = []
    for type_str in parser_type:
        type_str = type_str.split(":")
        parser_new.append(type_str[0])
        if len(type_str) > 1:
            if type_str[1][0] != '^':
                parser_sub_incl = type_str[1]
            else:
                parser_sub_excl = type_str[1][1:]
    parser_type = parser_new

    # TODO: open this up for other input types (see other entries under 'tag_type' 
    #       in https://gitlab.research.att.com/turnercode/metadata-flatten-extractor/blob/master/docs/README.rst#getting-started)
    list_parser_modules = parser_get_by_type(parser_type)

    if extractor_list is not None:   # given a specific name? if so, search with just that one
        if type(extractor_list) != list:  # normalize to list
            extractor_list = [extractor_list]
        list_parser_modules = set()
        for extractor in extractor_list:  # search across all given instances
            list_parser_modules |= set([x for x in list_parser_modules if extractor in x["name"]])
        list_parser_modules = list(list_parser_modules)
    
    df_return = empty_dataframe()
    for parser_obj in list_parser_modules:  # iterate through auto-discovered packages
        parser_instance = parser_obj['obj'](dir_content)   # create instance
        df = parser_instance.parse({"verbose": verbose})  # attempt to process
        if df is not None:
            df = df[df["tag_type"].isin(parser_type)]   # subselect only shots
            if len(parser_sub_incl):    # subselect type within a tag
                df = df[df["tag"].str.contains(parser_sub_incl)]
            if len(parser_sub_excl):    # exclude type within a tag
                df = df[~df["tag"].str.contains(parser_sub_excl)]
        if df is not None and len(df):
            if verbose:
                logger.critical(f"Found  {len(df)} shots with total duration {df['time_end'].max()}...")
            df.reset_index(drop=True, inplace=True)   # drop other index for straight number
            if df_return is None:
                df_return = df
            else:
                df_return = df_return.append(df, ignore_index=False, sort=False)
    if not len(df_return):
        logger.critical(f"Could not find shots from extractors {[x['name'] for x in list_parser_modules]}, aborting.")
    return df_return


def rle(inarray):
    """ 
    run length encoding. Partial credit to R rle function. 
    Multi datatype arrays catered for including non Numpy
    returns: tuple (runlengths, startpositions, values) 
    """
    # Original RLE encoding from this source...
    # https://gitlab.research.att.com/jdong/videoanalytichadoop/blob/master/video_recognition/video_clip_segmentation.py
    ia = np.asarray(inarray)                  # force numpy
    n = len(ia)
    if n == 0: 
        return (None, None, None)
    else:
        y = np.array(ia[1:] != ia[:-1])     # pairwise unequal (string safe)
        i = np.append(np.where(y), n - 1)   # must include last element posi
        z = np.diff(np.append(-1, i))       # run lengths
        p = np.cumsum(np.append(0, z))[:-1] # positions
        return(z, p, ia[i])


def event_rle(df, score_threshold=0.8, duration_threshold=10, duration_expand=3, peak_method='rle', max_duration=-1):
    # original source (has sample for each time interval in video)
    # HBO_20200227_170000_clip_00004  40.2523 9.7069  3600.642700     {"explosion": 0.00016436472414050305}
    # HBO_20200227_170000_clip_00005  49.9592 10.3402 3600.642700     {"explosion": 0.0011733169780347246}
    # HBO_20200227_170000_clip_00006  60.2994 8.8412  3600.642700     {"explosion": 0.022738034287840735}

    # new source (*MAY* have sample only when detected by extractor)
    #     time_begin  time_end  time_event               tag  tag_type source_event    score
    # 0        2.168     2.168       2.168  Nikita Dzhigurda  identity         face  0.50000
    # 1        2.377     2.377       2.377  Nikita Dzhigurda  identity         face  0.50000
    # 2        2.585     2.585       2.585  Nikita Dzhigurda  identity         face  0.50000
    # 3        3.169     3.169       3.169  Nikita Dzhigurda  identity         face  0.76000
    # 4        3.253     3.253       3.253       Jason Momoa  identity         face  1.00000
    # ..         ...       ...         ...               ...       ...          ...      ...
    # 2       47.700    48.300      47.700         speaker_1  identity       speech  0.72644
    # 3       48.300    48.900      48.300         speaker_2  identity       speech  0.75696
    if df is None:
        return None

    # we will be RESAMPLING/EXPANDING the windows, so adjust our duration expecations to a count
    duration_threshold_count = math.floor(duration_threshold / duration_expand)

    list_col_group = ["tag", "source_event", "tag_type"]
    df_segments = None
    for idx_g, df_group in df.groupby(list_col_group):   # iterate by group
        # copy and subselect just a few fields
        df_score = df_group[["time_begin", "time_end", "time_event", "score"]].copy()
        df_score.index = df_score["time_begin"].apply(lambda x: pd.Timedelta(x, unit='seconds'))
        
        # resample to AVERAGE to half expand duration, then resample to FILL to full expand duration
        df_score_sample = df_score.resample(f"{duration_expand / 2}S").mean() \
                                    .resample(f"{duration_expand}S").bfill().fillna(0)

        # now perform run-length encoding from score mask
        mask = np.array(df_score_sample["score"]) > score_threshold
        if peak_method == 'rle':
            runlengths, start_pos, score_valid  =  rle(mask)
        else:
            logger.error(f"Error: Unknown peak-detection method {peak_method}, aborting.")
            return None
        n  = len(runlengths)

        output = []
        for i in range(n):
            if runlengths[i] >= duration_threshold_count and score_valid[i] == True:
                start_off = start_pos[i]
                start_time = df_score_sample.iloc[start_off]["time_begin"]
                if i + 1 >= n:
                    end_off = len(df_score_sample) - 1
                else:
                    end_off = start_pos[i+1]
                end_time = df_score_sample.iloc[end_off-1]["time_end"]  # note that we adjust back for valid 'time_end'
                avg_score = df_score_sample.iloc[start_off:end_off]["score"].mean()
                output.append( [start_time, end_time, avg_score])
        df_new = pd.DataFrame(output, columns=["time_begin", "time_end", "score"])
        for col_idx in range(len(list_col_group)):
            df_new[list_col_group[col_idx]] = idx_g[col_idx]

        if df_segments is None:
            df_segments = df_new
        else:
            df_segments = df_segments.append(df_new, sort=False)
        # print(idx_g, duration_threshold, output)
    return df_segments.reset_index(drop=True)


def event_search(row, df, max_duration, direction_earlier, df_fallback=None, allow_flip=True):
    time_return = 0 
    if not direction_earlier:  # if going later, cap by max offset/duration
        time_return = row['time_end']
        if max_duration > 0:
            time_return = min(time_return, row['time_begin'] + max_duration)
    event_return = None

    side_search = 'left' if direction_earlier else 'right'
    field_search = 'time_begin' if direction_earlier else 'time_end'

    idx = df[field_search].searchsorted(row[field_search], side=side_search)
    if direction_earlier:
        idx -= 1
    # print("PRIMARY", direction_earlier, idx,df )

    if idx >= 0 and idx < len(df):
        # print(left, len(df_starts), row['time_begin'])
        # print(df_starts["time_begin"])
        time_return = df.iloc[idx][field_search]
        event_return = df.iloc[idx].to_dict()   # save the begin event info
    else:
        # special logic to see if it's closer to search "inward"
        new_row = row.copy()   # copy to a new working row
        if allow_flip:
            time_center = (new_row['time_end'] + new_row['time_begin']) / 2
            if direction_earlier:
                new_row['time_end'] = new_row['time_begin']
            else:
               new_row['time_begin'] = new_row['time_end']
            time_return, event_return = event_search(new_row, df, max_duration, not direction_earlier, df_fallback, False)
            # print("FLIP PROPOSAL", direction_earlier, time_return)
        
        if df_fallback is not None:   # utilize fallback if there (e.g. shots)
            idx = df_fallback[field_search].searchsorted(row[field_search], side=side_search)
            if direction_earlier:
                idx -= 1
            if idx >= 0 and idx < len(df_fallback):
                time_fallback = df_fallback.iloc[idx][field_search]
                if not allow_flip or abs(time_center - time_fallback) < abs(time_center - time_return):  # new fallback was better
                    time_return = df_fallback.iloc[idx][field_search]
                    event_return = df_fallback.iloc[idx].to_dict()   # save the begin event info
                    # print(f"FALLBACK LEFT - {left}, from: {row['time_begin']} to {time_return }")
        # end of miss from first pass
    return time_return, event_return


def event_alignment(df_events, df_scenes, max_duration=-1, min_duration=-1, 
                    df_events_fallback=None, score_threshold=0.5, allow_flip=True):
    df_events_sub = df_events[df_events['score'] >= score_threshold]
    df_starts = df_events_sub.sort_values('time_begin')       # start and stop must be sorted separately b/c of possible overlap
    df_ends = df_events_sub.sort_values('time_end')

    df_starts_fallback = None
    df_ends_fallback = None
    if df_events_fallback is not None:
        df_events_sub = df_events_fallback[df_events_fallback['score'] >= score_threshold]
        df_starts_fallback = df_events_sub.sort_values('time_begin')
        df_ends_fallback = df_events_sub.sort_values('time_end')
    # print("ALLOW FLIP", allow_flip)
    list_return = []
    for idx, row in df_scenes.iterrows():
        new_row = row.copy()   # copy to a new working row
        new_row['event_begin'] = {}
        new_row['event_end'] = {}

        new_row['time_begin'], new_row['event_begin'] = \
            event_search(row, df_starts, max_duration, True, df_starts_fallback, allow_flip)
        new_row['time_end'], new_row['event_end'] = \
            event_search(row, df_ends, max_duration, False, df_ends_fallback, allow_flip)

        # TODO: instead of hard cut for end, trim from both sides, assuming event in middle?

        list_return.append(new_row)
    return pd.DataFrame(list_return)


if __name__ == "__main__":
    # TODO: erase this when further developed
    path_execute = Path(__file__).parent
    path_content = path_execute.joinpath("testing", "data", "1ZaLRGW9bwk3pN7R6VWpbIBbKZL")  # assumes under local dir
    df_test = parse_results(str(path_content.resolve()), verbose=True, parser_type='face')

    # TODO: run length encoding or grouping for similar items 
    df_segment = event_rle(df_test, duration_threshold=10, duration_expand=3)
    print(df_segment)

    print(df_segment[["time_begin", "time_end"]].to_dict(orient='split')['data'])

    # print(df_test[["time_begin", "time_end", "time_event", "tag", "tag_type", "source_event", "score"]])

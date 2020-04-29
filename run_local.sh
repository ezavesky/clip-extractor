#!/bin/bash

# example script for local run
if [ $# -lt 2 ]; then
	echo "./run_local.sh <source_video> <output_data_dir> <docker_image> [<json_args>] - run clip extraction on source with prior processing"
    echo "  <docker_image> = 0 IF local, otherwise a docker image to run "
    echo "  e.g. ./run_local.sh video.mp4 results/ clip_extractor '{\"upstream_path\":\"JOB\", \"threshold_value\":0.0}' -- run on video.mp4 and JOB as chained extractor output dir"
    echo "" 
    exit -1
fi

RUNARGS="$4"
DOCKERIMG="$3" # clip_extractor # 0a9d09f733e1

if [ "$DOCKERIMG" == "0" ]; then
    docker run --rm -v `pwd`/..:/work -e EXTRACTOR_METADATA="$RUNARGS" -e EXTRACTOR_NAME=clip_extractor -e EXTRACTOR_JOB_ID=1 \
        -e EXTRACTOR_CONTENT_PATH=$1 -e EXTRACTOR_CONTENT_URL=file://$1 -e EXTRACTOR_RESULT_PATH=$2 $DOCKERIMG
else
    EXTRACTOR_METADATA="$RUNARGS" EXTRACTOR_NAME=clip_extractor EXTRACTOR_JOB_ID=1 \
        EXTRACTOR_CONTENT_PATH=$1 EXTRACTOR_CONTENT_URL=file://$1 EXTRACTOR_RESULT_PATH=$2 \
        python -u main.py
fi

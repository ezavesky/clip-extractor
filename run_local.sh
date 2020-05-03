# example script for local run
if [ $# -lt 1 ]; then
	echo "./run_local.sh <docker_image> [<source_directory> <output_data_dir> [<json_args>]] [<all_args>]"
    echo "   - run clip extraction on source with prior processing"
    echo " "
    echo "  <docker_image> = 0 IF command-line based (args using arg parse) "
    echo "                 = 1 IF local, otherwise a docker image to run "
    echo "                 = IMAGE_NAME IF docker image name to run"
    echo " "
    echo "  ./run_local.sh 0 --path_content features/ --path_result results/ --verbose "
    echo "  ./run_local.sh 1 features/ results/ 0 '{\"verbose\"true}' "
    echo "" 
    exit -1
fi

DOCKERIMG="$1" # clip_extractor # 0a9d09f733e1
shift
echo "docker_image '$DOCKERIMG'"

if [ "$DOCKERIMG" == "0" ]; then
    python -u main.py $@

elif [ "$DOCKERIMG" == "1" ]; then
    EXTRACTOR_METADATA="$3" EXTRACTOR_NAME=clip_extractor EXTRACTOR_JOB_ID=1 \
        EXTRACTOR_CONTENT_PATH=$1 EXTRACTOR_CONTENT_URL=file://$1 EXTRACTOR_RESULT_PATH=$2 \
        python -u main.py

else
    docker run --rm -v `pwd`/..:/work -e EXTRACTOR_METADATA="$3" -e EXTRACTOR_NAME=clip_extractor -e EXTRACTOR_JOB_ID=1 \
        -e EXTRACTOR_CONTENT_PATH=$1 -e EXTRACTOR_CONTENT_URL=file://$1 -e EXTRACTOR_RESULT_PATH=$2 $DOCKERIMG
fi

# produced 3.6G
## FROM        conda/miniconda3:latest
# produced only 2.3G
FROM python:3.7-slim
MAINTAINER  Eric Zavesky <ezavesky@research.att.com>

ARG WORKDIR=/usr/src/app
ARG PYPI_INSTALL="" 
# " --index-url http://dockercentral.it.att.com:8093/nexus/repository/pypi-group/simple --trusted-host dockercentral.it.att.com"

# install pacakages
WORKDIR $WORKDIR
COPY . $WORKDIR

RUN python -V \
    # create user ID and run mode
    # && groupadd -g $gid $user && useradd -m -u $uid -g $gid $user \
    ## && conda info \
    && apt-get update \
    # need to build something?
    && apt-get -y install gettext git vim ffmpeg \
    # update conda base
    # && conda update -n base -c defaults conda
    ## && conda install tensorflow keras \
    ## && conda install -c conda-forge pandas librosa flask "PyYAML<5.2" \
    # install dependencies not found in conda
    && pip install $PYPI_INSTALL --no-cache-dir --upgrade pip \
    && pip install $PYPI_INSTALL --no-cache-dir -r $WORKDIR/requirements.txt \
    # && cd $WORKDIR && python -c "import boundary; boundary.validate_embedding_models('$WORKDIR/models/pexels_austin.jpg')" \
    # clean up mess from gcc
    && apt-get -qq -y remove \
    && apt-get -qq -y autoremove \
    && apt-get autoclean \
    ## && conda clean -a  \
    # write bash file to determine how it works
    && echo "echo \"Args - \$@ - $WORKDIR \" " > $WORKDIR/run_script.sh \
    # && echo "echo \" Run with 'server' for flask app or no arguments for ContentAI CLI\" " >> $WORKDIR/run_script.sh \
    # && echo "cd $WORKDIR; " >> $WORKDIR/run_script.sh \
    # && echo "if [ \"\$1\" = \"server\" ]; then flask run -h 0.0.0.0 -p 9101 ; " >> $WORKDIR/run_script.sh \
    # && echo "else python -u ./main.py; fi" >> $WORKDIR/run_script.sh \
    && echo "python -u ./main.py" >> $WORKDIR/run_script.sh \
    && chmod +x $WORKDIR/run_script.sh 


EXPOSE 9101
CMD  ./run_script.sh $run_mode

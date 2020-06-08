# produced 3.6G
## FROM        conda/miniconda3:latest
# produced only 2.3G
FROM python:3.7-slim
MAINTAINER  Eric Zavesky <ezavesky@research.att.com>

ARG WORKDIR=/usr/src/app
ARG PYPI_INSTALL="" 
# " --index-url http://dockercentral.it.att.com:8093/nexus/repository/pypi-group/simple --trusted-host dockercentral.it.att.com"
ENV PROFILE=none

# install pacakages
WORKDIR $WORKDIR
COPY requirements.txt $WORKDIR

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
    echo "Done with build..."

COPY . $WORKDIR
EXPOSE 9101
CMD  python -u ./main.py $PROFILE
    

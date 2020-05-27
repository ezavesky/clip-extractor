clip-extractor
==============

A method to run clip extraction on new content with hooks for
operation within the `ContentAI Platform <https://www.contentai.io>`__.

**This is a skeleton project that will be updated as it is developed**

.. image:: docs/clip_prep.jpg
   :width: 400


1. `Getting Started <#getting-started>`__
2. `Testing <#testing>`__
3. `Changes <#changes>`__

Getting Started
===============

This library can be used as a `single-run
executable <#contentai-standalone>`__. Runtime parameters can be passed
for processing that configure the returned results and can be examined in
more detail in the `main <main.py>`__ script.

-  ``verbose`` - *(bool)* - verbose input/output configuration printing (*default=false*)
-  ``path_content`` - *(str)* - input video path for files to label (*default=video.mp4*)
-  ``path_result`` - *(str)* - output path for samples (*default=.*)
-  ``path_scenes`` - *(str)* - FILE to specify scene begin,end or DIRECTORY with extractor event outputs (*default=``path_content``*)
-  ``profile`` - *(string)* - specify a specific transcoding profile for the output video clips
-  ``overwrite`` - *(flag)* - force overwrite of existing files at result path  (*default=false*)
-  ``event_type`` - *(string)* - specify an event type to look for in generation (*default=tag*)
-  ``event_min_score`` - *(float)* - minimum confidence score for a new event to be considered in a scene (*default=0.8*)
-  ``event_min_length`` - *(float)* - minimum length in seconds for scene selection (*default=10*)
-  ``event_expand_length`` - *(float)* - expand instant events to a minimum of this length in seconds (*default=3*)
-  ``alignment_type`` - *(string)* - what tag_type should be used for clip alignment (*default=None*)
-  ``alignment_extractors`` - *(string list)* - use shots only from these extractors during alignment (*default=None*)
-  ``clip_bounds`` - *(float, float)* - clip boundaries; negative stop offsets from end (*default=None*)


Clip Extractor Operations
-------------------------

1. Pre-processing - Steps to be determined before any transcoding or clipping is performed.
   
   * Letterbox detection - will use tools to analyze the first N seconds of video and
     determine if the content is letterboxed.  (profile=letterbox)

2. Transcoding and clipping - All-in-one steps to simultaneously seek to and clip out a region
   of video.  Here, different profiles are available and can be specified via the ``profile`` 
   paremeter above.
   
   * TBD
   * TBD 2



Execution and Deployment
========================

This package is meant to be run as a one-off processing tool that
aggregates the insights of other extractors.

Locally Run
-----------

Run the code as if it is an extractor. In this mode, configure a few
environment variables to let the code know where to look for content.

To install package dependencies in a fresh system, the recommended
technique is a combination of conda and pip packages. The latest
requirements should be validated from the ``requirements.txt`` file but
at time of writing, they were the following.

.. code:: shell

   pip install --no-cache-dir -r requirements.txt 


One can also run the command-line with a single argument as input and
optionally ad runtime configuration (see `runtime
variables <#getting-started>`__) as part of the ``EXTRACTOR_METADATA``
variable as JSON.

For utility, the above line has been wrapped in the bash script
``run_local.sh``.

.. code:: shell

    RUNARGS="$3"
    EXTRACTOR_METADATA="$RUNARGS" EXTRACTOR_NAME=dsai_clip_extractor EXTRACTOR_JOB_ID=1 \
        EXTRACTOR_CONTENT_PATH=$1 EXTRACTOR_CONTENT_URL=file://$1 EXTRACTOR_RESULT_PATH=$2 \
        python -u main.py

This allows a simplified command-line specification of a run
configuration, which also allows the passage of metadata into a
configuration.

*Normal result generation into compressed CSVs (with overwrite).*

.. code:: shell

   ./run_local.sh 0 --path_video path/video.mp4 --path_result results/ --profile letterbox 
   ./run_local.sh 1 path/video.mp4 results/ '{"profile":"letterbox"}'
   ./run_local.sh DOCKERIMAGE path/video.mp4 results/ '{"profile":"letterbox"}'



Deploy and Run
~~~~~~~~~~~~~~

.. code:: shell

   contentai deploy <my_extractor>
   Deploying...
   writing workflow.dot
   done

.. code:: shell

   contentai run s3://bucket/video.mp4 -w 'digraph { dsai_clip_extractor }' -d '{"verbose":true, "threshold_value":0.0}'

   JOB ID:     1Tfb1vPPqTQ0lVD1JDPUilB8QNr
   CONTENT:    s3://video-data-extraction-dev/videos/Conan_10seconds.mp4
   STATE:      complete
   START:      Fri Nov 15 04:38:05 PM (6 minutes ago)
   UPDATED:    1 minute ago
   END:        Fri Nov 15 04:43:04 PM (1 minute ago)
   DURATION:   4 minutes 

   EXTRACTORS

   my_extractor

   TASK      STATE      START           DURATION
   724a493   complete   5 minutes ago   1 minute 

Similarly you can run the code locally.

::

   EXTRACTOR_NAME=dsai_clip_extractor \
   EXTRACTOR_CONTENT_PATH=$PWD/CNN-clip.mp4 \
   EXTRACTOR_RESULT_PATH=$PWD/results \
   python main.py

Or run it via the docker image…

::

   docker run --rm  -v `pwd`/:/x -e EXTRACTOR_CONTENT_PATH=/x/file.mp4 -e EXTRACTOR_RESULT_PATH=/x/result2 -e EXTRACTOR_METADATA='{"verbose":true, "threshold_value":0.0}' dsai_clip_extractor

view extractor logs (stdout)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code:: shell

   contentai logs -f <my_extractor>
   my_extractor Fri Nov 15 04:39:22 PM writing some data
   Job complete in 4m58.265737799s

For an example of how to chain extractors together, see `this
post <extractor-chaining.md>`__.


Testing
=======

(testing and validation forthcoming)

Changes
=======

1.0
---

- 1.0.1
    - fixes for windows and ffmpeg
    - alignment of scene path with directory expectation
    - update parameters in README
    - default scene path to be content source path

- 1.0.0
    - initial creation

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
executable <#contentai-standalone>`__ or a persistent `web
service <#flask-based-webservice>`__. Runtime parameters can be passed
for processing that configure the returned results and can be examped in
more detail in the `process <process.py>`__ script.

-  ``variable`` - *(string)* - specify a specific extractor to utilize
   for shot boundary search; 
   
To install package dependencies in a fresh system, the recommended
technique is a combination of conda and pip packages. The latest
requirements should be validated from the ``requirements.txt`` file but
at time of writing, they were the following.

.. code:: shell

   pip install --no-cache-dir -r requirements.txt 


Execution and Deployment
========================

This package is meant to be run as a one-off processing tool that
aggregates the insights of other extractors.

command-line standalone
-----------------------

Run the code as if it is an extractor. In this mode, configure a few
environment variables to let the code know where to look for content.

One can also run the command-line with a single argument as input and
optionally ad runtime configuration (see `runtime
variables <#getting-started>`__) as part of the ``EXTRACTOR_METADATA``
variable as JSON.

.. code:: shell

   python -u ./main.py 

Locally Run on Results
~~~~~~~~~~~~~~~~~~~~~~

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

   ./run_local.sh path/video.mp4 results/ '{"upstream_path":"2398havAMSDF"}'



Deploy and run
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

Flask-based Webservice
----------------------

Here a webservice will be launched that attempts to use the temp
directory as a primary location for file storage and retrieval. These
files will be posted from the server or retrieved via a URL.

.. code:: shell

   flask run -h 0.0.0.0 -p 9101


Testing
=======

An image ``models/pexels_austin.jpg`` has been included in this repository
for stoking the download of embedding models.  Its original source is 
`pexels <https://www.pexels.com/photo/america-architecture-austin-austin-texas-273204/>`__
and it is used solely for testing and bootstrapping embedding during docker
image creation.

(testing and validation forthcoming)

Changes
=======

1.0
---

- initial creation

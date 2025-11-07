############
pyslidescape
############
|TestStatus| |PyPiStatus| |BlackStyle| |BlackPackStyle| |MITLicenseBadge|

Create your presentation slides in inkscape! `pyslidescape` renders your
inkscape slides into a pdf file.


=======================================================
How to render a video from slides and a voice recording
=======================================================

After compiling your talk, record a voice over ``<path to voice audio.wav>`` with any tool you like and call:

.. code-block:: bash

    slidescape time-slides <output path to text file containing slide paths and durations.txt>

This will open an interactive slide viewer which records the slides order and duration in order to syncronize the slides with your voice over.

.. code-block:: bash

    ffmpeg \
    -f concat \
    -safe 0 \
    -i <path to text file containing slide paths and durations.txt> \
    -i <path to input voice audio.wav> \
    -c:v copy \
    -map 0:v:0 \
    -map 1:a:0 \
    -c:a aac \
    -b:a 384k \
    -pix_fmt yuv420p \
    -framerate 30 \
    <path to output video.mp4>


.. |TestStatus| image:: https://github.com/cherenkov-plenoscope/pyslidescape/actions/workflows/test.yml/badge.svg?branch=main
    :target: https://github.com/cherenkov-plenoscope/pyslidescape/actions/workflows/test.yml

.. |PyPiStatus| image:: https://img.shields.io/pypi/v/pyslidescape
    :target: https://pypi.org/project/pyslidescape

.. |BlackStyle| image:: https://img.shields.io/badge/code%20style-black-000000.svg
    :target: https://github.com/psf/black

.. |BlackPackStyle| image:: https://img.shields.io/badge/pack%20style-black-000000.svg
    :target: https://github.com/cherenkov-plenoscope/black_pack

.. |MITLicenseBadge| image:: https://img.shields.io/badge/License-MIT-yellow.svg
    :target: https://opensource.org/licenses/MIT


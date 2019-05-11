Welcome to pictool's documentation!
===================================

:program:`pictool` is a command line program for manipulating and altering
images. It is useful to show and update location data in images and has some
useful helpers to handle image tags related to location data.

Features
--------

* Handle multiple pictures. Most of the subcommands accept a `path` argument
  which can be used multiple times. Also sub-directories are used when `path`
  is given
* Get and Set GPS coordinates for images. The coordinates are written to the
  image metadata
* List available metadata tas for images
* Set location data tags (like Iptc.Application2.CountryCode) based on the
  available GPS data. This feature uses the `OpenStreetMap Nominatim service`_
* Query GPS coordinates. This is not using any images but is useful to get
  the GPS coordinates for a given address to then add theses GPS coordinates
  to images
* and more!

Installation
------------

For running :program:`pictool`, OpenCV_ and gexiv2_ need to be installed. Usually, both
are included in different distributions (like openSUSE_ or Debian_) and can
be installed via the available package manager (like :program:`zypper` or :program:`apt`).

When the requirements are installed, you can install :program:`pictool` via :program:`pip`::

  pip install pictool

Example usage
-------------

Get the GPS coords form a image
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Given that the GPS coordinates are stored in image(s) metadata, the
coordinates can be printed with:

.. code-block:: console

   pictool gps-get ~/Pictures/testpics/
   /home/tom/Pictures/testpics/20190331_103709.JPG: 7.120040833333334 °N 50.257847222222225 °W 218.0 m



.. _`OpenStreetMap Nominatim service`: https://wiki.openstreetmap.org/wiki/Nominatim
.. _OpenCV: https://opencv.org/
.. _gexiv2: https://wiki.gnome.org/Projects/gexiv2
.. _openSUSE: https://opensuse.org/
.. _Debian: https://www.debian.org/

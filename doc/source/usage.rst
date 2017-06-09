========
Usage
========

Sphinx Configuration
====================

To use the extension, add ``'sphinx-feature-classification'`` to the
``extensions`` list in the ``conf.py`` file in your Sphinx project.

Documenting Your Drivers
========================

1. This extension uses an ini file to render your driver matrix in Sphinx. You
   can begin by creating the file support-matrix.ini file in your sphinx's
   source directory.

2. In the INI file, create driver sections that are prefixed with driver-. The
   section has various options that can be specified.

+------------+-----------+---------------------------------------+
| Field Name | Mandatory | Description                           |
+============+===========+=======================================+
| title      | **Yes**   | Friendly name of the driver.          |
+------------+-----------+---------------------------------------+
| link       | No        | A link to documentation of the driver.|
+------------+-----------+---------------------------------------+

.. code-block:: INI

  [driver.slow-driver]
  title=Slow Driver
  link=https://docs.openstack.org/foo/latest/some-slow-driver-doc

  [driver.fast-driver]
  title=Fast Driver
  link=https://docs.openstack.org/foo/latest/some-fast-driver-doc


3. Next we'll create a feature section to show which drivers support it.

.. code-block:: INI

  [operation.attach-volume]
  title=Attach block volume to instance
  status=optional
  notes=The attach volume operation provides a means to hotplug
  additional block storage to a running instance.
  cli=nova volume-attach <server> <volume>
  driver-slow-driver=complete
  driver-fast-driver=complete

The 'status' field takes possible values

+---------------+------------------------------------------------------+
| Status        | Description                                          |
+===============+======================================================+
| mandatory     | Unconditionally required to be implemented.          |
+---------------+------------------------------------------------------+
| optional      | Optional to support, nice to have.                   |
+---------------+------------------------------------------------------+
| choice(group) | At least one of the options within the named group   |
|               | must be implemented.                                 |
+---------------+------------------------------------------------------+
| condition     | Required, if the referenced condition is met.        |
+---------------+------------------------------------------------------+

The value against each 'driver-XXXX' entry refers to the level
of the implementation of the feature in that driver

+---------------+------------------------------------------------------+
| Status        | Description                                          |
+===============+======================================================+
| complete      | Fully implemented, expected to work at all times.    |
+---------------+------------------------------------------------------+
| partial       | Implemented, but with caveats about when it will     |
|               | work eg some configurations or hardware or guest OS  |
|               | may not support it.                                  |
+---------------+------------------------------------------------------+
| missing       | Not implemented at all.                              |
+---------------+------------------------------------------------------+

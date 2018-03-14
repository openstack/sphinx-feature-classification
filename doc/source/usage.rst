========
Usage
========

Sphinx Configuration
====================

To use the extension, add ``'sphinx_feature_classification.support_matrix'`` to
the ``extensions`` list in the ``conf.py`` file in your Sphinx project.

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


3. Next we'll create a couple of feature sections to show which drivers support
   them. Notice that a driver is only required to implement detach-volume if
   they completed implementing attach-volume.

.. code-block:: INI

  [operation.attach-volume]
  title=Attach block volume to instance
  status=optional
  notes=The attach volume operation provides a means to hotplug
  additional block storage to a running instance.
  cli=my-project attach-volume <instance> <volume>
  driver-slow-driver=complete
  driver-fast-driver=complete

  [operation.detach-volume]
  title=Detach block volume from instance
  status=condition(operation.attach-volume==complete)
  notes=The detach volume operation provides a means to remove additional block
  storage from a running instance.
  cli=my-project detach-volume <instance> <volume>
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

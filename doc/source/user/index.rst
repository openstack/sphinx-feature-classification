=====
Usage
=====

Sphinx Configuration
--------------------

To use the extension, add ``'sphinx_feature_classification.support_matrix'`` to
the ``extensions`` list in the ``conf.py`` file in your Sphinx project.

.. code-block:: python
   :caption: conf.py

   extensions = [
     'sphinx_feature_classification.support_matrix',
     # ... other extensions
   ]

Once added, include the ``support_matrix`` directive in your chosen document.
The directive takes a single argument: a relative path to the INI file in which
the driver matrix is defined.

.. code-block:: rst
   :caption: support-matrix.rst

   .. support_matrix:: support-matrix.ini

See below for more details on the format of this file.


Drivers vs. Features vs. Implementations
----------------------------------------

Drivers
  Drivers are *backends* that are used to implement a set of features. What a
  driver actually is depends entirely on the project being documented. For a
  project like OpenStack Compute (nova), this could be a virtualization driver
  (*libvirt*, *Hyper-V*, *PowerVM*, etc.). For a project like OpenStack
  Storage, this could be a block storage driver (*LVM*, *NFS*, *RBD*, etc.). It
  is entirely project-specific.

Features
  Features are more clear cut. Features are something that your project should
  support (or *must* support). For a project like OpenStack Compute (nova),
  this could be the ability to restart an instance. For a project like
  OpenStack Storage (cinder), this could be the ability to create a snapshot of
  a volume.

Implementation
  Implementations refer to the state of a feature within a given driver. As not
  all features are required, not all drivers may implement them.


Documenting Your Drivers
------------------------

This extension uses an INI file to render your driver matrix in Sphinx. For
example, you may wish to call this file ``support-matrix.ini``. This file
should be placed somewhere within your Sphinx source directory. Within the INI
file, there are multiple sections.

Driver Sections
~~~~~~~~~~~~~~~

Driver sections are prefixed with ``driver.``. You can specify as many of them
as you need for your project. The section has various options that can be
specified.

``title``
  :Mandatory: **Yes**

  Friendly name of the driver.

``link``
  :Mandatory: No

  A link to documentation of the driver.

For example:

.. code-block:: INI
   :caption: support-matrix.ini

   [driver.slow-driver]
   title=Slow Driver
   link=https://docs.openstack.org/foo/latest/some-slow-driver-doc

   [driver.fast-driver]
   title=Fast Driver
   link=https://docs.openstack.org/foo/latest/some-fast-driver-doc

Feature Sections
~~~~~~~~~~~~~~~~

Feature sections are prefixed with ``operation.``. As with driver sections, you
can specify as many of them as you need for your project. These sections are
also used to describe the feature and indicate the implementation status of the
feature among the various drivers, as seen below. These sections have the
following options:

``title``
  :Mandatory: **Yes**

  Friendly name of the feature.

``status``
  :Mandatory: **Yes**

  The importance of the feature or whether it's required. One of:

  ``mandatory``
    Unconditionally required to be implemented.

  ``optional``
    Optional to support; nice to have.

  ``choice(group)``
    At least one of the options within the named group must be implemented.

  ``condition``
    Required, if the referenced condition is met.

``notes``
  :Mandatory: No

  Additional information about the feature.

``cli``
  :Mandatory: No

  A sample CLI command that can be used to utilize the feature.

``api``
  :Mandatory: No

  The alias for this feature in the API.

In addition, there are some driver specific options that should be repeated
for every driver defined earlier in the file.

``driver.XXX``
  :Mandatory: **Yes** (for each driver)

  The level of implementation of this feature in driver ``XXX``. One of:

  ``complete``
    Fully implemented, expected to work at all times.

  ``partial``
    Implemented, but with caveats about when it will work. For example, some
    configurations, hardware or guest OS' may not support it.

  ``missing``
    Not implemented at all.

``driver-notes.XXX``
  :Mandatory: No

  Additional information about the implementation of this feature in driver
  ``XXX``. While this is optional, it is highly recommended for implementations
  in the ``partial`` state.

For example:

.. code-block:: INI
   :caption: support-matrix.ini

   [operation.attach-volume]
   title=Attach block volume to instance
   status=optional
   notes=The attach volume operation provides a means to hotplug additional
       block storage to a running instance.
   cli=my-project attach-volume <instance> <volume>
   api=volume-attach
   driver.slow-driver=complete
   driver.fast-driver=complete

   [operation.detach-volume]
   title=Detach block volume from instance
   status=condition(operation.attach-volume==complete)
   notes=The detach volume operation provides a means to remove additional
       block storage from a running instance.
   cli=my-project detach-volume <instance> <volume>
   api=volume-detach
   driver.slow-driver=complete
   driver-notes.slow-driver=Works without issue if instance is off. When
       hotplugging, requires version foo of the driver.
   driver.fast-driver=complete

Notice that a driver is only required to implement detach-volume if they
completed implementing ``attach-volume``.


Example
-------

This is simply the combined example from above.

.. code-block:: INI
   :caption: support-matrix.ini

   [driver.slow-driver]
   title=Slow Driver
   link=https://docs.openstack.org/foo/latest/some-slow-driver-doc

   [driver.fast-driver]
   title=Fast Driver
   link=https://docs.openstack.org/foo/latest/some-fast-driver-doc

   [operation.attach-volume]
   title=Attach block volume to instance
   status=optional
   notes=The attach volume operation provides a means to hotplug additional
       block storage to a running instance.
   cli=my-project attach-volume <instance> <volume>
   api=volume-attach
   driver.slow-driver=complete
   driver.fast-driver=complete

   [operation.detach-volume]
   title=Detach block volume from instance
   status=condition(operation.attach-volume==complete)
   notes=The detach volume operation provides a means to remove additional
       block storage from a running instance.
   cli=my-project detach-volume <instance> <volume>
   api=volume-detach
   driver.slow-driver=complete
   driver-notes.slow-driver=Works without issue if instance is off. When
       hotplugging, requires version foo of the driver.
   driver.fast-driver=complete

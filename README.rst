Nion Utilities
==============

The Nion Utils library (used in Nion Swift)
-------------------------------------------
Nion utility classes.

.. start-badges

.. list-table::
    :stub-columns: 1

    * - tests
      - | |linux|
    * - package
      - |version|


.. |linux| image:: https://img.shields.io/travis/nion-software/nionutils/master.svg?label=Linux%20build
   :target: https://travis-ci.org/nion-software/nionutils
   :alt: Travis CI build status (Linux)

.. |version| image:: https://img.shields.io/pypi/v/nionutils.svg
   :target: https://pypi.org/project/nionutils/
   :alt: Latest PyPI version

.. end-badges

More Information
----------------

- `Changelog <https://github.com/nion-software/nionutils/blob/master/CHANGES.rst>`_

Introduction
------------

A utility library of useful Python objects.

-  Events
-  Observable
-  Bindings, Converters, Models
-  Geometry
-  Persistence
-  Process, Threads
-  Publish and Subscribe
-  Reference Counting
-  Stream
-  Structured Model

These objects are primarily used within the Nion Python libraries, but
may be useful in general usage too.

This project is funded by Nion Co. as part of the `Nion
Swift <http://nion.com/swift/>`__ imaging and analysis platform. The
code is available under the Apache License, Version 2.0.

Requirements
------------

Requires Python 3.7 or later.

Getting Help and Contributing
-----------------------------

If you find a bug, please file an issue on GitHub. You can also contact
us directly at swift@nion.com.

This is primarily a library focused on providing support to higher level
Nion Python libraries. If you are using this in your own project, we
will accept bug fixes and minor feature improvements via pull requests.
For larger features or additions, please contact us to discuss.

This library includes some direct tests, but is also tested via other
Nion Python projects. Any contribution will need to pass the entire
suite of tests. New contributions should be submitted with new tests.

Summary of Features
-------------------

Events
~~~~~~

Events can be used by objects to notify other objects when something of
interest occurs. The source object "fires" the event, optionally passing
parameters, and the "listener" receives a function call. The source
object determines when to fire an event. The event can have multiple
listeners. The listeners are called synchronously in the order in which
they are added, and the source can fire unconditionally, or until a
listener returns True or False.

.. code:: python

    from nion.utils import Event

    class Telescope:
      def __init__(self):
        self.new_planet_detected_event = Event.Event()

      def on_external_event(self, coordinates):
        self.new_planet_detected_event.fire(coordinates)

    def handle_new_planet(coordinates):
      print("New planet coordinates at " + str(coordinates))

    telescope = Telescope()
    listener = telescope.new_planet_detected_event.listen(handle_new_planet)

    listener.close()  # when finished

Observable
~~~~~~~~~~

The Observable based class defines five basic events for watching for
direct changes to an object such as a property changing, an object being
set or cleared, or an item being inserted or removed from a list. The
observable is used along with events to implement bindings.

.. code:: python

    from nion.utils import Observable

    class MyClass(Observable.Observable):
      def __init__(self):
        self.__weight = 1.0

      @property
      def weight(self):
        return self.__weight

      @weight.setter
      def weight(self, new_weight):
        self.__weight = new_weight
        self.notify_property_changed("weight")

    myc = MyClass()

    def property_changed(key):
      if key == "weight":
        print("The weight changed " + str(myc.weight))

    listener = myc.property_changed_event.listen(property_changed)

    listener.close()  # when finished

Bindings, Converters, Models
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Bindings connect a value in a source object to a value in a target
object. Bindings can be one way bindings from source to target, or two
way bindings from source to target and from target to source. Bindings
can bind property values, lists, or an item in a tuple between the
source and target. Bindings work using the Observable events and
subsequently are implemented via Events.

Bindings can optionally make value conversions between the source and
target. For instance, a binding between a float property and a user
interface text field will need to convert from float to string and back.
Converters between value and strings are included for integer, float,
percentage, check state, and UUID to strings.

Geometry
~~~~~~~~

Classes for integer and float based points, sizes, and rectangles are
included. Additional geometry routines are also included, for instance:
line midpoint.

Persistence
~~~~~~~~~~~

The PersistentObject based class defines a basic structure for storing
objects and their relationship to each other into a persistent storage
context. PersistentObjects can store basic properties, single objects
(to-one relationship) and lists of objects (to-many relationship).
Subclasses must strictly notify the PersistentObject of changes to their
persistent data and follow certain guidelines. Doing so allows the
object to be stored persistently and restored from persistent storage.

Properties in the PersistentObject can have validators, converters,
change notifications, and more. Items and relationships have change
notifications and more.

The PersistentStorageContext defines an interfaces which manages a
collection of PersistentObjects. It must be able to store a simple dict
structure for properties, items, and lists.

Process, Threads
~~~~~~~~~~~~~~~~

Process defines classes to facilitate a threaded queue, which executes
its items serially, and thread set which executes the most recent item
in the set.

ThreadPool defines a threaded dispatcher with the ability to limit
dispatch frequency and a thread pool with the ability to execute
explicitly without threads for testing.

Publish and Subscribe
~~~~~~~~~~~~~~~~~~~~~

Publish and subscribe implements a basic publish and subscribe
mechanism. It is should be considered experimental and is not
recommended for use.

Reference Counting
~~~~~~~~~~~~~~~~~~

The ReferenceCounted base class provides an explicitly reference counted
object that is unique from regular Python reference counting in that it
provides precise control of when the reference is acquired and released.
The about\_to\_delete method is called when reference count reaches
zero.

Stream
~~~~~~

The Stream classes provide a async-based stream of values that can be
controlled using standard reactive operators such as sample, debounce,
and combine. The stream source is an Event named value\_stream and the
source object must provide both the value\_stream and a value property.

Structured Model
~~~~~~~~~~~~~~~~

The Structured Model classes provide a way to describe a data structure
which can produce a modifiable and observable object to be used as a
model for other utility classes such as binding and events.

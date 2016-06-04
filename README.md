Introduction
============
A utility library of useful Python objects.

Requirements
============
Requires Python 3.5 or later.

Events
======
Events can be used by objects to notify other objects when something of interest occurs.
The source object "fires" the event, optionally passing parameters, and the "listener"
receives a function call. The source object determines when to fire an event. The event
can have multiple listeners. The listeners are called synchronously in the order in which
they are added, and the source can fire unconditionally, or until a listener returns True
or False.

Observable
==========
The Observable based class defines five basic events for watching for direct changes to an
object such as a property changing, an object being set or cleared, or an item being inserted
or removed from a list. The observable is used along with events to implement bindings.

Bindings, Converters, PropertyModel
===================================
Bindings connect a value in a source object to a value in a target object. Bindings can be
one way bindings from source to target, or two way bindings from source to target and from
target to source. Bindings can bind property values, lists, or an item in a tuple between
the source and target. Bindings work using the Observable events and subsequently are
implemented via Events.

Bindings can optionally make value conversions between the source and target. For instance,
a binding between a float property and a user interface text field will need to convert from
float to string and back. Converters between value and strings are included for integer, float,
percentage, check state, and UUID to strings.

Geometry
========
Classes for integer and float based points, sizes, and rectangles are included. Additional
geometry routines are also included, for instance: line midpoint.

Persistence
===========
The PersistentObject based class defines a basic structure for storing objects and their
relationship to each other into a persistent storage context. PersistentObjects can store
basic properties, single objects (to-one relationship) and lists of objects (to-many
relationship). Subclasses must strictly notify the PersistentObject of changes to their
persistent data and follow certain guidelines. Doing so allows the object to be stored
persistently and restored from persistent storage.

Properties in the PersistentObject can have validators, converters, change notifications, and
more. Items and relationships have change notifications and more.

The PersistentStorageContext defines an interfaces which manages a collection of PersistentObjects.
It must be able to store a simple dict structure for properties, items, and lists.

Process, ThreadPool
===================
Process defines classes to facilitate a threaded queue, which executes its items serially, and
thread set which executes the most recent item in the set.

ThreadPool defines a threaded dispatcher with the ability to limit dispatch frequency and a thread
pool with the ability to execute explicitly without threads for testing.

Publish and Subscribe
=====================
Publish and subscribe implements a basic publish and subscribe mechanism. It is should be
considered experimental and is not recommended for use.

Reference Counting
==================
The ReferenceCounted base class provides an explicitly reference counted object that is unique
from regular Python reference counting in that it provides precise control of when the reference
is acquired and released. The about_to_delete method is called when reference count reaches zero.

Stream
======
The Stream classes provide a threaded stream of values that can be controlled using standard
reactive operators such as sample, debounce, and combine. In addition, a FutureValue is provided
to provide delayed evaluation. The stream source is an Event named value_stream and the source
object must provide both the value_stream and a value property.

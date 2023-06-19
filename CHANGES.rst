Changelog (nionutils)
=====================

0.4.7 (2023-06-19)
------------------
- Add explicit support for Python 3.11; drop support for Python 3.8.
- Add an auditing capability for performance auditing.
- Add ability to add/remove streams from CombineLatestStream.
- Add ability to display datetime in local time and with format in DateTime converter.
- Add ValuesToIndexConverter.

0.4.6 (2022-11-04)
------------------
- Minor maintenance.

0.4.5 (2022-09-13)
------------------
- Add minor Color method to get RGB values.
- Add DateTime utilities (utcnow for Windows, strictly increasing).

0.4.4 (2022-07-25)
------------------
- Add a Color utility class.
- Fix issues with FloatToScaledIntegerConverter when min/max are invalid.
- Fix possible race condition in thread pool.

0.4.3 (2022-05-28)
------------------
- Improve convert_back method of IntegerToStringConverter for fuzzy conversion.

0.4.2 (2022-02-18)
------------------
- Ensure component prioritization works.
- Fix top level namespace.

0.4.1 (2021-12-13)
------------------
- Minor typing and return type issues.

0.4.0 (2021-11-10)
------------------
- Eliminate need to call close methods on models, streams, listeners, etc.
- Drop support for Python 3.7, add support for Python 3.10.
- Enable strict typing.
- Remove unused ConcatStream.
- Make ReferenceCounted work with Python references, not explicit ref count.
- Add useful Geometry functions: empty_rect, int_rect, as_tuple.
- Remove unused/deprecated PersistentObject.
- Add property changed property model for monitoring observables.
- Change Recorder to allow customer logger.
- Change ThreadPool to be no-close.
- Fix issue in single SingleItemDispatcher so it actually delays.
- Change SingleItemDispatcher to be no-close.
- Extend sync processes function to cancel outstanding async functions.
- Add experimental stream, value change, and reactor functions.
- Add method to sync but not close event loop.
- Add a single item dispatcher to thread pool.
- Deprecate ListBinding class.

0.3.26 (2021-03-12)
-------------------
- Add select forward/backward methods to IndexedSelection.

0.3.25 (2021-02-02)
-------------------
- Add None and fuzzy options to int converter.

0.3.24 (2020-12-07)
-------------------
- Fix issue updating selection on master instead of filtered items.
- Add ListPropertyModel to treat a list like a single property.

0.3.23 (2020-11-06)
-------------------
- Change list model to more efficiently send change events.
- Change selection to (optionally) fire changed messages when adjusting indexes.

0.3.22 (2020-10-06)
-------------------
- Fix property binding inconsistency.

0.3.21 (2020-08-31)
-------------------
- Fix issue with stream calling stale function.
- Filtered lists no longer access their container's master items when closing.
- Add rotate methods to FloatPoint and FloatSize.
- Improve LogTicker. Add support for major and minor ticks.
- Fix case of extending selection with no anchor.
- Add separate LogTicker class. Renamed old Ticker to LinearTicker. Add base Ticker class.
- Add date time to string converter.
- Extend PropertyChangedEventStream to optionally take an input stream rather than direct object.
- Add added/discarded notifications to Observable for set-like behavior.
- Add a pathlib.Path converter.
- Improve performance of filtered list models.
- Add Registry function to send registry events to existing components. Useful for initialization.
- Add geometry rectangle functions for intersect and union.
- Add geometry functions to convert from int to float versions.

0.3.20 (2020-01-28)
-------------------
- Add various geometry functions; facilitate geometry objects conversions to tuples.
- Add Process.close_event_loop for standardized way of closing event loops.
- Improve geometry comparisons so handle other being None.

0.3.19 (2019-06-27)
-------------------
- Add method to clear TaskQueue.
- Make event listeners context manager aware.
- Improve stack traceback during events (fire, listen, handler).
- Add auto-close (based on weak refs) and tracing (debugging) to Event objects.

0.3.18 (2019-03-11)
-------------------
- Ensure FuncStreamValueModel handles threading properly.

0.3.17 (2019-02-27)
-------------------
- Add ConcatStream and PropertyChangedEventStream.
- Add standardized [notify] item_content_changed event to Observable.
- Make item_changed_event optional for items within FilteredListModel.
- Add floordiv operator to IntSize.

0.3.16 (2018-12-11)
-------------------
- Change list model text filter to use straight text rather than regular expressions.

0.3.15 (2018-11-13)
-------------------
- Allow recorder object to be closed.
- Improve release of objects when closing MappedListModel.
- Add close method to ListModel for consistency.
- Allow persistent objects to delay writes and handle external data.
- Allow persistent relationships to define storage key.
- Extend Registry to allow registering same component with additional component types.

0.3.14 (2018-09-13)
-------------------
- Allow default values in persistent factory callback.

0.3.13 (2018-09-11)
-------------------
- Allow persistent items to be hidden (like properties).
- Allow persistent interface to use get_properties instead of properties attribute when saving.
- Allow FilteredListModel to have separate master/item property names.

0.3.12 (2018-07-23)
-------------------
- Fix bug where unregistered objects were not reported correctly.
- Add model changed event to structured model to monitor deep changes.

0.3.11 (2018-06-25)
-------------------
- Improve str conversion in Geometry classes (include x/y).
- Add a get_component method to Registry for easier lookup.
- Treat '.' in float numbers as decimal point independent of locale when parsing, leave locale decimal point valid too.

0.3.10 (2018-05-10)
-------------------
- Initial version online.

Changelog (nionutils)
=====================

0.3.21 (UNRELEASED)
-------------------
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

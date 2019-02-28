Changelog (nionutils)
=====================

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

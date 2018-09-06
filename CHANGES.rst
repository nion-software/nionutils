Changelog (niondata)
====================

UNRELEASED
----------

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

# Calendar Tool

Integrates Google Calendar API services, allowing event lists, searches, creations, deletions, edits, and free-time checking.

## Features

- **Today's Events**: List events happening in the current 24-hour UTC window.
- **Search Events**: Find calendar slots using textual content searches.
- **Create / Update / Delete**: Comprehensive REST-like calendar operations.
- **Free Time Finder**: Compares lists of events against boundaries and finds free periods of custom duration.

## Endpoints

- `GET /calendar/today`: Get current day's events.
- `GET /calendar/search?q={query}`: Search event entries.
- `POST /calendar/create`: Schedule new event.
- `PUT /calendar/update?event_id={id}`: Modify scheduled event attributes.
- `DELETE /calendar/delete?event_id={id}`: Remove meeting from calendar.
- `GET /calendar/free-slots`: Search available times between bounds.

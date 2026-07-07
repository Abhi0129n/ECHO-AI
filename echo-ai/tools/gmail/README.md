# Gmail Tool

Integrates Google Gmail client services, allowing authentication, email reading, drafting, sending, replying, and attachment downloading.

## Features

- **OAuth Authentication**: Automatically checks and refreshes standard token files under `config/`.
- **Read Unread**: Get incoming unread emails as summaries.
- **Search Emails**: Query matching messages via Google search query parameters.
- **Email Details**: Get a structured view of bodies, attachments, headers, and thread keys.
- **Send & Reply**: Supports plain-text messages along with binary attachments mapping.
- **Trash & Archive**: Remove or strip inbox labels directly.

## Endpoints

- `GET /gmail/unread`: List latest unread messages.
- `GET /gmail/search?q={query}`: Search emails.
- `GET /gmail/message/{message_id}`: Inspect complete message.
- `POST /gmail/send`: Compose and dispatch new email.
- `POST /gmail/reply?message_id={id}`: Reply in active thread.
- `GET /gmail/attachments`: Download attachment contents.
- `DELETE /gmail/message/{message_id}`: Trash message.

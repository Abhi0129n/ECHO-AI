# Browser Tool

Provides simple web scraping, link/image extraction, DuckDuckGo search queries, and remote file downloads.

## Features

- **Google (DuckDuckGo) Search**: Fetch search page results without requiring high-footprint webdriver clients.
- **Read Page**: Extract semantic text, tags, embedded links, and images.
- **Download PDF**: Save remote document files locally.

## Endpoints

- `GET /browser/search?q={query}`: Search DuckDuckGo.
- `GET /browser/read?url={url}`: Scrape web page details.
- `POST /browser/download?url={url}`: Download remote resource.

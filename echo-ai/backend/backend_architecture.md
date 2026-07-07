    # Backend Architecture

| Folder | Purpose |
| --- | --- |
| main.py | Starts the FastAPI application and registers routers |
| routers | Defines API endpoints and routes requests |
| services | Contains the business logic and interacts with tools/APIs |
| core | Shared configuration, logging, database setup, authentication |
| models | Database models (SQLAlchemy) |
| schemas | Request and response validation (Pydantic) |
| utils | Reusable helper functions |

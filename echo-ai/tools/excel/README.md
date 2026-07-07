# Excel Tool

Provides spreadsheet creation, cell read/write, row/column appending, and data extraction.

## Features

- **Create Workbook**: Create new `.xlsx` files with customizable sheet names.
- **Open Workbook**: Inspect sheet names and the active sheet.
- **Write Cell**: Update a cell's value (e.g. `A1`).
- **Read Cell**: Get a cell's value.
- **Append Row / Column**: Add linear data structure to a specific sheet.
- **Read Sheet**: Retrieve all rows and columns as structured tables.

## Endpoints

- `POST /excel/create`: Initialize new spreadsheet.
- `GET /excel/open`: Load sheet properties.
- `POST /excel/write`: Write cell values.
- `GET /excel/read`: Read cell values.
- `POST /excel/append`: Append rows to a sheet.
- `POST /excel/save`: Save workbook modifications.

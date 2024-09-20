# python-baserow-simple

This is a simple baserow API wrapper, that mainly does two things:

- return rows with column names and selections with their labels
- easier batch-updates accepting both existing and new rows

## Install it from PyPI

```bash
pip install python_baserow_simple
```

## Usage

Import the library and provide an [Baserow API
token](https://baserow.io/user-docs/personal-api-tokens) with sufficient privileges.

```py
from python_baserow_simple import BaserowApi

api = BaserowApi(database_url="URL TO BASEROW DB", token="BASEROW TOKEN")

# getting data
table_data = api.get_data(table_id="<TABLE ID>")
for entry_id, entry_data in table_data.items():
    ...


# updating entries for a table with a column named 'Name' accepting text
data = {
    "Name": "Hello World",
}
api.add_data("<TABLE ID>", data, row_id=<ROW ID>)

# multiple entries can be updated at the same time
entries = [
    {
        "id": None,  # this will create a new row
        "Name": "AAA",
    },
    {
        "id": 2,  # this will update row with baserow id 2
        "Name": "BBB",
    },
]
api.add_data_batch("<TABLE_ID>", entries)
```

## Development

Read the [CONTRIBUTING.md](CONTRIBUTING.md) file.

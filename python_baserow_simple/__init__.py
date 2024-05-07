from copy import deepcopy
from typing import Any, Dict

import requests


def load_token(token_path):
    with open(token_path) as tokenfile:
        token = tokenfile.readline().strip()
    return token


def format_value(raw_value, field_info):
    if field_info["type"] == "single_select":
        if isinstance(raw_value, dict):
            return raw_value["value"]
        elif raw_value is None:
            return raw_value
        raise RuntimeError(f"malformed single_select {raw_value}")
    elif field_info["type"] == "multiple_select":
        if isinstance(raw_value, list):
            return [v["value"] for v in raw_value]
        raise RuntimeError(f"malformed multiple_select {raw_value}")
    elif field_info["type"] == "link_row":
        if isinstance(raw_value, list):
            return [v["id"] for v in raw_value]
        raise RuntimeError(f"malformed link_row {raw_value}")
    else:
        return raw_value


class BaserowApi:
    table_path = "api/database/rows/table"
    fields_path = "api/database/fields/table"

    def __init__(self, database_url: str, token=None, token_path=None):
        self._database_url = database_url
        if token_path:
            self._token = load_token(token_path)
        if token:
            self._token = token
        self._fields: Dict[int, Any] = {}

    def _get_fields(self, table_id):
        get_fields_url = f"{self._database_url}/{self.fields_path}/{table_id}/"
        resp = requests.get(
            get_fields_url,
            headers={"Authorization": f"Token {self._token}"},
        )

        resp.raise_for_status()
        data = resp.json()
        return data

    def _create_row(self, table_id, data):
        create_row_url = f"{self._database_url}/{self.table_path}/{table_id}/?user_field_names=true"  # noqa: E501
        resp = requests.post(
            create_row_url,
            headers={
                "Authorization": f"Token {self._token}",
                "Content-Type": "application/json",
            },
            json=data,
        )
        resp.raise_for_status()
        resp_data = resp.json()
        if "id" in resp_data:
            return resp_data["id"]
        else:
            raise RuntimeError(f"Malformed response {resp_data}")

    def _update_row(self, table_id, row_id, data):
        update_row_url = f"{self._database_url}/{self.table_path}/{table_id}/{row_id}/?user_field_names=true"  # noqa: E501
        resp = requests.patch(
            update_row_url,
            headers={
                "Authorization": f"Token {self._token}",
                "Content-Type": "application/json",
            },
            json=data,
        )
        resp.raise_for_status()

    def _update_rows(self, table_id, datas):
        update_rows_url = f"{self._database_url}/{self.table_path}/{table_id}/batch/?user_field_names=true"  # noqa: E501
        resp = requests.patch(
            update_rows_url,
            headers={
                "Authorization": f"Token {self._token}",
                "Content-Type": "application/json",
            },
            json={"items": datas},
        )
        resp.raise_for_status()
        data = resp.json()
        ids = [e["id"] for e in data["items"]]
        return ids

    def _create_rows(self, table_id, datas):
        create_rows_url = f"{self._database_url}/{self.table_path}/{table_id}/batch/?user_field_names=true"  # noqa: E501
        resp = requests.post(
            create_rows_url,
            headers={
                "Authorization": f"Token {self._token}",
                "Content-Type": "application/json",
            },
            json={"items": datas},
        )
        resp.raise_for_status()
        data = resp.json()
        ids = [e["id"] for e in data["items"]]
        return ids

    def _convert_selects(self, data, fields):
        data_conv = deepcopy(data)

        def convert_option(v, opts):
            if isinstance(v, int):
                return v

            for opt in opts:
                if opt["value"] == v:
                    return opt["id"]
            raise RuntimeError(f"Could not convert {v} to any of {opts}")

        for field in fields:
            if not field["read_only"] and field["name"] in data_conv:
                cur_value = data_conv[field["name"]]

                if cur_value is None or cur_value == []:
                    continue

                if field["type"] == "single_select":
                    data_conv[field["name"]] = convert_option(
                        cur_value, field["select_options"]
                    )

                elif field["type"] == "multiple_select":
                    new_value = []
                    for single_value in cur_value:
                        conv_value = convert_option(
                            single_value, field["select_options"]
                        )
                        new_value.append(conv_value)
                    data_conv[field["name"]] = new_value
        return data_conv

    def _get_data(self, url, paginated=True):
        resp = requests.get(
            url, headers={"Authorization": f"Token {self._token}"}
        )
        data = resp.json()

        if paginated:
            if "results" not in data:
                raise RuntimeError(f"Could not get data from {url}")

            if data["next"]:
                return data["results"] + self._get_data(data["next"])
            return data["results"]
        else:
            return data

    def get_fields(self, table_id):
        if table_id not in self._fields:
            self._fields[table_id] = self._get_fields(table_id)
        return self._fields[table_id]

    def writable_fields(self, table_id):
        fields = self.get_fields(table_id)
        writable_fields = [field for field in fields if not field["read_only"]]
        return writable_fields

    def get_data(self, table_id, writable_only=True):
        """Get all data in a table.

        writable_only - Only return fields which can be written to. This
        excludes all formula and computed fields.
        """
        if writable_only:
            fields = self.writable_fields(table_id)
        else:
            fields = self.get_fields(table_id)
        names = {f["name"]: f for f in fields}
        get_data_url = f"{self._database_url}/{self.table_path}/{table_id}/?user_field_names=true"  # noqa: E501
        data = self._get_data(get_data_url)

        writable_data = {
            d["id"]: {
                k: format_value(v, names[k])
                for k, v in d.items()
                if k in names
            }
            for d in data
        }

        return writable_data

    def get_entry(self, table_id, entry_id, linked=False, seen_tables=None):
        get_entry_url = f"{self._database_url}/{self.table_path}/{table_id}/{entry_id}/?user_field_names=true"  # noqa: E501
        data = self._get_data(get_entry_url, paginated=False)
        fields = self.get_fields(table_id)
        names = {f["name"]: f for f in fields}
        formatted_data = {k: format_value(v, names[k]) for k, v in data.items() if k in names}

        seen_tables_next = seen_tables or []
        seen_tables_next.append(table_id)

        # fully hydrate with linked data
        if linked:
            link_fields = [f for f in fields if f["type"] == "link_row"]
            for field in link_fields:
                linked_table_id = field["link_row_table_id"]
                if not seen_tables or linked_table_id not in seen_tables:
                    if ids := data.get(field["name"]):
                        formatted_data[field["name"]] = [
                            self.get_entry(linked_table_id, e_id["id"], linked=False, seen_tables=seen_tables_next)for e_id in ids
                        ]

        return formatted_data

    def add_data(self, table_id, data, row_id=None) -> int:
        fields = self.get_fields(table_id)
        data_conv = self._convert_selects(data, fields)
        if row_id:
            self._update_row(table_id, row_id, data_conv)
        else:
            row_id = self._create_row(table_id, data_conv)

        return row_id

    def add_data_batch(self, table_id, entries):
        """Add multiple entries."""
        entries_update = []
        entries_new = []
        for entry in entries:
            if entry.get("id") is not None:
                entries_update.append(entry)
            else:
                entries_new.append(entry)

        errors = []
        if entries_new:
            try:
                self._create_rows(table_id, entries_new)
            except requests.HTTPError as err:
                errors.append(err.response.text)
        if entries_update:
            try:
                self._update_rows(table_id, entries_update)
            except requests.HTTPError as err:
                errors.append(err.response.text)
        return errors

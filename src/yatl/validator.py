import json


class Response:
    def __init__(self, status_code, json_data):
        self.status_code = status_code
        self.json_data = json_data


class ResponseValidator:
    def __init__(self, response: Response, expect_spec: dict):
        self.response = response
        self.expect_spec = expect_spec

    def check_expectations(self):
        expected_status = self.expect_spec.get("status")
        if expected_status is not None and self.response.status_code != expected_status:
            raise AssertionError(
                f"Expected status {expected_status}, got {self.response.status_code}"
            )

        expected_json = self.expect_spec.get("json")
        if expected_json is not None:
            try:
                resp_json = self.response.json()
            except json.JSONDecodeError:
                raise AssertionError("Response is not JSON, but JSON was expected")

            for key, value in expected_json.items():
                if key not in resp_json:
                    raise AssertionError(f"Key '{key}' is missing in response")
                if resp_json[key] != value:
                    raise AssertionError(
                        f"For key '{key}' expected '{value}', got '{resp_json[key]}'"
                    )

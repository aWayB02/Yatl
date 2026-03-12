# YATL (Yet Another Testing Language) - Usage Guide

YATL is a lightweight testing framework designed for API testing using YAML-based test specifications. It supports HTTP requests, response validation, data extraction, and templating with Jinja2.

## Table of Contents

1. [Getting Started](#getting-started)
2. [Test Structure](#test-structure)
3. [HTTP Request Specification](#http-request-specification)
4. [Response Validation](#response-validation)
5. [Data Extraction](#data-extraction)
6. [Templating with Jinja2](#templating-with-jinja2)
7. [Running Tests](#running-tests)
8. [Examples](#examples)
9. [Advanced Features](#advanced-features)

## Getting Started

## Test Structure

A YATL test file is a YAML document with the following top-level keys:

- `name` (optional): Descriptive name of the test suite.
- `base_url` (optional): Base URL for all requests in the test.
- `steps`: List of test steps, each representing an HTTP request and its assertions.

Example:

```yaml
name: User API Test
base_url: http://localhost:8000

steps:
  - name: Create a user
    request:
      method: POST
      url: /users
      body:
        json:
          id: 1
          name: John Doe
          email: john@example.com
    expect:
      status: 200
```

## HTTP Request Specification

Each step contains a `request` object with the following fields:

- `method` (required): HTTP method (GET, POST, PUT, DELETE, etc.). Defaults to GET.
- `url` (required): Endpoint path, relative to `base_url`.
- `headers` (optional): Dictionary of HTTP headers.
- `params` (optional): Query parameters as key-value pairs.
- `cookies` (optional): Cookies as key-value pairs.
- `body` (optional): Request body, which can be JSON, XML, plain text, or form data.

### Body Types

YATL supports multiple body formats:

#### JSON

```yaml
body:
  json:
    key: value
    nested:
      field: 123
```

The `Content-Type` header will automatically be set to `application/json` if not provided.

#### XML

```yaml
body:
  xml: |
    <note>
      <to>User</to>
      <from>YATL</from>
    </note>
```

`Content-Type` will be set to `application/xml`.

#### Plain Text

```yaml
body:
  text: "Hello, world!"
```

`Content-Type` will be set to `text/plain`.

#### Form Data

```yaml
body:
  form:
    username: john
    password: secret
```

`Content-Type` will be set to `application/x-www-form-urlencoded`.

#### Multipart Files

```yaml
body:
  files:
    file: /path/to/file.txt
```

### Timeout

You can specify a request timeout (in seconds):

```yaml
request:
  timeout: 30
```

## Response Validation

After sending a request, you can validate the response using the `expect` block.

### Status Code

```yaml
expect:
  status: 200
```

### Headers

```yaml
expect:
  headers:
    content-type: application/json
    cache-control: no-cache
```

Header validation is case-insensitive and ignores parameters (e.g., `charset`).

### Body

You can validate JSON, XML, or plain text bodies.

#### JSON Body Validation

```yaml
expect:
  body:
    json:
      id: 1
      name: John Doe
```

Nested objects are supported. The validator checks exact equality.

#### XML Body Validation

```yaml
expect:
  body:
    xml:
      "/note/to": "User"
      "/note/from": "YATL"
```

The keys are XPath expressions, and values are expected text content of the matched element.

#### Plain Text Body Validation

```yaml
expect:
  body:
    text: "Hello, world!"
```

The validator checks if the expected substring is present in the response text.

## Data Extraction

You can extract values from a response and store them in the test context for use in subsequent steps.

Use the `extract` block:

```yaml
extract:
  user_id: id
  token: access_token
```

The extraction mechanism depends on the response content type.

### JSON Extraction

For JSON responses, you can specify a path (key) in the JSON object. If the path is `null`, the key name is used as the path.

Example: If the response is `{"id": 123, "access_token": "abc"}`, the above extraction will store `user_id = 123` and `token = "abc"`.

### XML Extraction

For XML responses, specify XPath expressions:

```yaml
extract:
  note_to: "/note/to"
```

### Plain Text Extraction

For plain text, you can use regular expressions:

```yaml
extract:
  match: "\d+"
```

## Templating with Jinja2

YATL uses Jinja2 templating to dynamically generate values in requests, expectations, and extractions. The context includes:

- Variables extracted from previous steps.
- The `base_url` and test name.
- Any custom variables defined in the test.

### Usage in YAML

Wrap templated strings in double curly braces:

```yaml
request:
  url: /users/{{ user_id }}
  headers:
    Authorization: Bearer {{ token }}
```

### Example

```yaml
steps:
  - name: Login
    request:
      method: POST
      url: /login
      body:
        json:
          username: admin
          password: secret
    extract:
      token: access_token
  - name: Get profile
    request:
      method: GET
      url: /profile
      headers:
        Authorization: Bearer {{ token }}
```

## Running Tests

### Command Line

The simplest way to run tests is via the built-in runner:

```bash
python -m src.yatl.run
```

This will recursively search for files ending with `.test.yaml` or `.test.yml` in the current directory and run them.

### Programmatic Usage

You can also integrate YATL into your Python scripts:

```python
from yatl.run import Runner
from yatl.extractor import DataExtractor
from yatl.render import TemplateRenderer

runner = Runner(DataExtractor(), TemplateRenderer())
runner.run_test("path/to/test.yaml")
```

## Examples

### JSON API Test

```yaml
name: JSON API Example
base_url: https://api.example.com

steps:
  - name: Create item
    request:
      method: POST
      url: /items
      body:
        json:
          name: "Widget"
          price: 9.99
    expect:
      status: 201
      body:
        json:
          success: true
    extract:
      item_id: id

  - name: Retrieve item
    request:
      method: GET
      url: /items/{{ item_id }}
    expect:
      status: 200
      body:
        json:
          name: "Widget"
          price: 9.99
```

### XML API Test

```yaml
name: XML Service Test
base_url: http://localhost:8000

steps:
  - name: Get XML
    request:
      method: GET
      url: /xml
    expect:
      status: 200
      headers:
        content-type: application/xml
      body:
        xml:
          "/note/to": "User"
          "/note/from": "YATL"
```

### Plain Text Test

```yaml
name: Text Endpoint
base_url: http://localhost:8000

steps:
  - name: Get greeting
    request:
      method: GET
      url: /text
    expect:
      status: 200
      body:
        text: "Hello"
```

## Advanced Features

### Conditional Steps

Currently, YATL does not support conditional steps natively, but you can achieve conditional logic by writing separate test files.

### Retry Logic

Not built-in; consider using external tools like `pytest` with retry decorators.

### Environment Variables

You can use environment variables in templates via Jinja2's `os.environ`:

```yaml
request:
  url: {{ os.environ.get("API_BASE_URL") }}/endpoint
```

### Custom Validators

Extend the `ResponseValidator` class to add custom validation logic.

## Troubleshooting

### Common Errors

- **Header mismatch**: Ensure header values are normalized (e.g., `content-type` may include charset).
- **JSON extraction fails**: Verify the path exists in the response.
- **Templating errors**: Check that variables are defined in the context.

### Debugging

Enable verbose logging by modifying `run.py` or using the `print` statements already present.

## Contributing

Contributions are welcome! Please see the repository's contributing guidelines.

## License

This project is licensed under the MIT License.
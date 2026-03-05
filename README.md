## Yatl - Yet Another Testing Language

Yatl is a simple testing language that allows you to write tests in YAML. 
You can using this framework to write tests for your applications and integration to CI/CD.

## Installation

```bash
pip install yatl
```

## Usage

To use Yatl, create a test file in YAML format.
The test file should contain the following fields:

```yaml
- name: the name of the test
  base_url: the base url to be used
  variables: the global variables to be used in the test
- steps: a list of steps to be executed
    - name: the name of the step
      request: the request to be made
        url: the url to be requested
        method: the http method to be used
        headers: the headers to be used
        body: the body to be sent
        params: the params to be used
      expect: the expected response
        status: the expected status code
        json: the expected json response
      extract: the variables to be extracted
```

File name should be suffix **.test.yaml**

for example, create **example.test.yaml** and write the following code:

```yaml
name: first test

steps:
  - name: first step
    request:
      url: https://google.com
      method: GET
    expect:
      status: 200
```

To run the test, use the following command:

```bash
make run_tests
```
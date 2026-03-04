## Модуль `parser.py` реализует парсер Y-тестов для HTTP-заросов с поддержкой шаблонов Jinja2, извлечением данных и проверкой ожиданий. Он является частью фреймворка YATL (Yet Another Test Language).

Выполнение происходит следующим образом:

    - Резолвит все поля запроса с помощью контекста.
    - Отправляет HTTP-запрос.
    - Проверяет ожидания (expect).
    - Извлекает данные (extract) и добавляет их в контекст.
    - Возвращает обновлённый контекст.

## Основные функции

### `render_data(data, context)`

Рекурсивно обходит структуру данных (словари, списки, строки) и заменяет все строки вида `{{...}}` на значения из контекста с помощью Jinja2.

**Параметры:**
- `data` — любой тип данных (строка, словарь, список, число, булево значение, None).
- `context` — словарь с переменными, доступными для подстановки.

**Возвращает:** данные того же типа, где все строки, содержащие шаблоны Jinja2, заменены на результат рендеринга.

**Пример:**
```python
context = {"user_id": 42}
data = {"url": "/users/{{user_id}}", "method": "GET"}
result = render_data(data, context)
# result = {"url": "/users/42", "method": "GET"}
```

### `extract_data(response, extract_spec)`

Извлекает данные из HTTP-ответа согласно спецификации `extract`.

**Параметры:**
- `response` — объект ответа `requests.Response`.
- `extract_spec` — словарь, где ключ — имя переменной, а значение — путь к данным в ответе (или `None` для простого извлечения по имени ключа).

**Возвращает:** словарь извлечённых данных.

**Пример:**
```yaml
extract:
  user_id: null   # извлечёт поле "user_id" из JSON-ответа
  email: "user.email"  # в будущем поддержка JSONPath
```

### `check_expectations(response, expect_spec)`

Проверяет ожидания: статус ответа и частичное совпадение JSON.

**Параметры:**
- `response` — объект ответа `requests.Response`.
- `expect_spec` — словарь с ожиданиями:
  - `status` (опционально) — ожидаемый HTTP-статус.
  - `json` (опционально) — словарь, который должен частично присутствовать в JSON-ответе.

**Исключения:** `AssertionError`, если ожидания не выполнены.

### `run_step(step, context)`

Выполняет один шаг теста:
1. Резолвит все поля шага с помощью `render_data`.
2. Отправляет HTTP-запрос.
3. Проверяет ожидания через `check_expectations`.
4. Извлекает данные через `extract_data` и обновляет контекст.

**Параметры:**
- `step` — словарь, описывающий шаг (см. формат YAML).
- `context` — текущий контекст переменных.

**Возвращает:** обновлённый контекст.

### `run_test(yaml_path)`

Загружает YAML-файл и выполняет все шаги теста.

**Параметры:**
- `yaml_path` — путь к YAML-файлу с описанием теста.

**Логика:**
1. Загружает YAML.
2. Инициализирует контекст из глобальных полей (например, `base_url`).
3. Последовательно выполняет каждый шаг из `steps`.
4. Выводит прогресс в консоль.

## Формат YAML-теста

Пример теста (`tests/example.test.yaml`):

```yaml
name: Create and check user
base_url: http://127.0.0.1:8000/
user_id_not_found: 1234567890

steps:
  - name: Create user
    request:
      method: POST
      url: /users
      json:
        name: "Ivan"
        email: "ivan@example.com"
    expect:
      status: 200
    extract:
      user_id: null

  - name: Get user
    request:
      method: GET
      url: "/users/{{user_id}}"
      timeout: 10
    expect:
      status: 200
      json:
        name: "Ivan"
        email: "ivan@example.com"

  - name: Delete existing user
    request:
      method: DELETE
      url: "/users/{{user_id}}"
    expect:
      status: 200
      json:
        status: User deleted

  - name: Delete non-existing user
    request:
      method: DELETE
      url: "/users/{{user_id_not_found}}"
    expect:
      status: 404
      json:
        detail: User not found
```

## Использование

Запуск теста из командной строки:

```bash
python -m src.yatl.parser tests/example.test.yaml
```

Или программно:

```python
from src.yatl.parser import run_test
run_test("path/to/test.yaml")
```

## Зависимости

- `PyYAML` — загрузка YAML.
- `requests` — отправка HTTP-запросов.
- `Jinja2` — рендеринг шаблонов.

Установите их через `poetry install` или `pip install -r requirements.txt`.

## Примечания

- Это временная документация, актуальная на март 2026 года.
- Модуль находится в активной разработке, возможны изменения.
- Для расширенных возможностей (JSONPath, кастомные валидации) планируется доработка.

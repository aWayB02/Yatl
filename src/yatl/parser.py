import yaml
import requests
from jinja2 import Template
import json


# ---------- Вспомогательные функции ----------
def render_data(data, context):
    """
    Рекурсивно обходит структуру данных (словари, списки, строки)
    и заменяет все строки вида {{...}} на значения из context.
    """
    if isinstance(data, str):
        # Любая строка считается потенциальным шаблоном
        return Template(data).render(context)
    elif isinstance(data, dict):
        return {key: render_data(value, context) for key, value in data.items()}
    elif isinstance(data, list):
        return [render_data(item, context) for item in data]
    else:
        # Числа, булевы значения, None — не обрабатываем
        return data


def extract_data(response, extract_spec):
    """
    Извлекает данные из ответа согласно спецификации extract.
    Поддерживается простой синтаксис: если значение None, то берётся поле с таким же именем.
    Можно расширить для поддержки JSONPath (например, 'user_id: $.data.id').
    """
    extracted = {}
    if response.headers.get("content-type") == "application/json":
        resp_json = response.json()
    else:
        resp_json = None

    for key, path in extract_spec.items():
        if path is None:
            if resp_json and key in resp_json:
                extracted[key] = resp_json[key]
            else:
                raise ValueError(f"Поле '{key}' не найдено в JSON-ответе")
        else:
            # Здесь можно реализовать JSONPath, но пока заглушка
            # Для примера просто берём по ключу, если path строка
            if resp_json and path in resp_json:
                extracted[key] = resp_json[path]
            else:
                raise ValueError(f"Не удалось извлечь '{key}' по пути '{path}'")
    return extracted


def check_expectations(response, expect_spec):
    """
    Проверяет ожидания: статус и совпадение JSON.
    """
    # Проверка статуса
    expected_status = expect_spec.get("status")
    if expected_status is not None and response.status_code != expected_status:
        raise AssertionError(
            f"Ожидался статус {expected_status}, получен {response.status_code}"
        )

    # Проверка JSON (частичное совпадение)
    expected_json = expect_spec.get("json")
    if expected_json is not None:
        try:
            resp_json = response.json()
        except json.JSONDecodeError:
            raise AssertionError("Ответ не является JSON, но ожидался JSON")

        # Простейшая проверка: все ключи из expected_json должны присутствовать и совпадать
        for key, value in expected_json.items():
            if key not in resp_json:
                raise AssertionError(f"В ответе отсутствует ключ '{key}'")
            if resp_json[key] != value:
                raise AssertionError(
                    f"По ключу '{key}' ожидалось '{value}', получено '{resp_json[key]}'"
                )


def run_step(step, context):
    """
    Выполняет один шаг:
    1. Резолвит все поля запроса с помощью контекста.
    2. Отправляет HTTP-запрос.
    3. Проверяет ожидания (expect).
    4. Извлекает данные (extract) и добавляет их в контекст.
    Возвращает обновлённый контекст.
    """
    # Резолвинг данных шага (включая request и всё остальное)
    resolved_step = render_data(step, context)

    request_data = resolved_step["request"]
    method = request_data.get("method", "GET").upper()
    url = request_data["url"]
    timeout = request_data.get("timeout", None)
    if not url.startswith(("http://", "https://")):
        base_url = context.get("base_url", "")
        url = base_url.rstrip("/") + "/" + url.lstrip("/")

    headers = request_data.get("headers", {})
    json_body = request_data.get("json")
    params = request_data.get("params")

    # Выполняем запрос
    response = requests.request(
        method=method,
        url=url,
        headers=headers,
        json=json_body,
        params=params,
        timeout=timeout,
    )

    # Проверка ожиданий
    if "expect" in resolved_step:
        check_expectations(response, resolved_step["expect"])

    # Извлечение данных
    if "extract" in resolved_step:
        extracted = extract_data(response, resolved_step["extract"])
        context.update(extracted)

    return context


def run_test(yaml_path):
    """
    Загружает YAML-файл и выполняет все шаги.
    """
    with open(yaml_path, "r", encoding="utf-8") as f:
        test_spec = yaml.safe_load(f)

    def create_context(test_spec):
        context = {}
        for k, v in test_spec.items():
            if k == "steps":
                return context
            context[k] = v
        return context

    # Инициализация контекста: base_url и любые глобальные переменные
    context = create_context(test_spec)

    print(f"Запуск теста: {test_spec.get('name', 'Без имени')}")
    steps = test_spec.get("steps", [])
    for i, step in enumerate(steps, start=1):
        print(f"  Шаг {i}: {step.get('name', 'Без имени')}")
        context = run_step(step, context)

    print("Тест успешно завершён!")


if __name__ == "__main__":
    run_test("tests/unit.test.yaml")

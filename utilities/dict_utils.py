import json


def get_value_or_fail(data: dict, key: str) -> str:
    value = data.get(key)
    if not value:
        raise Exception(f'Could not extract {key}')
    else:
        return value


def print_object(obj: object) -> None:
    print(json.dumps(vars(obj), default=lambda x: x.__dict__))

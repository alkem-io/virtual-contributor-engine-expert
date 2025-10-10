from pydantic import BaseModel
from typing import Any, Dict
from json_schema_to_pydantic import create_model


def _transform_schema(obj: Any) -> None:
    """In-place transform of the loaded JSON structure.

    Operations (single pass, recursive):
    - If an object has a 'properties' key whose value is a LIST, convert it to a
      DICT keyed by each property's 'name'. Remove the 'name' field from each.
    - For each property (or any dict) having 'optional': true and a string 'type',
      change 'type' -> [original_type, "null"]. Remove 'optional'.
    - If 'optional' exists but is not True, simply remove it.
    - Recurse into nested dicts and lists.
    """
    if isinstance(obj, dict):
        # First convert list-based properties to dict
        if isinstance(obj.get("properties"), list):
            new_props: Dict[str, Any] = {}
            for item in obj["properties"]:  # type: ignore[index]
                if not isinstance(item, dict):
                    continue
                name = item.get("name")
                if not isinstance(name, str):
                    continue  # Skip malformed entries
                # Prepare property copy
                prop_copy = dict(item)
                prop_copy.pop("name", None)
                # Handle optional/type transformation for the property itself
                if prop_copy.get("optional") is True and isinstance(prop_copy.get("type"), str):
                    prop_copy["type"] = [prop_copy["type"], "null"]
                # Remove the optional flag regardless of value
                if "optional" in prop_copy:
                    prop_copy.pop("optional", None)
                new_props[name] = prop_copy
            obj["properties"] = new_props

        # Now handle this dict itself if it has 'optional'
        if "optional" in obj:
            if obj.get("optional") is True and isinstance(obj.get("type"), str):
                obj["type"] = [obj["type"], "null"]
            obj.pop("optional", None)

        # Recurse into 'items' for array types
        type_val = obj.get("type")
        if (
            type_val == "array" or (isinstance(type_val, list) and "array" in type_val)
        ):
            items = obj.get("items")
            if items is None:
                print("WARNING: Array type missing 'items' schema:", obj)
            if items is not None:
                _transform_schema(items)
        # Recurse through remaining values
        for k, v in list(obj.items()):
            _transform_schema(v)

    elif isinstance(obj, list):
        for item in obj:
            _transform_schema(item)


"""Utility to build a Pydantic model from the prompt graph JSON schema-like file.

Steps performed:
1. Load the JSON file (prompt.graph.expert.json) located in the same directory.
2. In a single recursive pass:
   - Convert any 'properties' field that is a LIST of objects with 'name' into
     a DICT keyed by the 'name' (removing the 'name' field from each property value).
   - For any property object that contains 'optional': true and whose 'type' is a
     STRING, convert the 'type' value into a list: [original_type, "null"].
   - Remove every 'optional' field (whether true or false) after processing.
3. Use json_schema_to_pydantic.create_model to generate and return a Pydantic model
   for the "state" portion of the prompt graph (this is the schema-like segment).

The main entry point is the function build_prompt_graph_model().
"""


def parse_json_graph(data: Dict[str, Any]) -> BaseModel:
    _transform_schema(data)
    model_cls = create_model(data, root_schema=data)
    return model_cls


__all__ = ["parse_json_graph"]

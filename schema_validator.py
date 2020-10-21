
plan_cost_shares_schema = {
    "type": "object",
    "properties": {
        "deductible": {"type" : "integer"},
        "_org": {"type" : "string"},
        "copay": {"type" : "integer"},
        "objectId": {"type" : "string"},
        "objectType": {"type" : "string"}
    },
    "required": ["deductible", "_org","copay","objectId","objectType"]
}


linked_service_schema = {
    "type": "object",
    "properties": {
        "_org": {"type" : "string"},
        "name": {"type" : "string"},
        "objectId": {"type" : "string"},
        "objectType": {"type" : "string"}
    },
    "required": ["_org", "name","objectId","objectType"]
}

linked_plan_services_schema = {
    "type": "array",
    "items": {
        "type": "object",
        "properties": {
            "linkedService": linked_service_schema,
            "planserviceCostShares": plan_cost_shares_schema,
            "_org": {"type": "string"},
            "objectId": {"type" : "string"},
            "objectType": {"type" : "string"}
        },
        "required": ["linkedService","planserviceCostShares","_org","objectId","objectType"]
    }
}
main_schema = {
    "type": "object",
    "properties": {
        "planCostShares": plan_cost_shares_schema,
        "linkedPlanServices": linked_plan_services_schema,
        "_org": {"type": "string"},
        "objectId": {"type" : "string"},
        "objectType": {"type" : "string"},
        "planType": {"type": "string"},
        "creationDate": {"type": "string"}
    },
    "required": ["planCostShares","linkedPlanServices","_org", "planType","objectId","objectType","creationDate"]
}

from jsonschema import validate


def validate_schema(data):
    try:
        validate(data,schema=main_schema)
        return True
    except Exception as e:
        print(e)
        return False

def merge_for_patch(old_obj, new_obj):
    if("planCostShares" in new_obj):
        for k,v in new_obj['planCostShares'].items():
            old_obj['planCostShares'][k] = v
    if('linkedPlanServices' in new_obj):
        for item in new_obj['linkedPlanServices']:
            old_obj['linkedPlanServices'].append(item)
    for k,v in new_obj.items():
        if(k not in ['linkedPlanServices','planCostShares']):
            old_obj[k] = v
    return old_obj


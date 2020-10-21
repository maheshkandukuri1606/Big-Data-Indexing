from flask import Flask,request, Response, make_response
import json, uuid
from schema_validator import validate_schema, merge_for_patch
from auth import validate_token
import redis
import producer

r = redis.Redis(host='localhost', port=6379, db=0)

app = Flask(__name__)

def addPlanServiceToData(data):
    for i in data["linkedPlanServices"]:
        i["planserviceCostShares"]["objectType"] = "planservice_membercostshare"
    return data

def nestedObject(data, objectId, es_type="create"):
    obj = {}
    arr = []
    for key,value in data.items():
        if type(value) == type({}):
            obj[key] = nestedObject(value, data["objectId"],es_type)
        elif type(value) == type([]):
            for i in value:
                arr.append(nestedObject(i, data["objectId"],es_type))
            obj[key] = str(arr)
        else:
            obj[key] = str(value)
    if obj:
        data = {"data":obj,"plan_service":{"name":data["objectType"]}}
        if(objectId):
            data['plan_service']['parent'] = objectId
        es_data = {"type":es_type, "data":data}
        producer.produceData(es_data)
    return data['data']['objectType']+"_" + data['data']["objectId"]




def auth_decorator(func):
    def wrapper(*args, **kwargs):
        auth = request.headers.get('Authorization', None)
        if (not auth):
            return "Required Auth Token in Header", 400
        token = auth.split(" ")[1]
        if not validate_token(token):
            resp = make_response({"message": "Invalid Token"})
            return resp, 400
        return func(*args, **kwargs)

    wrapper.__name__ = func.__name__
    return wrapper

@app.route('/plan/<id>', methods=["GET"])
@auth_decorator
def get_plan(id):
    etag_val = r.get("ETag"+id)
    none_match_etag = request.headers.get('If-None-Match', "")
    match_etag = request.headers.get('If-Match', "")
    if(none_match_etag and etag_val and none_match_etag == etag_val.decode("utf-8")):
        return "", 304
    if(match_etag and etag_val and match_etag != etag_val.decode("utf-8")):
        return "", 304
    data = r.get(id)
    if(data):
        u_id = r.get("ETag" + id)
        resp = Response(data)
        resp.headers["ETag"] = u_id.decode("utf-8")
        return resp, 200
    else:
        return make_response({"message":"No Plan found"}), 404


@app.route('/plan', methods=["POST"])
@auth_decorator
def post_plan():
    data = request.get_json()
    if(not validate_schema(data)):
        return "Error while validating schema to the schema", 400
    key = data['objectId']
    if (r.exists(key)):
        return "ObjectId already exists", 409
    addPlanServiceToData(data)
    nestedObject(data,"")
    r.set(key,json.dumps(data))
    u_id = uuid.uuid4().hex
    r.set("ETag"+key, u_id)
    resp = make_response({"message":"Successfully Created Plan : "+key})
    resp.headers["ETag"] = u_id
    return resp, 201






@app.route('/plan/<id>', methods=["PUT"])
@auth_decorator
def put_plan(id):

    data = r.get(id)
    request_data = request.get_json()
    etag_val = r.get("ETag" + id)
    match_etag = request.headers.get('If-Match', "")
    if(match_etag and etag_val and match_etag != etag_val.decode("utf-8")):
        return "Plan has been updated by other user please get latest etag", 409
    if (not validate_schema(request_data)):
        return "Error while validating schema to the schema", 400
    if(data):
        addPlanServiceToData(request_data)
        nestedObject(request_data,"")
        r.set(id, json.dumps(request_data))
        u_id = uuid.uuid4().hex
        r.set("ETag" + id, u_id)
        resp = make_response({"message":"Successfully Updated Plan "+ id})
        resp.headers["ETag"] = u_id
        return resp, 200
    else:
        return make_response({"message":"No Plan found"}), 404

@app.route('/plan/<id>', methods=["PATCH"])
@auth_decorator
def patch_plan(id):
    data = r.get(id)
    request_data = request.get_json()
    etag_val = r.get("ETag" + id)
    match_etag = request.headers.get('If-Match', "")
    if(match_etag and etag_val and match_etag != etag_val.decode("utf-8")):
        return "Plan has been updated by other user please get latest etag", 409
    if(data):
        data = json.loads(data)
        merge_data = merge_for_patch(data,request_data)
        if (not validate_schema(merge_data)):
            return "Error while validating schema to the schema", 400
        addPlanServiceToData(merge_data)
        nestedObject(merge_data,"")
        r.set(id, json.dumps(merge_data))
        u_id = uuid.uuid4().hex
        r.set("ETag" + id, u_id)
        resp = make_response({"message":"Successfully Updated Plan "+ id})
        resp.headers["ETag"] = u_id
        return resp, 200
    else:
        return make_response({"message":"No Plan found"}), 404

@app.route('/plan/<id>', methods=["DELETE"])
@auth_decorator
def delete_plan(id):
    data = r.get(id)
    data = json.loads(data)
    nestedObject(data, "", es_type="delete")
    if(r.delete(id)==1):
        r.delete("ETag"+id)
        return make_response({"message": "Successfully Deleted Plan"}), 200
    else:
        return make_response({"message":"No Plan found"}), 404


if __name__ == '__main__':
    app.run(port=8080)
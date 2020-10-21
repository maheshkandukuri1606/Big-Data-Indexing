from kafka import KafkaConsumer
from json import loads
import logging, requests

def send_data_to_ES(data, child_id, parent_id=None):
    if parent_id:
        url = "http://localhost:9200/planservice/orm/{}?routing={}".format(child_id,parent_id)
    else:
        url = "http://localhost:9200/planservice/orm/{}".format(child_id)
    session = requests.Session()
    session.auth = ("elastic", "changeme")
    session.put(url, json=data)

def delete_data_on_ES(data, child_id, parent_id=None):
    url = 'http://localhost:9200/planservice/_delete_by_query'

    query = {
        "query": {
            "bool": {
                "must": [
                    {
                        "match": {
                            "_id": child_id
                        }
                    }
                ]
            }
        }
    }
    if(parent_id):
        query['query']['bool']['must'].append({"match":{"_routing":parent_id}})
    session = requests.Session()
    session.auth = ("elastic", "changeme")
    resp = session.post(url, json=query)
    print(resp.status_code)

consumer = KafkaConsumer(
    'DemoTopic',
     bootstrap_servers=['localhost:9092'],
     auto_offset_reset='earliest',
     enable_auto_commit=True,
     group_id='my-group',
     value_deserializer=lambda x: loads(x.decode('utf-8')))

for message in consumer:
    data = message.value
    message = data['data']
    print('s')
    if('type' not in data):
        print("no")
        continue
    es_type = data["type"]
    child_id = message['data']['objectId']
    parent_id = message['plan_service'].get("parent",None)
    if(es_type=="create"):
        print(message)
        send_data_to_ES(message,child_id,parent_id)

    elif(es_type=="delete"):
        delete_data_on_ES(message, child_id, parent_id)


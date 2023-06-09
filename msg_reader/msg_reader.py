import oci
import mysql.connector
import json
import base64
import os
from opentelemetry import trace

tracer = trace.get_tracer("get_message.tracer")

service_endpoint = os.environ['SERVICE_ENDPOINT']
queue_id = os.environ['QUEUE_ID']
secret_id = os.environ['SECRET_ID']
host = os.environ['HOST']
user = os.environ['USER']

if 'OCI_RESOURCE_PRINCIPAL_VERSION' in os.environ:
    signer = oci.auth.signers.get_resource_principals_signer()
else:
    signer = oci.auth.signers.InstancePrincipalsSecurityTokenSigner()

queue_client = oci.queue.QueueClient(config={}, signer=signer, service_endpoint=service_endpoint)

def get_text_secret(secret_ocid):
    try:
        client = oci.secrets.SecretsClient(config={}, signer=signer)
        secret_content = client.get_secret_bundle(secret_ocid).data.secret_bundle_content.content.encode('utf-8')
        decrypted_secret_content = base64.b64decode(secret_content).decode("utf-8")
    except Exception as ex:
        print("ERROR: failed to retrieve the secret content", ex, flush=True)
        raise
    return decrypted_secret_content

def mysql_connect(host, user ,pw):
    try:
        mydb = mysql.connector.connect(
            host= host,
            port = 3306,
            user= user,
            password=pw)
    except Exception as ex:
        return ex
    return mydb

@tracer.start_as_current_span("insert_data")
def insert_data(mydb, messages):
    mycursor = mydb.cursor()
    sql = f"insert into otel_demo.Dados (dados) values ({json.dumps(messages.content)})"
    mycursor.execute(sql)
    mydb.commit()

def get_message(queue_id):
    
    get_messages_response = queue_client.get_messages(
        queue_id=queue_id,
        visibility_in_seconds=10,
        timeout_in_seconds=10,
        limit=10)
    return get_messages_response.data.messages

@tracer.start_as_current_span("delete_msg")
def delete_message(queue_id, messages):
    
    delete_message_response = queue_client.delete_message(
    queue_id=queue_id,
    message_receipt=messages.receipt)
    return delete_message_response.headers
    
@tracer.start_as_current_span("process_msg")    
def process_data(mydb, messages, queue_id):
    insert_data(mydb, messages)
    delete_message(queue_id, messages)


if __name__ == "__main__":

    passwd = get_text_secret(secret_id)
    db = mysql_connect(host, user ,passwd)
    while True:
        messages = get_message(queue_id)
        if len(messages) > 0:
            for msg in messages:
                process_data(db, msg, queue_id)
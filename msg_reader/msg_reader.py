import oci
import pymysql
import json
import base64
import os
from opentelemetry import trace, context
from opentelemetry.trace import NonRecordingSpan, SpanContext, TraceFlags

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

def mysql_connect(host, user, pw):
    try:
        return pymysql.connect(
            host=host,
            port=3306,
            database="otel_demo",
            user=user,
            password=pw,
            autocommit=True
        )
    except Exception as ex:
        print("ERROR: failed to connect to MySQL", ex, flush=True)
        raise

@tracer.start_as_current_span("insert_data")
def insert_data(mydb, messages):
    with mydb.cursor() as mycursor:
        sql = "INSERT INTO Dados (dados) VALUES (%s)"
        mycursor.execute(sql, (json.dumps(messages),))

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

def get_propagated_context(trace_id, span_id):
    # Create a SpanContext from the extracted trace and span IDs
    return SpanContext(
        trace_id=trace_id,
        span_id=span_id,
        is_remote=True,
        trace_flags=TraceFlags(TraceFlags.SAMPLED),
    )

@tracer.start_as_current_span("process_msg")    
def process_data(mydb, messages, queue_id):
    insert_data(mydb, messages.content)
    delete_message(queue_id, messages)

if __name__ == "__main__":

    passwd = get_text_secret(secret_id)
    db = mysql_connect(host, user ,passwd)
    while True:
        messages = get_message(queue_id)
        if len(messages) > 0:
            for msg in messages:
                prop = msg.metadata.custom_properties
                ctx = trace.set_span_in_context(NonRecordingSpan(get_propagated_context(int(prop['trace_id']), int(prop['span_id']))))
                context.attach(ctx)
                process_data(db, msg, queue_id)
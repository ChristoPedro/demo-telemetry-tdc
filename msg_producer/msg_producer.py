import oci
import os
import json
from flask import Flask, request, Response
from opentelemetry import trace

tracer = trace.get_tracer("put_message.tracer")

app = Flask(__name__)

service_endpoint = os.environ['SERVICE_ENDPOINT']
queue_id = os.environ['QUEUE_ID']

if 'OCI_RESOURCE_PRINCIPAL_VERSION' in os.environ:
    signer = oci.auth.signers.get_resource_principals_signer()
else:
    signer = oci.auth.signers.InstancePrincipalsSecurityTokenSigner()

queue_client = oci.queue.QueueClient(config={}, signer=signer, service_endpoint=service_endpoint)

@tracer.start_as_current_span("put_message")
def put_message (queue_id, message):
    try:
        span = trace.get_current_span()
        span_context = span.get_span_context()
        trace_id = span_context.trace_id
        span_id = span_context.span_id

        put_messages_response = queue_client.put_messages(
            queue_id= queue_id,
            put_messages_details=oci.queue.models.PutMessagesDetails(
                messages=[
                    oci.queue.models.PutMessagesDetailsEntry(
                        content=json.dumps(message),
                    metadata=oci.queue.models.MessageMetadata(
                        custom_properties={
                            'trace_id': str(trace_id),
                            'span_id': str(span_id)}))]))
        return put_messages_response.data.messages[0] , 200
    except Exception as e:
        return {"Error" : e} , 404

@app.route("/", methods=['POST'])
def post_messages():
    message = json.loads(request.data.decode("utf-8"))
    retorno , status = put_message(queue_id, message )
    return Response(response=str(retorno),
                    status=status,
                    mimetype="application/json") 

if __name__ == "__main__":
    
    app.run(debug=False, host='0.0.0.0')
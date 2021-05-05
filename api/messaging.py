from twilio.twiml.messaging_response import MessagingResponse


def as_twilio_response(message: str) -> str:
    resp = MessagingResponse()
    msg = resp.message()
    msg.body(message)
    return str(resp)

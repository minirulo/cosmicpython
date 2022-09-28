from allocation.domain import events

def send_out_of_stock_notification(event: events.OutOfStock):
    pass


HANDLERS = {
    events.OutOfStock: [send_out_of_stock_notification]
}


def handle(event: events.Event):
    for handler in HANDLERS[type(event)]:
        handler(event)






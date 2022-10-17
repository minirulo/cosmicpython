import inspect
from allocation.domain import events, commands
from allocation.service_layer import unit_of_work, messagebus, handlers
from allocation.adapters import email, redis_eventpublisher, orm
from typing import Callable, Dict, Type, List

def injected_dependencies(handler, dependencies):
    params = inspect.signature(handler).parameters
    deps = {
        name: dependency
        for name, dependency in dependencies.items()
        if name in params
    }
    return lambda message: handler(message, **deps)


def bootstrap(
    start_orm: bool = True,
    uow: unit_of_work.AbstractUnitOfWork = unit_of_work.SqlAlchemyUnitOfWork(),
    send_mail: Callable = email.send_email,
    publish: Callable = redis_eventpublisher.publish
) -> messagebus.MessageBus:
    if start_orm:
        orm.start_mappers()
        
    dependencies = {"uow": uow, "send_mail": send_mail, "publish": publish}
    injected_event_handlers = {
        event_type: [
            injected_dependencies(handler, dependencies)
            for handler in event_handlers
        ]
        for event_type, event_handlers in handlers.EVENT_HANDLERS.items()
    }
    injected_command_handlers = {
        command_type: injected_dependencies(handler, dependencies)
        for command_type, handler in handlers.COMMAND_HANDLERS.items()
    }
    return messagebus.MessageBus(
        uow=uow,
        event_handlers=injected_event_handlers,
        command_handlers=injected_command_handlers
    )
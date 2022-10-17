from allocation.domain import commands, events
from . import unit_of_work
from typing import List, Union, Dict, Type, Callable
from tenacity import Retrying, RetryError, stop_after_attempt, wait_exponential
from . import handlers, unit_of_work

import logging
logger = logging.getLogger(__name__)

Message = Union[events.Event, commands.Command]

class MessageBus:
    def __init__(
        self, 
        uow: unit_of_work.AbstractUnitOfWork, 
        event_handlers: Dict[Type[events.Event], List[Callable]], 
        command_handlers: Dict[Type[commands.Command], Callable]
    ) -> None:
        self.uow = uow
        self.event_handlers = event_handlers
        self.command_handlers = command_handlers
    
    def handle(
        self,
        message: Message
    ):
        results = []
        self.queue = [message]
        while self.queue:
            message = self.queue.pop(0)
            if isinstance(message, events.Event):
                self.handle_event(message)
            elif isinstance(message, commands.Command):
                result = self.handle_command(message)
                results.append(result)
            else:
                raise Exception(f"{message} is neither a Command nor an Event")
        return results
    
    def handle_command(
        self,
        command: commands.Command
    ):
        logger.debug("handling command %s", command)
        try:
            handler = self.command_handlers[type(command)]
            result = handler(command)
            self.queue.extend(self.uow.collect_new_events())
            return result
        except Exception as e:
            logger.exception("Erro handling command %s", command)
            raise

    def handle_event(
        self,
        event: events.Event
    ):
        for handler in self.event_handlers[type(event)]:
            try:
                for attempt in Retrying(
                    stop=stop_after_attempt(3),
                    wait=wait_exponential()
                ):
                    with attempt:
                        logger.debug("handling event %s with handler %s", event, handler)
                        handler(event)
                        self.queue.extend(self.uow.collect_new_events())
            except RetryError as retry_fail:
                logger.error(
                    "Failed to handle event %s times, giving up!",
                    retry_fail.last_attempt.attempt_number
                )
                continue
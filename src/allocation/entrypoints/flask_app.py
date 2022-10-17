from datetime import datetime
from flask import Flask, request, jsonify
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from allocation import views
from allocation.domain import model, commands
from allocation.adapters import orm
from allocation.service_layer import services, unit_of_work, messagebus

app = Flask(__name__)
orm.start_mappers()


@app.route("/add_batch", methods=["POST"])
def add_batch():
    eta = request.json["eta"]
    if eta is not None:
        eta = datetime.fromisoformat(eta).date()
    uow = unit_of_work.SqlAlchemyUnitOfWork()
    bus = messagebus.MessageBus()
    bus.handle(commands.CreateBatch(request.json["ref"],request.json["sku"],request.json["quantity"],eta), uow)
    return "OK", 201


@app.route("/allocate", methods=["POST"])
def allocate_endpoint():
    try:
        uow = unit_of_work.SqlAlchemyUnitOfWork()
        bus = messagebus.MessageBus()
        [batchref] = bus.handle(commands.Allocate(request.json["reference"],request.json["sku"],request.json["quantity"]), uow)
    except (model.OutOfStock, messagebus.InvalidSku) as e:
        return {"message": str(e)}, 400

    return {"batchref": batchref}, 201


@app.route("/allocations/<orderid>", methods=["GET"])
def allocations_view_endpoint(orderid):
    uow = unit_of_work.SqlAlchemyUnitOfWork()
    result = views.allocations(orderid, uow)
    if not result:
        return "not found", 404
    return jsonify(result), 200
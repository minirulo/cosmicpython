from datetime import datetime
from flask import Flask, request, jsonify

from allocation import views, bootstrap
from allocation.domain import model, commands
from allocation.service_layer import unit_of_work, handlers

app = Flask(__name__)
bus = bootstrap.bootstrap()


@app.route("/add_batch", methods=["POST"])
def add_batch():
    eta = request.json["eta"]
    if eta is not None:
        eta = datetime.fromisoformat(eta).date()
    bus.handle(commands.CreateBatch(request.json["ref"],request.json["sku"],request.json["quantity"], eta))
    return "OK", 201


@app.route("/allocate", methods=["POST"])
def allocate_endpoint():
    try:
        [batchref] = bus.handle(commands.Allocate(request.json["reference"],request.json["sku"],request.json["quantity"]))
    except (model.OutOfStock, handlers.InvalidSku) as e:
        return {"message": str(e)}, 400

    return {"batchref": batchref}, 201


@app.route("/allocations/<orderid>", methods=["GET"])
def allocations_view_endpoint(orderid):
    uow = unit_of_work.SqlAlchemyUnitOfWork()
    result = views.allocations(orderid)
    if not result:
        return "not found", 404
    return jsonify(result), 200
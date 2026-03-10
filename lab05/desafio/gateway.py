# gateway.py — gateway de traducao de protocolo: REST -> gRPC
"""
Expoe uma API REST (POST /calcular) e internamente delega ao servidor gRPC
da Tarefa 4. Traduz erros gRPC para respostas HTTP apropriadas.

Arquitetura:
    Cliente REST  -->  Gateway Flask (porta 5051)  -->  Servidor gRPC (porta 50051)
    (HTTP/JSON)        (traduz)                        (HTTP/2 + Protobuf)
"""
import sys
import os

# Adiciona t4_grpc ao path para importar os stubs gerados pelo protoc
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "t4_grpc"))

import grpc
import calculadora_pb2
import calculadora_pb2_grpc
from flask import Flask, request, jsonify

app = Flask(__name__)

GRPC_HOST = "localhost"
GRPC_PORT = 50051

# Mapeamento de StatusCode gRPC -> HTTP status code
_GRPC_TO_HTTP = {
    grpc.StatusCode.INVALID_ARGUMENT:  400,
    grpc.StatusCode.NOT_FOUND:         404,
    grpc.StatusCode.ALREADY_EXISTS:    409,
    grpc.StatusCode.PERMISSION_DENIED: 403,
    grpc.StatusCode.UNAUTHENTICATED:   401,
    grpc.StatusCode.UNAVAILABLE:       503,
    grpc.StatusCode.INTERNAL:          500,
    grpc.StatusCode.UNIMPLEMENTED:     501,
    grpc.StatusCode.DEADLINE_EXCEEDED: 504,
}


@app.post("/calcular")
def calcular():
    """
    POST /calcular
    Body: {"operacao": "soma", "a": 7, "b": 3}
    Traduz para gRPC Calcular(RequisicaoCalculo(...)) e retorna o resultado.
    """
    dados = request.get_json(silent=True)
    if not dados:
        return jsonify({"erro": "Corpo JSON obrigatorio"}), 400

    campos = ["operacao", "a", "b"]
    faltando = [c for c in campos if c not in dados]
    if faltando:
        return jsonify({"erro": f"Campos obrigatorios ausentes: {faltando}"}), 400

    try:
        a = float(dados["a"])
        b = float(dados["b"])
    except (TypeError, ValueError):
        return jsonify({"erro": "Campos 'a' e 'b' devem ser numericos"}), 400

    # Cria canal HTTP/2 e delega ao servidor gRPC
    with grpc.insecure_channel(f"{GRPC_HOST}:{GRPC_PORT}") as canal:
        stub = calculadora_pb2_grpc.CalculadoraStub(canal)
        req = calculadora_pb2.RequisicaoCalculo(
            operacao=dados["operacao"],
            a=a,
            b=b,
        )
        try:
            resp = stub.Calcular(req)
            return jsonify({
                "resultado":  resp.resultado,
                "descricao":  resp.descricao,
                "via":        "gRPC -> HTTP/2 + Protobuf",
            }), 200

        except grpc.RpcError as e:
            http_status = _GRPC_TO_HTTP.get(e.code(), 500)
            return jsonify({
                "erro":        e.details(),
                "grpc_status": str(e.code()),
            }), http_status


@app.get("/saude")
def saude():
    """GET /saude — verifica se o gateway consegue atingir o servidor gRPC."""
    try:
        with grpc.insecure_channel(f"{GRPC_HOST}:{GRPC_PORT}") as canal:
            stub = calculadora_pb2_grpc.CalculadoraStub(canal)
            resp = stub.VerificarSaude(calculadora_pb2.RequisicaoSaude())
            return jsonify({
                "gateway": "online",
                "grpc_server": resp.status,
                "grpc_versao": resp.versao,
            }), 200
    except grpc.RpcError as e:
        return jsonify({"gateway": "online", "grpc_server": "indisponivel", "detalhe": str(e)}), 503


if __name__ == "__main__":
    print("Gateway REST->gRPC em http://localhost:5051 | Ctrl+C para encerrar")
    print(f"Servidor gRPC esperado em {GRPC_HOST}:{GRPC_PORT}")
    app.run(host="localhost", port=5051, debug=False)

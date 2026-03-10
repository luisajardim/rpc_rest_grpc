# comparativo.py — analise comparativa executavel dos tres paradigmas
"""
Simula as tres abordagens em memoria para fins de analise comparativa.
Nenhum servidor externo necessario.
"""
from typing import Any

# ===== ABORDAGEM 1: RPC — chamada procedural =====

_rpc_registry = {
    "soma":    lambda a, b: a + b,
    "divisao": lambda a, b: a / b if b != 0 else float("inf"),
}

class ClienteRPC:
    """Proxy RPC: o cliente chama como funcao local. A rede e oculta."""
    def soma(self, a: float, b: float) -> float:
        return _rpc_registry["soma"](a, b)

# ===== ABORDAGEM 2: REST — recurso + verbo HTTP =====

_db: dict = {}
_next_id: int = 1

def post_calculos(payload: dict) -> tuple:
    """Simula POST /calculos — cria um recurso de calculo."""
    global _next_id
    ops = {"soma": payload["a"] + payload["b"],
           "divisao": payload["a"] / payload["b"] if payload["b"] != 0 else float("inf")}
    resultado = ops[payload["operacao"]]
    recurso = {"id": _next_id, **payload, "resultado": resultado}
    _db[_next_id] = recurso
    _next_id += 1
    return 201, recurso

def get_calculos(id: int) -> tuple:
    """Simula GET /calculos/{id} — recupera recurso existente."""
    if id not in _db:
        return 404, {"erro": "nao encontrado"}
    return 200, _db[id]

# ===== ABORDAGEM 3: gRPC — contrato .proto, tipos fortes =====

class RequisicaoCalculo:
    """Simula mensagem Protobuf gerada pelo compilador gRPC."""
    def __init__(self, operacao: str, a: float, b: float):
        self.operacao = operacao
        self.a = a
        self.b = b

class RespostaCalculo:
    def __init__(self, resultado: float, descricao: str):
        self.resultado = resultado
        self.descricao = descricao

def calcular_grpc(req: RequisicaoCalculo) -> RespostaCalculo:
    """Simula o servicer gRPC."""
    ops = {"soma": req.a + req.b,
           "divisao": req.a / req.b if req.b != 0 else float("inf")}
    r = ops[req.operacao]
    return RespostaCalculo(resultado=r, descricao=f"{req.a} {req.operacao} {req.b} = {r}")

# ===== DEMONSTRACAO =====

print("=" * 60)
print("  COMPARATIVO: RPC  vs  REST  vs  gRPC")
print("=" * 60)

print("\n[1] RPC — chamada procedural (estilo XML-RPC)")
cliente = ClienteRPC()
r = cliente.soma(7, 3)
print(f"    cliente.soma(7, 3) = {r}")
print("    -> O cliente chama como funcao local; protocolo e invisible")

print("\n[2] REST — recurso + verbo HTTP")
status, recurso = post_calculos({"operacao": "soma", "a": 7, "b": 3})
print(f"    POST /calculos  -> {status}  {recurso}")
status2, recurso2 = get_calculos(recurso["id"])
print(f"    GET  /calculos/{recurso['id']}  -> {status2}  {recurso2}")
print("    -> Estado persistido como recurso; cliente controla via verbos")

print("\n[3] gRPC — contrato .proto + tipos fortes")
req = RequisicaoCalculo(operacao="soma", a=7.0, b=3.0)
resp = calcular_grpc(req)
print(f"    Calcular(RequisicaoCalculo(operacao='soma', a=7, b=3))")
print(f"    -> {resp.descricao}")
print("    -> Contrato em .proto; tipos verificados em compilacao")

print("\n" + "=" * 60)
print("  DIMENSOES DE COMPARACAO")
print("=" * 60)
dimensoes = [
    ("Dimensao",         "RPC (XML-RPC)",    "REST",              "gRPC"),
    ("─" * 16,           "─" * 16,           "─" * 18,            "─" * 18),
    ("Unidade central",  "Procedimento",     "Recurso (URI)",     "Servico (.proto)"),
    ("Protocolo",        "HTTP ou TCP",      "HTTP/1.1",          "HTTP/2"),
    ("Serializacao",     "XML",              "JSON (texto)",      "Protobuf (binario)"),
    ("Contrato",         "Interface remota", "Convencao REST",    "Schema .proto"),
    ("Tipagem",          "Dinamica",         "Sem verificacao",   "Estatica / forte"),
    ("Streaming",        "Nao nativo",       "Limitado",          "Sim (bidirecional)"),
    ("Melhor para",      "Sistemas legados", "APIs publicas/web", "Microservicos internos"),
]
for linha in dimensoes:
    print(f"  {linha[0]:<18} {linha[1]:<18} {linha[2]:<20} {linha[3]}")

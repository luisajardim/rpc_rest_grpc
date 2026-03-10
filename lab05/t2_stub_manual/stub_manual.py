# stub_manual.py — implementacao manual de stub + skeleton RPC
"""
Objetivo: tornar visivel o que qualquer framework RPC (XML-RPC, gRPC) oculta.
Componentes implementados manualmente:
  - Stub (cliente): serializa a chamada e envia via socket TCP.
  - Skeleton (servidor): recebe, deserializa e despacha para a funcao correta.
  - Marshalling: conversao de argumentos Python para bytes (JSON aqui; Protobuf no gRPC).
"""
import json
import socket
import threading
import time
from typing import Any

# ===================================================
# SKELETON (lado do servidor)
# Recebe bytes -> deserializa -> executa -> serializa -> devolve
# ===================================================

def _skeleton_tratar_conexao(conn: socket.socket, registro: dict):
    """
    O skeleton e gerado automaticamente em frameworks como gRPC.
    Aqui ele e manual para expor sua logica.
    """
    with conn:
        # 1. Le os primeiros 4 bytes como tamanho da mensagem (framing)
        tamanho = int.from_bytes(conn.recv(4), "big")
        # 2. Le exatamente `tamanho` bytes e deserializa (unmarshalling)
        chamada = json.loads(conn.recv(tamanho).decode())
        nome, args = chamada["method"], chamada["args"]
        print(f"  [Skeleton] Recebeu chamada: {nome}({args})")
        # 3. Despacha para a funcao registrada (dispatch table)
        try:
            if nome not in registro:
                raise KeyError(f"Metodo '{nome}' nao registrado")
            resultado = registro[nome](*args)
            resposta = json.dumps({"result": resultado}).encode()
        except Exception as e:
            resposta = json.dumps({"error": str(e)}).encode()
        # 4. Serializa e envia o resultado de volta (marshalling)
        conn.sendall(len(resposta).to_bytes(4, "big") + resposta)

def _skeleton_iniciar(host: str, port: int, registro: dict, parar: threading.Event):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as srv:
        srv.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        srv.bind((host, port))
        srv.listen(5)
        srv.settimeout(0.5)
        print(f"  [Skeleton] Servidor ouvindo em {host}:{port}")
        while not parar.is_set():
            try:
                conn, addr = srv.accept()
                threading.Thread(
                    target=_skeleton_tratar_conexao,
                    args=(conn, registro),
                    daemon=True
                ).start()
            except socket.timeout:
                continue

# ===================================================
# STUB (lado do cliente)
# Serializa a chamada -> envia -> recebe -> deserializa
# ===================================================

def _stub_chamar(host: str, port: int, nome: str, args: list) -> Any:
    """
    O stub e gerado automaticamente em frameworks como XML-RPC e gRPC.
    Aqui ele e manual para expor cada etapa.
    """
    # 1. Marshalling: converte chamada Python em bytes JSON
    payload = json.dumps({"method": nome, "args": args}).encode()
    print(f"  [Stub]     Enviando: {payload.decode()}")
    with socket.create_connection((host, port), timeout=3) as s:
        # 2. Framing: 4 bytes de tamanho + payload
        s.sendall(len(payload).to_bytes(4, "big") + payload)
        # 3. Recebe resposta com framing
        tamanho = int.from_bytes(s.recv(4), "big")
        resposta = json.loads(s.recv(tamanho).decode())
    # 4. Unmarshalling: converte bytes JSON em objeto Python
    if "error" in resposta:
        raise RuntimeError(f"Erro remoto: {resposta['error']}")
    return resposta["result"]

# ===================================================
# FUNCOES DO SERVICO (logica de negocio pura)
# Nao sabem que estao sendo chamadas remotamente
# ===================================================

def somar(a: float, b: float) -> float:
    return a + b

def obter_info() -> dict:
    return {"servico": "calculadora", "versao": "1.0", "status": "online"}

# ===================================================
# DEMONSTRACAO
# ===================================================

REGISTRO = {"somar": somar, "obter_info": obter_info}
HOST, PORT = "localhost", 9876

# Inicia o skeleton em background
parar = threading.Event()
t = threading.Thread(
    target=_skeleton_iniciar,
    args=(HOST, PORT, REGISTRO, parar),
    daemon=True
)
t.start()
time.sleep(0.15)  # aguarda o servidor estar pronto

print("=" * 55)
print("  DEMONSTRACAO: Stub + Skeleton RPC manual via sockets")
print("=" * 55)

print("\nChamada 1: somar(7, 5)")
r = _stub_chamar(HOST, PORT, "somar", [7, 5])
print(f"  Resultado recebido: {r}\n")

print("Chamada 2: obter_info()")
info = _stub_chamar(HOST, PORT, "obter_info", [])
print(f"  Resultado recebido: {info}\n")

print("Chamada 3: metodo inexistente (erro esperado)")
try:
    _stub_chamar(HOST, PORT, "metodo_que_nao_existe", [])
except RuntimeError as e:
    print(f"  Erro propagado corretamente: {e}\n")

parar.set()
print("Servidor encerrado.\n")
print("=" * 55)
print("  COMPONENTES REVELADOS POR ESTA TAREFA")
print("=" * 55)
print("  Stub (cliente):    serializa args -> envia bytes -> deserializa resultado")
print("  Skeleton (serv.):  recebe bytes -> dispatch -> serializa resultado")
print("  Marshalling:       Python dict/list/float -> bytes JSON (ou Protobuf no gRPC)")
print("  Framing:           4 bytes de tamanho + payload (delimitador de mensagem)")
print("  Dispatch table:    dicionario nome->funcao (registry no servidor)")

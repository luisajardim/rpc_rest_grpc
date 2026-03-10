# Lab 05 — Comunicação entre Processos: RPC, REST e gRPC na Prática

**Disciplina:** Laboratório de Desenvolvimento de Aplicações Móveis e Distribuídas  
**Curso:** Engenharia de Software — PUC Minas  
**Professor:** Cristiano de Macedo Neto  
**Carga horária:** 100 minutos  
**Pré-requisitos:** Lab 04 (transparência em sistemas distribuídos) concluído; Python 3.11+ instalado  

---

## Contexto e Motivação

Em 1984, Andrew Birrell e Bruce Jay Nelson publicaram o artigo seminal *Implementing Remote Procedure Calls* — a ideia central era simples: tornar a chamada de um procedimento em outra máquina tão natural e transparente quanto uma chamada local, com semântica limpa e eficiência suficiente para não inibir o programador de usar a rede. Esse princípio fundador ecoa até hoje em todas as tecnologias de comunicação que você vai implementar neste laboratório.

Quatro décadas depois, o cenário de comunicação entre processos distribuídos amadureceu em três grandes paradigmas:

- **RPC clássico** (Remote Procedure Call): o cliente invoca uma função remota como se fosse local; o protocolo é ocultado por *stubs* gerados automaticamente.
- **REST** (Representational State Transfer): proposto por Roy T. Fielding em sua tese de doutorado em 2000, organiza a comunicação em torno de **recursos** identificados por URIs e manipulados por verbos HTTP padronizados — `GET`, `POST`, `PUT`, `DELETE`.
- **gRPC**: framework open-source do Google que retoma a ideia de contrato forte do RPC clássico, mas modernizado sobre HTTP/2 com serialização binária via *Protocol Buffers* e suporte a streaming bidirecional.

Este laboratório percorre os três paradigmas de forma progressiva: você vai **ver o que está escondido** (Tarefa 2 — stub manual), **usar uma abstração clássica** (Tarefa 1 — XML-RPC), **construir uma API REST completa** (Tarefa 3) e **experimentar o gRPC** (Tarefa 4), terminando com uma análise comparativa fundamentada (Tarefa 5).

> **Referências principais:**
> - BIRRELL, Andrew D.; NELSON, Bruce Jay. Implementing Remote Procedure Calls. *ACM Transactions on Computer Systems*, v. 2, n. 1, p. 39-59, fev. 1984.
> - FIELDING, Roy T. *Architectural Styles and the Design of Network-based Software Architectures*. Tese (Doutorado) — University of California, Irvine, 2000. Cap. 5. Disponível em: <https://ics.uci.edu/~fielding/pubs/dissertation/top.htm>.
> - TANENBAUM, Andrew S.; VAN STEEN, Maarten. *Distributed Systems: Principles and Paradigms*. 3. ed. Pearson, 2017. Seção 4.1 (RPC) e Cap. 2 (Architectures).

---

## Objetivos de Aprendizagem

Ao concluir este laboratório, o aluno será capaz de:

1. Explicar o papel dos *stubs* (cliente) e *skeletons* (servidor) no mecanismo de RPC e por que eles existem.
2. Implementar um servidor e cliente XML-RPC usando apenas a biblioteca padrão do Python.
3. Projetar e implementar uma API REST com Flask, aplicando corretamente os verbos HTTP e códigos de status.
4. Compilar um arquivo `.proto`, gerar os stubs gRPC e implementar um serviço funcional.
5. Comparar os três paradigmas segundo critérios técnicos objetivos: protocolo, serialização, contrato, tipagem e casos de uso adequados.

---

## Gestão de Tempo

> ⚠️ As Tarefas 1 a 4 são obrigatórias. A Tarefa 5 (comparativo) é obrigatória como análise, mas pode ser feita fora da aula se o tempo esgotar. O Desafio é bônus.

| Tarefa | Tipo | Tempo sugerido |
|---|---|---|
| Setup e dependências | Configuração | 5 min |
| Tarefa 1 — XML-RPC | Implementação | 20 min |
| Tarefa 2 — Stub manual | Execução + análise | 15 min |
| Tarefa 3 — REST com Flask | Implementação | 25 min |
| Tarefa 4 — gRPC | Implementação | 25 min |
| Tarefa 5 — Comparativo | Análise + reflexão | 10 min |
| **Total** | | **~100 min** |

---

## Ambiente e Dependências

```bash
# Criar e ativar ambiente virtual
python -m venv venv
source venv/bin/activate        # Linux/macOS
# venv\Scripts\activate.bat     # Windows

# Instalar dependências
pip install flask requests grpcio grpcio-tools
```

> **Nota:** `xmlrpc` faz parte da biblioteca padrão do Python — não precisa de instalação.

---

## Estrutura do Repositório

```
lab05/
├── t1_xmlrpc/
│   ├── servidor_xmlrpc.py       <- servidor XML-RPC
│   └── cliente_xmlrpc.py        <- cliente XML-RPC
├── t2_stub_manual/
│   └── stub_manual.py           <- stub + skeleton implementados manualmente
├── t3_rest/
│   ├── servidor_rest.py         <- API REST com Flask
│   └── cliente_rest.py          <- cliente HTTP com requests
├── t4_grpc/
│   ├── calculadora.proto        <- contrato do servico
│   ├── calculadora_pb2.py       <- gerado automaticamente (nao editar)
│   ├── calculadora_pb2_grpc.py  <- gerado automaticamente (nao editar)
│   ├── servidor_grpc.py         <- implementacao do servicer
│   └── cliente_grpc.py          <- cliente gRPC
├── t5_comparativo/
│   └── comparativo.py           <- analise comparativa executavel
└── reflexao.md
```

---

## Roteiro de Atividades

### Tarefa 1 — XML-RPC: o RPC Clássico (20 min)

**Conceito:** XML-RPC é uma implementação de RPC que usa HTTP como transporte e XML como formato de serialização. É a tecnologia mais próxima do modelo original de Birrell & Nelson disponível na biblioteca padrão do Python. O *stub* do cliente (`ServerProxy`) faz uma chamada parecer local; o *skeleton* do servidor (`SimpleXMLRPCServer`) recebe, deserializa, executa e devolve o resultado — tudo de forma automática.

> **Por que XML-RPC antes de gRPC?** Porque o XML-RPC expõe o modelo RPC de forma mais transparente: você consegue inspecionar o tráfego HTTP/XML com ferramentas simples, entendendo o que acontece "por baixo" antes de usar abstrações mais sofisticadas.

**Passo 1.1 — Implemente o servidor:**

Crie `t1_xmlrpc/servidor_xmlrpc.py`. O servidor expõe um serviço de calculadora e um serviço de log de eventos como se fossem funções locais do cliente.

```python
# servidor_xmlrpc.py
from xmlrpc.server import SimpleXMLRPCServer
import datetime

# ===== FUNCOES DO SERVICO =====

def calcular(operacao: str, a: float, b: float) -> float:
    """
    Executa uma operacao aritmetica remotamente.
    Este codigo roda no servidor; o cliente chama como se fosse local.
    """
    ops = {
        "soma":          lambda x, y: x + y,
        "subtracao":     lambda x, y: x - y,
        "multiplicacao": lambda x, y: x * y,
        "divisao":       lambda x, y: x / y if y != 0 else float("inf"),
    }
    if operacao not in ops:
        raise ValueError(f"Operacao desconhecida: '{operacao}'")
    resultado = ops[operacao](a, b)
    print(f"[Servidor] calcular({operacao}, {a}, {b}) = {resultado}")
    return resultado

def registrar_evento(mensagem: str) -> str:
    """Registra um evento com timestamp e retorna confirmacao."""
    ts = datetime.datetime.now().strftime("%H:%M:%S")
    linha = f"[{ts}] {mensagem}"
    print(f"[Servidor] Evento: {linha}")
    return f"ACK: {linha}"

def listar_operacoes() -> list:
    """Retorna a lista de operacoes disponiveis (introspeccao simples)."""
    return ["soma", "subtracao", "multiplicacao", "divisao"]

# ===== CONFIGURACAO DO SERVIDOR =====

if __name__ == "__main__":
    HOST, PORT = "localhost", 8765
    server = SimpleXMLRPCServer((HOST, PORT), logRequests=False, allow_none=True)
    server.register_function(calcular,          "calcular")
    server.register_function(registrar_evento,  "registrar_evento")
    server.register_function(listar_operacoes,  "listar_operacoes")
    server.register_introspection_functions()   # habilita system.listMethods()
    print(f"Servidor XML-RPC em http://{HOST}:{PORT} | Ctrl+C para encerrar")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nServidor encerrado.")
```

**Passo 1.2 — Implemente o cliente:**

Crie `t1_xmlrpc/cliente_xmlrpc.py`. Observe que o código cliente chama `proxy.calcular(...)` como se fosse uma função local — a rede é completamente transparente neste nível.

```python
# cliente_xmlrpc.py
import xmlrpc.client

ENDPOINT = "http://localhost:8765/"

def main():
    # ServerProxy e o "stub" do cliente:
    # cada atributo acessado vira uma chamada RPC automaticamente.
    proxy = xmlrpc.client.ServerProxy(ENDPOINT, allow_none=True)

    print("=== Chamadas XML-RPC para o servidor de calculadora ===\n")

    # Introspeccao: descobre o que o servidor oferece
    metodos = proxy.system.listMethods()
    print(f"Metodos disponiveis no servidor: {metodos}\n")

    # Operacoes aritmeticas — chamadas identicas a funcoes locais
    chamadas = [
        ("soma",          10.0, 3.0),
        ("subtracao",     10.0, 3.0),
        ("multiplicacao",  4.0, 7.0),
        ("divisao",       22.0, 7.0),
    ]
    for op, a, b in chamadas:
        try:
            resultado = proxy.calcular(op, a, b)
            print(f"  calcular('{op}', {a}, {b}) = {resultado:.6f}")
        except xmlrpc.client.Fault as e:
            # Fault e o mecanismo XML-RPC para propagar excecoes do servidor
            print(f"  Erro do servidor [{e.faultCode}]: {e.faultString}")

    # Chamada de funcao de log
    print()
    ack = proxy.registrar_evento("Aluno concluiu Tarefa 1")
    print(f"  registrar_evento -> '{ack}'")

    # Operacao invalida — deve retornar Fault
    print("\n  Testando operacao invalida ('raiz_quadrada'):")
    try:
        proxy.calcular("raiz_quadrada", 9.0, 0.0)
    except xmlrpc.client.Fault as e:
        print(f"  Fault recebido: {e.faultString}")

if __name__ == "__main__":
    try:
        main()
    except ConnectionRefusedError:
        print("Servidor nao disponivel.")
        print("Execute primeiro: python servidor_xmlrpc.py")
```

**Como executar (dois terminais):**

```bash
# Terminal 1
python t1_xmlrpc/servidor_xmlrpc.py

# Terminal 2
python t1_xmlrpc/cliente_xmlrpc.py
```

**Questões para reflexão:**
- Você chamou `proxy.calcular("soma", 10, 3)` como se fosse uma função local. Onde, exatamente, ocorre a serialização XML? Inspecione o tráfego HTTP com `logRequests=True` no servidor e observe o que é transmitido.
- O que é um `xmlrpc.client.Fault`? Como ele se compara a uma exceção Python convencional? Por que o RPC precisa de um mecanismo especial para propagar erros do servidor para o cliente?
- O método `system.listMethods()` demonstra **introspecção remota**. Qual das transparências da ISO/RM-ODP (vistas no Lab 04) esse recurso relaciona-se mais diretamente? Justifique.

---

### Tarefa 2 — Stub Manual: O que o Framework Esconde (15 min)

**Conceito:** Frameworks de RPC como XML-RPC e gRPC geram *stubs* e *skeletons* automaticamente, ocultando toda a complexidade de serialização e transporte. Esta tarefa torna essa camada **visível**: você vai executar e analisar uma implementação de RPC feita do zero, usando apenas sockets TCP e JSON, para entender o que acontece "por baixo" de qualquer framework RPC.

> Esta tarefa é de **execução e análise** — o código já está pronto. Seu objetivo é executá-lo, observar o output e responder às questões.

Crie `t2_stub_manual/stub_manual.py` com o código abaixo e execute-o:

```python
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
```

```bash
# Execucao (terminal unico — servidor em thread background)
python t2_stub_manual/stub_manual.py
```

**Questões para reflexão:**
- Identifique no código as quatro etapas do ciclo de uma chamada RPC descritas por Birrell & Nelson (1984): *marshalling*, *transmissão*, *dispatching* e *unmarshalling*. Em qual linha de código cada etapa ocorre?
- O XML-RPC usa XML; o gRPC usa Protobuf binário; este stub usa JSON. Qual a consequência prática de usar JSON em vez de Protobuf para um sistema com alto volume de chamadas? Considere tamanho de payload e overhead de parsing.
- O *framing* (4 bytes de tamanho + payload) é necessário por uma propriedade do protocolo TCP. Qual é essa propriedade, e o que aconteceria se você não usasse framing?

---

### Tarefa 3 — API REST com Flask (25 min)

**Conceito:** REST não é um protocolo — é um **estilo arquitetural** definido por seis restrições, a mais importante sendo a interface uniforme: os recursos são identificados por URIs, e as operações sobre eles são expressas pelos verbos HTTP (`GET`, `POST`, `PUT`, `DELETE`). Ao contrário do RPC, o cliente não chama funções: ele **manipula representações de recursos** via HTTP. O servidor é **stateless** — cada requisição contém toda a informação necessária.

Nesta tarefa você implementa uma API REST completa de gerenciamento de produtos. Atenção especial aos **códigos de status HTTP**: eles fazem parte do contrato e comunicam semântica ao cliente.

| Verbo | URI | Semântica | Código de sucesso |
|---|---|---|---|
| GET | `/produtos` | Lista todos os produtos | 200 OK |
| GET | `/produtos/{id}` | Retorna produto por ID | 200 OK |
| POST | `/produtos` | Cria novo produto | 201 Created |
| PUT | `/produtos/{id}` | Atualiza produto existente | 200 OK |
| DELETE | `/produtos/{id}` | Remove produto | 200 OK |

**Passo 3.1 — Implemente o servidor:**

Crie `t3_rest/servidor_rest.py`:

```python
# servidor_rest.py
from flask import Flask, request, jsonify

app = Flask(__name__)

# Banco de dados em memoria (suficiente para fins de laboratorio)
_produtos: dict = {
    1: {"id": 1, "nome": "Teclado Mecanico", "preco": 349.90, "estoque": 15},
    2: {"id": 2, "nome": "Monitor 24pol",    "preco": 1299.00, "estoque": 8},
}
_proximo_id: int = 3

# ===== ENDPOINTS =====

@app.get("/produtos")
def listar_produtos():
    """GET /produtos — lista todos os produtos."""
    return jsonify(list(_produtos.values())), 200

@app.get("/produtos/<int:produto_id>")
def obter_produto(produto_id: int):
    """GET /produtos/{id} — retorna produto pelo ID."""
    produto = _produtos.get(produto_id)
    if not produto:
        # 404 Not Found: recurso nao existe
        return jsonify({"erro": "Produto nao encontrado"}), 404
    return jsonify(produto), 200

@app.post("/produtos")
def criar_produto():
    """POST /produtos — cria um novo produto."""
    global _proximo_id
    dados = request.get_json(silent=True)
    if not dados or "nome" not in dados or "preco" not in dados:
        # 400 Bad Request: dados invalidos ou incompletos
        return jsonify({"erro": "Campos obrigatorios: nome, preco"}), 400
    novo = {
        "id":      _proximo_id,
        "nome":    dados["nome"],
        "preco":   float(dados["preco"]),
        "estoque": int(dados.get("estoque", 0)),
    }
    _produtos[_proximo_id] = novo
    _proximo_id += 1
    # 201 Created: recurso criado com sucesso
    return jsonify(novo), 201

@app.put("/produtos/<int:produto_id>")
def atualizar_produto(produto_id: int):
    """PUT /produtos/{id} — atualiza completamente um produto existente."""
    if produto_id not in _produtos:
        return jsonify({"erro": "Produto nao encontrado"}), 404
    dados = request.get_json(silent=True)
    if not dados:
        return jsonify({"erro": "Corpo JSON obrigatorio"}), 400
    atual = _produtos[produto_id]
    _produtos[produto_id] = {
        "id":      produto_id,
        "nome":    dados.get("nome",    atual["nome"]),
        "preco":   float(dados.get("preco",   atual["preco"])),
        "estoque": int(dados.get("estoque", atual["estoque"])),
    }
    return jsonify(_produtos[produto_id]), 200

@app.delete("/produtos/<int:produto_id>")
def deletar_produto(produto_id: int):
    """DELETE /produtos/{id} — remove produto."""
    if produto_id not in _produtos:
        return jsonify({"erro": "Produto nao encontrado"}), 404
    removido = _produtos.pop(produto_id)
    return jsonify({"mensagem": f"Produto '{removido['nome']}' removido"}), 200

if __name__ == "__main__":
    print("API REST rodando em http://localhost:5050 | Ctrl+C para encerrar")
    app.run(host="localhost", port=5050, debug=False)
```

**Passo 3.2 — Implemente o cliente:**

Crie `t3_rest/cliente_rest.py`. Note que o cliente manipula **recursos via verbos HTTP** — nenhuma chamada de função nomeada, ao contrário do RPC.

```python
# cliente_rest.py
import requests
import json

BASE = "http://localhost:5050"

def sep(titulo: str):
    print(f"\n{'─' * 50}")
    print(f"  {titulo}")
    print('─' * 50)

def exibir(r: requests.Response):
    print(f"  Status: {r.status_code}")
    try:
        print(f"  Body:   {json.dumps(r.json(), ensure_ascii=False, indent=4)}")
    except Exception:
        print(f"  Body:   {r.text}")

def main():
    sep("GET /produtos — listar todos")
    exibir(requests.get(f"{BASE}/produtos"))

    sep("GET /produtos/1 — buscar por ID")
    exibir(requests.get(f"{BASE}/produtos/1"))

    sep("GET /produtos/999 — ID inexistente (404 esperado)")
    exibir(requests.get(f"{BASE}/produtos/999"))

    sep("POST /produtos — criar novo produto")
    r = requests.post(f"{BASE}/produtos",
                      json={"nome": "Headset USB", "preco": 199.90, "estoque": 25})
    exibir(r)
    novo_id = r.json().get("id")

    sep(f"PUT /produtos/{novo_id} — atualizar preco")
    exibir(requests.put(f"{BASE}/produtos/{novo_id}",
                        json={"nome": "Headset USB", "preco": 179.90, "estoque": 25}))

    sep(f"DELETE /produtos/{novo_id} — remover produto")
    exibir(requests.delete(f"{BASE}/produtos/{novo_id}"))

    sep("GET apos DELETE — confirma remocao (404 esperado)")
    exibir(requests.get(f"{BASE}/produtos/{novo_id}"))

    sep("POST com dados invalidos — 400 esperado")
    exibir(requests.post(f"{BASE}/produtos", json={"nome": "Incompleto"}))

if __name__ == "__main__":
    try:
        main()
    except requests.exceptions.ConnectionError:
        print("Servidor nao disponivel.")
        print("Execute primeiro: python servidor_rest.py")
```

**Como executar (dois terminais):**

```bash
# Terminal 1
python t3_rest/servidor_rest.py

# Terminal 2
python t3_rest/cliente_rest.py
```

**Questões para reflexão:**
- O endpoint `POST /produtos` retorna `201 Created` em vez de `200 OK`. Por que isso importa do ponto de vista do protocolo HTTP? O que um cliente genérico (ex: um proxy de cache) pode inferir a partir do código de status `201`?
- O servidor desta tarefa **não é stateless de verdade**: `_produtos` é um dicionário em memória, e o estado se perde ao reiniciar. O que precisaria mudar na arquitetura para que o servidor fosse genuinamente stateless conforme a restrição REST de Fielding?
- Compare a experiência de chamar `proxy.calcular("soma", 7, 3)` (Tarefa 1) com `requests.post("/calculos", json={...})` (Tarefa 3). Qual abordagem deixa mais claro o **contrato entre cliente e servidor**? Justifique sua resposta considerando o princípio da interface uniforme do REST.

---

### Tarefa 4 — gRPC: Contrato Forte e HTTP/2 (25 min)

**Conceito:** O gRPC retoma a ideia central do RPC clássico — o cliente chama como se fosse local — mas com três melhorias fundamentais em relação ao XML-RPC: (1) **contrato explícito e tipado** em arquivos `.proto`; (2) **serialização binária** com Protocol Buffers, muito mais eficiente que XML ou JSON; (3) **HTTP/2** como transporte, habilitando multiplexação e streaming bidirecional.

O fluxo de desenvolvimento gRPC é:

```
1. Escrever o contrato (.proto)
        ↓
2. Compilar com grpc_tools.protoc (gera os stubs automaticamente)
        ↓
3. Implementar o servicer (servidor) usando os stubs gerados
        ↓
4. Usar o stub gerado no cliente
```

**Passo 4.1 — Escreva o contrato:**

Crie `t4_grpc/calculadora.proto`. Este arquivo é o **único ponto de verdade** do serviço: tanto servidor quanto cliente dependem dele, e qualquer breaking change aqui quebra ambos — o compilador detecta isso antes do runtime.

```protobuf
// calculadora.proto
syntax = "proto3";

package calculadora;

// Definicao do servico: quais RPCs ele oferece
service Calculadora {
  rpc Calcular     (RequisicaoCalculo) returns (RespostaCalculo);
  rpc VerificarSaude (RequisicaoSaude)  returns (RespostaSaude);
}

// Mensagem de entrada para Calcular
message RequisicaoCalculo {
  string operacao = 1;   // "soma", "subtracao", "multiplicacao", "divisao"
  double a        = 2;
  double b        = 3;
}

// Mensagem de saida de Calcular
message RespostaCalculo {
  double resultado  = 1;
  string descricao  = 2;
}

// Health check — sem parametros
message RequisicaoSaude {}

message RespostaSaude {
  string status = 1;   // "online" | "degraded"
  string versao = 2;
}
```

**Passo 4.2 — Compile o contrato (gera os stubs automaticamente):**

```bash
cd t4_grpc
python -m grpc_tools.protoc \
    -I. \
    --python_out=. \
    --grpc_python_out=. \
    calculadora.proto
```

> Dois arquivos serão gerados: `calculadora_pb2.py` (classes de mensagem) e `calculadora_pb2_grpc.py` (classes de serviço). **Não edite esses arquivos** — eles são regenerados sempre que o `.proto` muda.

**Passo 4.3 — Implemente o servidor:**

Crie `t4_grpc/servidor_grpc.py`. O servidor implementa a classe `CalculadoraServicer`, que é gerada a partir do `.proto`:

```python
# servidor_grpc.py
import grpc
from concurrent import futures
import calculadora_pb2
import calculadora_pb2_grpc

class CalculadoraServicer(calculadora_pb2_grpc.CalculadoraServicer):
    """
    Implementacao do servico definido no calculadora.proto.
    Herda de CalculadoraServicer (gerado automaticamente pelo compilador).
    Cada metodo corresponde a um RPC declarado no .proto.
    """

    def Calcular(self, request, context):
        """
        'request' e do tipo RequisicaoCalculo (definido no .proto).
        O compilador garante que os campos existem com os tipos corretos.
        """
        ops = {
            "soma":          lambda a, b: a + b,
            "subtracao":     lambda a, b: a - b,
            "multiplicacao": lambda a, b: a * b,
            "divisao":       lambda a, b: a / b if b != 0 else None,
        }
        if request.operacao not in ops:
            # gRPC tem seu proprio mecanismo de status de erro
            context.set_code(grpc.StatusCode.INVALID_ARGUMENT)
            context.set_details(f"Operacao desconhecida: '{request.operacao}'")
            return calculadora_pb2.RespostaCalculo()

        resultado = ops[request.operacao](request.a, request.b)
        if resultado is None:
            context.set_code(grpc.StatusCode.INVALID_ARGUMENT)
            context.set_details("Divisao por zero nao e permitida")
            return calculadora_pb2.RespostaCalculo()

        descricao = f"{request.a} {request.operacao} {request.b} = {resultado}"
        print(f"[Servidor gRPC] {descricao}")
        return calculadora_pb2.RespostaCalculo(
            resultado=resultado,
            descricao=descricao
        )

    def VerificarSaude(self, request, context):
        return calculadora_pb2.RespostaSaude(status="online", versao="1.0.0")

if __name__ == "__main__":
    PORTA = 50051
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=4))
    calculadora_pb2_grpc.add_CalculadoraServicer_to_server(CalculadoraServicer(), server)
    server.add_insecure_port(f"[::]:{PORTA}")
    server.start()
    print(f"Servidor gRPC rodando na porta {PORTA} | Ctrl+C para encerrar")
    try:
        server.wait_for_termination()
    except KeyboardInterrupt:
        print("\nServidor encerrado.")
        server.stop(0)
```

**Passo 4.4 — Implemente o cliente:**

Crie `t4_grpc/cliente_grpc.py`. O cliente usa o `Stub` gerado automaticamente pelo compilador — as chamadas parecem locais, exatamente como no XML-RPC, mas com tipos verificados em tempo de compilação:

```python
# cliente_grpc.py
import grpc
import calculadora_pb2
import calculadora_pb2_grpc

def main(porta: int = 50051):
    # O canal e a conexao HTTP/2 persistente com o servidor
    with grpc.insecure_channel(f"localhost:{porta}") as canal:
        # O Stub e o proxy gerado automaticamente a partir do .proto
        stub = calculadora_pb2_grpc.CalculadoraStub(canal)

        print("=== Chamadas gRPC para o servico Calculadora ===\n")

        # Health check
        saude = stub.VerificarSaude(calculadora_pb2.RequisicaoSaude())
        print(f"  Status: {saude.status} | Versao: {saude.versao}\n")

        # Operacoes aritmeticas
        chamadas = [
            ("soma",          10.0, 3.0),
            ("subtracao",     10.0, 3.0),
            ("multiplicacao",  4.0, 7.0),
            ("divisao",       22.0, 7.0),
        ]
        for op, a, b in chamadas:
            req = calculadora_pb2.RequisicaoCalculo(operacao=op, a=a, b=b)
            try:
                resp = stub.Calcular(req)
                print(f"  {resp.descricao}")
            except grpc.RpcError as e:
                print(f"  Erro gRPC [{e.code()}]: {e.details()}")

        # Divisao por zero
        print("\n  Testando divisao por zero:")
        try:
            stub.Calcular(calculadora_pb2.RequisicaoCalculo(
                operacao="divisao", a=10.0, b=0.0
            ))
        except grpc.RpcError as e:
            print(f"  Erro capturado: [{e.code()}] {e.details()}")

        # Operacao invalida
        print("\n  Testando operacao invalida ('raiz_quadrada'):")
        try:
            stub.Calcular(calculadora_pb2.RequisicaoCalculo(
                operacao="raiz_quadrada", a=9.0, b=0.0
            ))
        except grpc.RpcError as e:
            print(f"  Erro capturado: [{e.code()}] {e.details()}")

if __name__ == "__main__":
    try:
        main()
    except grpc.RpcError as e:
        if e.code() == grpc.StatusCode.UNAVAILABLE:
            print("Servidor nao disponivel.")
            print("Execute primeiro: python servidor_grpc.py")
```

**Como executar (dois terminais):**

```bash
# Terminal 1 (dentro de t4_grpc/)
python servidor_grpc.py

# Terminal 2 (dentro de t4_grpc/)
python cliente_grpc.py
```

**Questões para reflexão:**
- O arquivo `.proto` é chamado de "contrato" ou *schema*. Qual a diferença prática entre ter um contrato explícito (`.proto`) versus o REST, onde o contrato existe como convenção implícita? O que acontece se o servidor mudar o campo `resultado` de `double` para `string` sem avisar?
- O gRPC usa `grpc.StatusCode.INVALID_ARGUMENT` para erros de entrada, enquanto o REST usa o código HTTP `400`. São mecanismos equivalentes? Qual deles é mais rico semanticamente — e por quê?
- Compare `xml.client.Fault` (Tarefa 1) com `grpc.RpcError` (Tarefa 4): os dois são mecanismos de propagação de erro entre processos distintos. Qual oferece mais informação estruturada ao cliente?

---

### Tarefa 5 — Comparativo entre Paradigmas (10 min)

**Conceito:** Não existe um paradigma universalmente superior. RPC, REST e gRPC foram criados em contextos diferentes, com prioridades diferentes — e cada um tem um caso de uso onde ele domina.

Execute o script abaixo e use a tabela gerada como base para o bloco de reflexão:

Crie `t5_comparativo/comparativo.py`:

```python
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
```

```bash
python t5_comparativo/comparativo.py
```

**Questões para reflexão (registre no `reflexao.md`):**
- A coluna "Melhor para" sugere que gRPC é preferível para microserviços internos enquanto REST domina APIs públicas. Por que a **tipagem forte do .proto** é vantagem em microserviços internos mas potencial barreira em APIs públicas?
- Por que o REST é chamado de "orientado a recursos" e o RPC de "orientado a ações"? Dê um exemplo concreto de uma operação (ex: "cancelar um pedido") modelada das duas formas e discuta as implicações de cada escolha.

---

## Desafio Opcional (para quem terminar antes)

Implemente um **gateway de tradução de protocolo**: crie um servidor Flask que expõe uma API REST (`POST /calcular`) e internamente delega a chamada para o servidor gRPC da Tarefa 4.

```
Cliente REST  -->  Gateway Flask  -->  Servidor gRPC
(HTTP/JSON)        (traduz)           (HTTP2/Protobuf)
```

Requisitos:
1. O gateway recebe `{"operacao": "soma", "a": 7, "b": 3}` via `POST /calcular`.
2. Traduz para uma chamada gRPC `Calcular(RequisicaoCalculo(...))`.
3. Retorna o resultado como JSON ao cliente REST.
4. Trata erros gRPC (`grpc.RpcError`) e os converte em respostas HTTP apropriadas (ex: `400` para `INVALID_ARGUMENT`).

---

## Bloco de Reflexão (obrigatório — entregue no `reflexao.md`)

Responda individualmente, com suas próprias palavras. Cada resposta deve ter no mínimo **4 linhas**, citar ao menos **um conceito técnico** e, quando aplicável, referenciar o código que você escreveu.

1. **Stubs e skeletons:** Explique, com base no que você observou na Tarefa 2, o papel do stub (cliente) e do skeleton (servidor) em qualquer sistema RPC. Por que esses componentes existem — o que aconteceria sem eles?

2. **REST não é RPC:** Fielding (2000) critica explicitamente o uso de RPC sobre HTTP por violar a restrição de interface uniforme do REST. Com base nas Tarefas 1 e 3, descreva uma diferença fundamental de modelagem entre as duas abordagens, usando um exemplo concreto da sua implementação.

3. **Evolução de contrato:** O `.proto` da Tarefa 4 define o campo `resultado` como `double`. Se você precisasse adicionar um novo campo `unidade: string` ao `RespostaCalculo` sem quebrar clientes existentes, como o Protobuf lida com isso? E como o REST (sem schema) lidaria com a mesma mudança?

4. **Escolha de tecnologia:** Considere o seguinte cenário: uma startup precisa expor uma API de pagamentos tanto para parceiros externos (apps de terceiros) quanto para comunicação interna entre 10 microsserviços. Que tecnologia você recomendaria para cada caso e por quê? Baseie-se nos critérios do comparativo da Tarefa 5.

5. **Conexão com Labs anteriores:** O Lab 04 mostrou que transparência excessiva pode ser prejudicial. Como isso se aplica ao RPC? Em que situação a transparência do RPC — que faz uma chamada remota parecer local — pode levar um desenvolvedor a tomar uma decisão de design errada?

---

## Critérios de Avaliação

| Critério | Detalhamento | Peso |
|---|---|---|
| **Código executável** | Tarefas 1, 3 e 4 rodando sem erros, com servidor e cliente funcionando; Tarefa 2 executada e output registrado | 50% |
| **Reflexão** | 5 respostas no `reflexao.md`, mínimo 4 linhas cada, com ao menos 1 conceito técnico por resposta | 30% |
| **Organização** | Estrutura de arquivos correta; arquivos gerados pelo `protoc` presentes em `t4_grpc/` | 10% |
| **Desafio (bônus)** | Gateway REST→gRPC funcional com tratamento correto de erros | +10% |

---

## Referências

- BIRRELL, Andrew D.; NELSON, Bruce Jay. Implementing Remote Procedure Calls. *ACM Transactions on Computer Systems*, v. 2, n. 1, p. 39-59, fev. 1984. DOI: 10.1145/2080.357392.
- FIELDING, Roy T. *Architectural Styles and the Design of Network-based Software Architectures*. Tese (Doutorado) — University of California, Irvine, 2000. Cap. 5 (REST). Disponível em: <https://ics.uci.edu/~fielding/pubs/dissertation/top.htm>.
- TANENBAUM, Andrew S.; VAN STEEN, Maarten. *Distributed Systems: Principles and Paradigms*. 3. ed. Pearson, 2017. Seção 4.1 (RPC) e Seção 4.3 (Message-Passing).
- GOOGLE LLC. *Protocol Buffers — Language Guide (proto3)*. Disponível em: <https://protobuf.dev/programming-guides/proto3/>.
- GOOGLE LLC. *gRPC — Core Concepts, Architecture and Lifecycle*. Disponível em: <https://grpc.io/docs/what-is-grpc/core-concepts/>.
- MARTIN, Robert C. *Arquitetura Limpa: o guia do artesão para estrutura e design de software*. Alta Books, 2019. Cap. 18 (Boundary Anatomy) — padrões de fronteira entre componentes.
- PYTHON SOFTWARE FOUNDATION. *xmlrpc — XMLRPC server and client modules*. Disponível em: <https://docs.python.org/3/library/xmlrpc.html>.

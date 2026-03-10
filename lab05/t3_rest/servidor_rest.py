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

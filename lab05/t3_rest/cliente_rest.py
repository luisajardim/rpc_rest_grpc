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

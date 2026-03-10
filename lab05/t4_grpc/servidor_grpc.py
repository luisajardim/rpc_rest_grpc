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

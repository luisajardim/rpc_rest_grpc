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

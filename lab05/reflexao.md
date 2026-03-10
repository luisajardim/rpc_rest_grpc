# Reflexao -- Lab 05: RPC, REST e gRPC na Pratica

**Aluno:**  Luisa Oliveira Jardim
**Data:**  09/03/2026

---

## 1. Stubs e Skeletons

> *Explique, com base no que voce observou na Tarefa 2, o papel do stub (cliente) e do skeleton (servidor) em qualquer sistema RPC. Por que esses componentes existem -- o que aconteceria sem eles?*

**Output registrado da execucao de `stub_manual.py`:**

```
  [Skeleton] Servidor ouvindo em localhost:9876
=======================================================
  DEMONSTRACAO: Stub + Skeleton RPC manual via sockets
=======================================================

Chamada 1: somar(7, 5)
  [Stub]     Enviando: {"method": "somar", "args": [7, 5]}
  [Skeleton] Recebeu chamada: somar([7, 5])
  Resultado recebido: 12

Chamada 2: obter_info()
  [Stub]     Enviando: {"method": "obter_info", "args": []}
  [Skeleton] Recebeu chamada: obter_info([])
  Resultado recebido: {'servico': 'calculadora', 'versao': '1.0', 'status': 'online'}

Chamada 3: metodo inexistente (erro esperado)
  [Stub]     Enviando: {"method": "metodo_que_nao_existe", "args": []}
  [Skeleton] Recebeu chamada: metodo_que_nao_existe([])
  Erro propagado corretamente: Erro remoto: "Metodo 'metodo_que_nao_existe' nao registrado"

Servidor encerrado.

=======================================================
  COMPONENTES REVELADOS POR ESTA TAREFA
=======================================================
  Stub (cliente):    serializa args -> envia bytes -> deserializa resultado
  Skeleton (serv.):  recebe bytes -> dispatch -> serializa resultado
  Marshalling:       Python dict/list/float -> bytes JSON (ou Protobuf no gRPC)
  Framing:           4 bytes de tamanho + payload (delimitador de mensagem)
  Dispatch table:    dicionario nome->funcao (registry no servidor)
```

Na Tarefa 2 eu implementei manualmente o que o `grpc_tools` gera automaticamente na Tarefa 4: o **stub** do lado do cliente e o **skeleton** do lado do servidor. O stub (`_stub_chamar`) e basicamente o "representante local" do servidor -- quando eu chamo `_stub_chamar(HOST, PORT, "somar", [7, 5])`, ele serializa os argumentos em JSON, abre um socket TCP pra porta 9876 e manda a mensagem. Pra quem ta usando, parece so uma funcao normal. O skeleton (`_skeleton_tratar_conexao`) faz o caminho contrario: fica escutando o socket, recebe o JSON, descobre qual metodo foi pedido e chama o codigo de verdade (`somar` ou `obter_info`), depois devolve o resultado.

Sem esses dois componentes eu teria que misturar logica de rede com logica de negocio em todo lugar -- seria um caos. O conceito tecnico aqui e a **transparencia de acesso**: o codigo que usa o stub nao precisa saber se `somar` roda na mesma maquina ou num servidor la na Irlanda. O lado ruim dessa transparencia e que erros de rede (timeout, servidor caido) nao sao iguais a erros locais, como ficou claro quando chamei um metodo inexistente e recebi um `KeyError` propagado como mensagem de erro JSON.

---

## 2. REST nao e RPC

> *Fielding (2000) critica explicitamente o uso de RPC sobre HTTP por violar a restricao de interface uniforme do REST. Com base nas Tarefas 1 e 3, descreva uma diferenca fundamental de modelagem entre as duas abordagens, usando um exemplo concreto da sua implementacao.*

A diferenca mais clara que percebi comparando as duas tarefas e que RPC e orientado a **acoes** e REST e orientado a **recursos**. No XML-RPC da Tarefa 1, o servidor expoe funcoes: `calculadora.somar`, `calculadora.dividir`. O cliente chama `proxy.somar(10, 3)` e o URI nunca muda -- `http://localhost:8765` pra tudo. O que varia e o nome do metodo que vai dentro do XML. Voce ta basicamente ligando pro servidor e pedindo pra ele executar uma funcao.

No REST da Tarefa 3 a logica e outra: o servidor expoe **recursos** como `/produtos` e `/produtos/1`, e as acoes sao os proprios verbos HTTP (`GET` pra buscar, `POST` pra criar, `DELETE` pra remover). A critica do Fielding faz sentido aqui -- o XML-RPC usa `POST` pra absolutamente tudo e bota o verbo real dentro do corpo da requisicao. Isso quebra a **interface uniforme**, que e uma das restricoes fundamentais do REST: qualquer cliente que conheca HTTP deveria conseguir interagir com a API sem precisar de documentacao especifica, algo impossivel quando o servidor ignora a semantica dos metodos HTTP.

---

## 3. Evolucao de Contrato

> *O `.proto` da Tarefa 4 define o campo `resultado` como `double`. Se voce precisasse adicionar um novo campo `unidade: string` ao `RespostaCalculo` sem quebrar clientes existentes, como o Protobuf lida com isso? E como o REST (sem schema) lidaria com a mesma mudanca?*

O Protobuf e inteligente nisso: ele identifica os campos pelo **field number**, nao pelo nome. No `calculadora.proto` da Tarefa 4, `resultado` e o campo 1 (`double resultado = 1`). Se eu quiser adicionar `unidade`, coloco `string unidade = 2` -- um numero novo, que nunca existiu antes. Clientes compilados com o `.proto` antigo simplesmente ignoram o campo 2 quando recebem uma resposta nova, porque o Protobuf garante **compatibilidade retroativa** para campos adicionados. Servidores mais antigos que ainda nao mandam `unidade` retornam string vazia por padrao, e os clientes novos tratam isso normalmente. Ninguem quebra.

No REST sem schema, publicar a mudanca e ate mais facil: o servidor começa a incluir `"unidade": "reais"` no JSON e pronto. Clientes antigos que so leem `resposta["resultado"]` nem percebem que o campo novo existe. O problema e que essa compatibilidade e uma **convencao** sem garantia -- se alguem renomear `resultado` para `value` por descuido, nenhum compilador vai reclamar, so vai quebrar em producao. No gRPC, esse tipo de erro aparece na hora de recompilar os stubs, muito antes de ir pra producao.

---

## 4. Escolha de Tecnologia

> *Considere o seguinte cenario: uma startup precisa expor uma API de pagamentos tanto para parceiros externos (apps de terceiros) quanto para comunicacao interna entre 10 microsservicos. Que tecnologia voce recomendaria para cada caso e por que? Baseie-se nos criterios do comparativo da Tarefa 5.*

Pra **API publica com parceiros externos**, eu usaria REST com JSON sem pensar duas vezes. Desenvolvedor de app de terceiro nao quer instalar `protoc`, configurar build system pra gerar stubs nem aprender um toolchain novo -- ele quer abrir o Postman, bater na URL e ver o JSON. REST com HTTP/1.1 funciona em qualquer linguagem, qualquer ferramenta, qualquer browser. A interface uniforme (verbos + recursos) ainda e documentavel com OpenAPI/Swagger de forma que ate desenvolvedor junior consegue integrar rapido. Barreira de entrada baixissima e exatamente o que voce quer quando depende de parceiros externos.

Pra **comunicacao interna entre os 10 microsservicos**, eu apostaria no gRPC. Usando os criterios da Tarefa 5: gRPC roda sobre HTTP/2 (multiplexacao, cabecalhos comprimidos, latencia menor), serializa com Protobuf (binario, muito mais leve que JSON), e o `.proto` funciona como contrato centralizado -- se um servico mudar a assinatura de forma incompativel, o erro aparece na compilacao dos stubs, nao em producao as 3h da manha. Quando voce tem microsservicos se chamando centenas de vezes por segundo, a diferenca de performance e real. E dentro da empresa todas as equipes compartilham o mesmo repositorio de `.proto`, entao a barreira de adocao do gRPC praticamente nao existe.

---

## 5. Conexao com Labs Anteriores

> *O Lab 04 mostrou que transparencia excessiva pode ser prejudicial. Como isso se aplica ao RPC? Em que situacao a transparencia do RPC -- que faz uma chamada remota parecer local -- pode levar um desenvolvedor a tomar uma decisao de design errada?*

No Lab 04 a gente viu que tentar esconder completamente toda a complexidade de um sistema distribuido pode ser mais perigoso do que util. No RPC isso se manifesta na **transparencia de acesso**: `proxy.somar(7, 5)` parece exatamente igual a chamar uma funcao local. O problema e que uma funcao local ou retorna ou levanta uma excecao previsivel -- uma chamada de rede pode falhar de formas muito mais estranhas.

O cenario classico de decisao errada: imagine um sistema de pagamentos onde o desenvolvedor chama `proxy.debitar_conta(user_id, valor)` sem colocar timeout nem tratar o caso de falha de rede. O servidor processa o debito, mas a resposta se perde na rede. O cliente nao recebeu confirmacao, entao tenta de novo. O servidor processa pela segunda vez. Debito duplo. Isso acontece porque a transparencia do RPC fez o desenvolvedor esquecer de pensar em **semantica de execucao** -- especificamente, se a operacao e *at-most-once*, *at-least-once* ou *exactly-once*. Numa funcao local essa pergunta nao existe. Numa chamada remota ela e critica, e o RPC esconde exatamente isso.

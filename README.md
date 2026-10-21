# Trabalho de Redes — Cliente/Servidor UDP

Aplicação cliente-servidor desenvolvida em Python utilizando **sockets UDP**.


## Grupo:
* Arthur da Fonte
* Arthur Reis
* Bruno Santana
* Hugo Diego
* Lucas Samuel
* Matheus Freire
* Matheus Fialho
* Miguel Tojal
* Pablo Coelho
* Raul Maia
* Vitor Gadelha

## Como executar

Primeiro, execute o servidor:

```bash
python servidor.py
```

Em outro terminal, execute o cliente:

```bash
python cliente.py
```

Exemplo de entrada:

```text
Modo (INDIVIDUAL/LOTE): LOTE
Controle (GBN/SR): GBN
Tamanho do texto: 100
```

## Protocolo

Exemplo de solicitação:

```text
TUDO_BEM;MODO=LOTE;CTRL=GBN;TAM_TEXTO=100
```

Exemplo de resposta:

```text
TUDO_BEM_SIM;MODO=LOTE;CTRL=GBN;TAM_TEXTO=100;JANELA=5
```
<details>
<summary>Entrega 1</summary>

  ## Entrega 1 -

## Funcionalidades

Durante o handshake são definidos:

- **Modo de envio:** `INDIVIDUAL` ou `LOTE`
- **Controle de transmissão:** `GBN` (Go-Back-N) ou `SR` (Repetição Seletiva)
- **Tamanho do texto:** informado pelo cliente
- **Tamanho da janela:** definido pelo servidor

O servidor valida os parâmetros recebidos e responde aceitando ou recusando a comunicação.

## Estrutura

```text
.
├── cliente.py
├── servidor.py
├── protocolo_mensagem.py
└── config.py
```

- `cliente.py` — inicia a comunicação e envia os parâmetros.
- `servidor.py` — recebe, valida e responde ao cliente.
- `protocolo_mensagem.py` — monta e interpreta as mensagens do protocolo.
- `config.py` — configura IP, porta, buffer e valores padrão.

<details>
<summary>Relatório - Entrega 1</summary>
  
# Cliente/Servidor UDP - Relatório 1 - Primeira Parte Implementação

# Relatório de Implementação — Cliente/Servidor UDP e Handshake

## 1. Objetivo

Implementar uma aplicação cliente-servidor utilizando **sockets UDP**, responsável por realizar um handshake inicial antes da transmissão dos dados.

Nesse handshake devem ser definidos o **modo de envio** (individual ou lote), o **controle de transmissão** (Go-Back-N ou Repetição Seletiva), o **tamanho do texto** e o **tamanho inicial da janela de recepção**.

## 2. O que foi feito

- Implementação de cliente e servidor utilizando UDP.
- Criação de um protocolo textual próprio para troca de mensagens.
- Implementação do handshake `TUDO_BEM` → `TUDO_BEM_SIM` ou `RECUSADO`.
- Negociação dos parâmetros:
  - `MODO`: `INDIVIDUAL` ou `LOTE`;
  - `CTRL`: `GBN` ou `SR`;
  - `TAM_TEXTO`: tamanho informado pelo cliente;
  - `JANELA`: tamanho inicial definido pelo servidor.
- Validação do modo e do controle escolhidos.
- Validação de tamanho mínimo do texto (`30`).
- Respostas de recusa com identificação do motivo.
- Centralização das configurações de IP, porta, buffer e janela.

## 3. Como cheguei lá / decisões tomadas

Foi utilizado **UDP (`SOCK_DGRAM`)** porque o objetivo do projeto é posteriormente implementar mecanismos de confiabilidade, como Go-Back-N e Repetição Seletiva, sem utilizar as garantias já fornecidas pelo TCP.

O protocolo de aplicação foi criado em formato textual:

```text
TIPO;CHAVE=VALOR;CHAVE=VALOR
```

Por exemplo:

```text
TUDO_BEM;MODO=LOTE;CTRL=GBN;TAM_TEXTO=100
```

Esse formato foi escolhido por ser simples de montar, visualizar e testar.

Também foi decidido separar `MODO` de `CTRL`, pois são parâmetros diferentes: `MODO` determina envio individual ou em lote, enquanto `CTRL` determina o futuro mecanismo de confiabilidade.

O **servidor ficou responsável pela validação final** e pela definição da janela inicial (`JANELA=5`). O cliente apenas propõe os demais parâmetros.

## 4. Arquivos alterados

- **`cliente.py`** — recebe os parâmetros do usuário, envia o handshake e processa a resposta do servidor.
- **`servidor.py`** — recebe e valida o handshake, aceita ou recusa a solicitação e informa a janela.
- **`protocolo_mensagem.py`** — implementa `montar()` e `desmontar()` para codificar e interpretar o protocolo textual.
- **`config.py`** — concentra IP, porta, tamanho do buffer, tamanho mínimo do texto e janela padrão.

## 5. Como testar/validar

Primeiro, executar o servidor:

```bash
python servidor.py
```

Em outro terminal, executar:

```bash
python cliente.py
```

Informar, por exemplo:

```text
Modo: LOTE
Controle: GBN
Tamanho do texto: 100
```

O cliente deverá enviar:

```text
TUDO_BEM;MODO=LOTE;CTRL=GBN;TAM_TEXTO=100
```

e receber uma resposta semelhante a:

```text
TUDO_BEM_SIM;MODO=LOTE;CTRL=GBN;TAM_TEXTO=100;JANELA=5
```

Também podem ser testados valores inválidos de modo, controle e tamanhos menores que `30`, que devem resultar em `RECUSADO`.

### Relatório/ Diário de Aprendizagem Uso de IA⬇️ :
[![Read the Docs](https://img.shields.io/badge/Read%20the%20Docs-%23000000.svg?style=for-the-badge&logo=readthedocs&logoColor=white)](https://docs.google.com/document/d/15zSdHppBRYHB8-EuIskW2odFl35smm78s4MK0QK3myk/edit?tab=t.to6ynmibpxae)

### Caso deseje saber mais sobre a implementação de forma *Técnica* acesse o documento abaixo ⬇️ :
[![Read the Docs](https://img.shields.io/badge/Read%20the%20Docs-%23000000.svg?style=for-the-badge&logo=readthedocs&logoColor=white)](https://docs.google.com/document/d/12iL8a6ONzk0YM9PACcytHFAVXDBGYF2RQswipV-NIGY/edit?usp=sharing)



</details>

</details>

<details>
<summary>Entrega 2</summary>

## Entrega 2 — Protocolo sem erros e perdas

### Funcionalidades

Durante o handshake, o cliente informa o modo de envio (`INDIVIDUAL` ou `LOTE`), o controle de transmissão (`GBN` ou `SR`) e o tamanho do texto. O servidor valida os parâmetros e, se aceitar a comunicação, informa o tamanho da janela.

O cliente divide o texto em fragmentos de até quatro caracteres. Cada pacote de dados contém um número de sequência e um checksum. No modo `INDIVIDUAL`, o cliente envia um pacote por vez; no modo `LOTE`, pode enviar pacotes até preencher a janela. O servidor confirma os pacotes cumulativamente no GBN e individualmente no SR.

Depois de receber todos os fragmentos, o servidor monta o texto e confirma o encerramento com a sequência `FIM` → `FIM_ACK` → `FIM_CONFIRM`.

A implementação também contém retransmissões por timeout ou NACK. Essas são extensões para recuperação; no caminho normal, sem erros e perdas, não são acionadas.


### Especificação das mensagens

Formato geral: `TIPO;CAMPO=valor;CAMPO=valor|payload`. O `|` separa o cabeçalho do payload, e o servidor corta só no primeiro `|`. Por isso o texto do usuário pode ter `;`, `=` e `|`.

| Mensagem | Direção | Campos | Exemplo |
|---|---|---|---|
| `DADOS` | Cliente → Servidor | `SEQ`, `CHK` e payload de até 4 caracteres | `DADOS;SEQ=0;CHK=12135\|ola,` |
| `ACK` | Servidor → Cliente | `SEQ`, `JANELA` | `ACK;SEQ=0;JANELA=5\|` |
| `NACK` | Servidor → Cliente | `SEQ`, `JANELA` | `NACK;SEQ=3;JANELA=5\|` |
| `FIM` | Cliente → Servidor | `TOTAL` de pacotes | `FIM;TOTAL=8\|` |
| `FIM_ACK` | Servidor → Cliente | `TOTAL` | `FIM_ACK;TOTAL=8\|` |
| `FIM_CONFIRM` | Cliente → Servidor | `TOTAL` | `FIM_CONFIRM;TOTAL=8\|` |

- **GBN:** o servidor só aceita o próximo `SEQ` esperado e o `ACK` é cumulativo ("recebi tudo até SEQ").
- **SR:** o servidor guarda os pacotes dentro da janela e o `ACK` é individual, um por `SEQ`.
- **NACK:** é enviado quando o checksum não bate. No GBN o cliente reenvia a janela inteira, no SR só o pacote.
- **Janela:** o servidor informa no `ACK` (de 1 a 5). No modo `INDIVIDUAL` o cliente usa janela 1.

### Checksum

O checksum foi implementado à mão, sem biblioteca, em `checksum.py`. Ele soma o payload em palavras de 16 bits com complemento de 1, igual ao UDP, e inverte os bits no final. O servidor recalcula o valor e compara com o `CHK` recebido: se for igual responde `ACK`, se for diferente responde `NACK`.

<details>
<summary>Relatório - Entrega 2</summary>

# Relatório de Implementação — Protocolo de Transferência UDP

## 1. Objetivo

Implementar a troca de mensagens entre cliente e servidor utilizando UDP, com um protocolo definido para negociar os parâmetros, transferir um texto fragmentado e confirmar o encerramento. Nesta entrega, o fluxo principal considera um canal sem erros e sem perdas.

## 2. O que foi feito

- Implementação da transferência de dados após o handshake.
- Fragmentação do texto em pacotes de até quatro caracteres.
- Inclusão do número de sequência e do checksum nos pacotes de dados.
- Confirmações cumulativas para GBN e individuais para SR.
- Validação dos pacotes recebidos e montagem do texto no servidor.
- Encerramento confirmado por `FIM`, `FIM_ACK` e `FIM_CONFIRM`.
- Inclusão de retransmissões por timeout e NACK como mecanismos adicionais de recuperação.

## 3. Como cheguei lá / decisões tomadas

O protocolo mantém separados o modo de envio e o controle de transmissão. `INDIVIDUAL` limita o envio a um pacote por vez; `LOTE` utiliza a janela definida pelo servidor. O GBN confirma cumulativamente os pacotes recebidos em ordem, enquanto o SR confirma cada pacote individualmente.

Cada pacote de dados inclui um número de sequência e um checksum. O servidor verifica o checksum antes de aceitar o conteúdo. Quando todos os fragmentos esperados chegam, o servidor os organiza e reconstrói o texto.

Foi adicionado um encerramento em três mensagens para que cliente e servidor confirmem o fim da transferência. Os timeouts e as retransmissões estão implementados como complemento; o fluxo de referência desta entrega é o caminho sem erros ou perdas.

## 4. Arquivos alterados

- [`cliente.py`](./cliente.py) — fragmenta e envia o texto, processa ACK/NACK, controla a janela, retransmite pacotes quando necessário e confirma o encerramento.
- [`servidor.py`](./servidor.py) — valida pacotes e checksums, envia confirmações, reconstrói o texto e conclui o handshake de encerramento.
- [`config.py`](./config.py) — define o timeout e os tipos de mensagem usados no encerramento (`FIM_ACK` e `FIM_CONFIRM`).

O protocolo também utiliza os módulos de apoio [`protocolo_mensagem.py`](./protocolo_mensagem.py), para montar, interpretar e fragmentar mensagens, e [`checksum.py`](./checksum.py), para calcular e validar checksums.

## 5. Principais funções

Em [`cliente.py`](./cliente.py):

- `enviar_dados()` monta e envia um pacote com sequência e checksum.
- `receber_controle()` recebe e interpreta mensagens de controle do servidor.
- `retransmitir()` reenvia um ou mais pacotes pendentes.

Em [`servidor.py`](./servidor.py):

- `aguardar_confirmacao_final()` aguarda o `FIM_CONFIRM` e reenvia o `FIM_ACK` caso receba novamente o `FIM`.

Em [`protocolo_mensagem.py`](./protocolo_mensagem.py):

- `montar()` e `desmontar()` montam e interpretam mensagens de controle.
- `montar_pacote()` e `desmontar_pacote()` montam e interpretam pacotes com cabeçalho e payload.
- `fragmentar()` divide o texto em partes menores.

Em [`checksum.py`](./checksum.py):

- `calcular_checksum()` calcula o checksum do conteúdo.
- `checksum_valido()` verifica se o checksum recebido corresponde ao conteúdo.

## 6. Como testar/validar

Primeiro, executar o servidor:

```bash
python servidor.py
```

Em outro terminal, executar:

```bash
python cliente.py
```

Testar as combinações `INDIVIDUAL` com `GBN`, `INDIVIDUAL` com `SR`, `LOTE` com `GBN` e `LOTE` com `SR`. Nos testes manuais realizados, as quatro combinações concluíram o fluxo sem perdas: o servidor recebeu e montou o texto, e a troca `FIM` → `FIM_ACK` → `FIM_CONFIRM` foi concluída.

### Relatório / Diário de Aprendizagem - Entrega 2 ⬇️:
[![Read the Docs](https://img.shields.io/badge/Read%20the%20Docs-%23000000.svg?style=for-the-badge&logo=readthedocs&logoColor=white)](https://docs.google.com/document/d/1RJ7ZuJGJtmab1CgMhnQLUB5gL-h0BEnbhnKPvbHM0Wo/edit?usp=sharing)
</details>

</details>

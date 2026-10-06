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

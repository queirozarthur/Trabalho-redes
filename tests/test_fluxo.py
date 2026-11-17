import os
from pathlib import Path
import queue
import runpy
import socket
import threading
import unittest
from unittest.mock import patch

import config
from protocolo_mensagem import desmontar_pacote_integro
from test_transferencia import PonteUDP, TEXTO


PASTA = Path(__file__).resolve().parents[1]


class RedeSimulada:
    def __init__(self):
        self.enderecos = {}
        self.porta = 40000

    def criar_socket(self, *args):
        self.porta += 1
        return SocketSimulado(self, ("127.0.0.1", self.porta))


class SocketSimulado:
    def __init__(self, rede, endereco):
        self.rede = rede
        self.endereco = endereco
        self.fila = queue.Queue()
        self.timeout = None
        self.rede.enderecos[endereco] = self

    def bind(self, endereco):
        if endereco[1] == 0:
            return
        self.rede.enderecos.pop(self.endereco)
        self.endereco = endereco
        self.rede.enderecos[endereco] = self

    def getsockname(self):
        return self.endereco

    def settimeout(self, timeout):
        self.timeout = timeout

    def sendto(self, dados, destino):
        receptor = self.rede.enderecos.get(destino)
        if receptor is not None:
            receptor.fila.put((dados, self.endereco))
        return len(dados)

    def recvfrom(self, tamanho):
        try:
            dados, origem = self.fila.get(timeout=self.timeout)
            return dados[:tamanho], origem
        except queue.Empty:
            raise socket.timeout() from None

    def close(self):
        self.rede.enderecos.pop(self.endereco, None)


class TestFluxo(unittest.TestCase):
    def executar_fluxo(self, modo, controle, falha="normal"):
        rede = RedeSimulada()
        pronto = threading.Event()
        logs = {"cliente": [], "servidor": []}
        erros = []
        entradas = iter([modo, controle, "100", TEXTO])

        def registrar(*valores, **kwargs):
            nome = threading.current_thread().name
            linha = " ".join(str(valor) for valor in valores)
            logs[nome].append(linha)
            if linha == "Aguardando conexao...":
                pronto.set()

        def executar(nome):
            try:
                runpy.run_path(str(PASTA / f"{nome}.py"), run_name="__main__")
            except BaseException as erro:
                erros.append(erro)

        with patch("socket.socket", rede.criar_socket), \
                patch("builtins.input", lambda mensagem: next(entradas)), \
                patch("builtins.print", registrar), \
                patch.dict(os.environ, {"REDES_CHAVE_HEX": "000102030405060708090a0b0c0d0e0f"}), \
                patch.object(config, "TIMEOUT", 0.1), \
                patch.object(config, "ENDERECO_SERVIDOR", ("127.0.0.1", 8082)):
            ponte = PonteUDP(config.ENDERECO_SERVIDOR, falha)
            ponte.thread.start()
            servidor = threading.Thread(target=executar, args=("servidor",), name="servidor", daemon=True)
            cliente = threading.Thread(target=executar, args=("cliente",), name="cliente", daemon=True)
            try:
                servidor.start()
                self.assertTrue(pronto.wait(timeout=2), str(erros))
                config.ENDERECO_SERVIDOR = ("127.0.0.1", ponte.porta)
                cliente.start()
                cliente.join(timeout=5)
                servidor.join(timeout=2)
                self.assertFalse(cliente.is_alive(), str(logs))
                self.assertFalse(servidor.is_alive(), str(logs))
                self.assertEqual(erros, [], str(erros))
                self.assertIsNone(ponte.erro)
                self.assertIn(f"Texto completo: {TEXTO}", logs["servidor"])
                self.assertTrue(any("[FIM_CONFIRM]" in linha for linha in logs["servidor"]))
                if falha != "normal":
                    self.assertTrue(ponte.aplicada)
                if falha == "nack":
                    self.assertTrue(any("[NACK]" in linha for linha in logs["cliente"]))
                por_sequencia = {}
                for pacote in ponte.pacotes:
                    _, campos, payload = desmontar_pacote_integro(pacote)
                    seq = int(campos["SEQ"])
                    self.assertEqual(len(bytes.fromhex(payload)), len(TEXTO[seq * 4:seq * 4 + 4].encode("utf-8")))
                    if seq in por_sequencia:
                        self.assertEqual(pacote, por_sequencia[seq])
                    por_sequencia[seq] = pacote
                self.assertNotIn("Olá", "".join(ponte.pacotes))
            finally:
                ponte.fechar()

    def test_quatro_combinacoes_sem_falhas(self):
        for modo in ["INDIVIDUAL", "LOTE"]:
            for controle in ["GBN", "SR"]:
                with self.subTest(modo=modo, controle=controle):
                    self.executar_fluxo(modo, controle)

    def test_recuperacao_com_falhas(self):
        falhas = ["perder_dados", "corromper_payload", "corromper_seq", "duplicar",
                  "inverter", "perder_ack", "corromper_ack", "perder_fim_ack", "nack"]
        for controle in ["GBN", "SR"]:
            for falha in falhas:
                with self.subTest(controle=controle, falha=falha):
                    self.executar_fluxo("LOTE", controle, falha)

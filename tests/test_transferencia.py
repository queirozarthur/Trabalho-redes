import os
from pathlib import Path
import socket
import subprocess
import sys
import tempfile
import threading
import time
import unittest

from protocolo_mensagem import desmontar_pacote_integro, montar_pacote_integro


PASTA = Path(__file__).resolve().parents[1]
TEXTO = "😀😃😄😁 Olá;=| transferência cifrada com acentos e símbolos!"


class PonteUDP:
    def __init__(self, servidor, falha):
        self.servidor = servidor
        self.falha = falha
        self.aplicada = False
        self.cliente = None
        self.adiado = None
        self.pacotes = []
        self.erro = None
        self.parar = threading.Event()
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.socket.bind(("127.0.0.1", 0))
        self.porta = self.socket.getsockname()[1]
        self.socket.settimeout(0.05)
        self.thread = threading.Thread(target=self.executar, daemon=True)

    def executar(self):
        try:
            while not self.parar.is_set():
                try:
                    dados, origem = self.socket.recvfrom(4096)
                except socket.timeout:
                    continue
                resposta = origem == self.servidor
                if not resposta:
                    self.cliente = origem
                destino = self.cliente if resposta else self.servidor
                texto = dados.decode("utf-8")
                if texto.startswith("DADOS;") and not resposta:
                    self.pacotes.append(texto)
                    if not self.aplicada:
                        if self.falha == "perder_dados":
                            self.aplicada = True
                            continue
                        if self.falha == "corromper_payload":
                            dados = dados[:-1] + (b"0" if dados[-1:] != b"0" else b"1")
                            self.aplicada = True
                        elif self.falha == "corromper_seq":
                            dados = dados.replace(b"SEQ=0;", b"SEQ=1;", 1)
                            self.aplicada = True
                        elif self.falha == "nack":
                            tipo, campos, _ = desmontar_pacote_integro(texto)
                            dados = montar_pacote_integro(tipo, campos, "zz").encode()
                            self.aplicada = True
                        elif self.falha == "duplicar":
                            self.socket.sendto(dados, destino)
                            self.aplicada = True
                        elif self.falha == "inverter":
                            if self.adiado is None:
                                self.adiado = dados
                                continue
                            self.socket.sendto(dados, destino)
                            dados = self.adiado
                            self.aplicada = True
                if not self.aplicada and resposta:
                    if self.falha == "perder_ack" and texto.startswith("ACK;"):
                        self.aplicada = True
                        continue
                    if self.falha == "perder_fim_ack" and texto.startswith("FIM_ACK;"):
                        self.aplicada = True
                        continue
                    if self.falha == "corromper_ack" and texto.startswith("ACK;"):
                        dados = dados.replace(b"JANELA=5", b"JANELA=4", 1)
                        self.aplicada = True
                self.socket.sendto(dados, destino)
        except Exception as erro:
            self.erro = erro

    def fechar(self):
        self.parar.set()
        self.thread.join(timeout=2)
        self.socket.close()


class TestTransferencia(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as receptor:
            receptor.bind(("127.0.0.1", 0))
            receptor.settimeout(0.2)
            with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as emissor:
                emissor.sendto(b"teste", receptor.getsockname())
                try:
                    receptor.recvfrom(16)
                except socket.timeout:
                    raise unittest.SkipTest("O ambiente nao permite receber UDP no loopback")

    def executar_transferencia(self, modo, controle, falha="normal"):
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as reserva:
            reserva.bind(("127.0.0.1", 0))
            porta_servidor = reserva.getsockname()[1]
        ponte = PonteUDP(("127.0.0.1", porta_servidor), falha)
        ambiente = dict(os.environ, PYTHONIOENCODING="utf-8", PYTHONUNBUFFERED="1",
                        REDES_CHAVE_HEX="000102030405060708090a0b0c0d0e0f")
        processos = []
        with tempfile.TemporaryDirectory() as pasta:
            caminho_log = Path(pasta) / "servidor.log"
            with caminho_log.open("w", encoding="utf-8") as log:
                try:
                    ponte.thread.start()
                    servidor = subprocess.Popen(self.comando("servidor", porta_servidor),
                                                cwd=PASTA, env=ambiente, stdout=log,
                                                stderr=subprocess.STDOUT)
                    processos.append(servidor)
                    limite = time.monotonic() + 5
                    while "Aguardando conexao" not in caminho_log.read_text(encoding="utf-8"):
                        if servidor.poll() is not None or time.monotonic() >= limite:
                            self.fail(caminho_log.read_text(encoding="utf-8"))
                        time.sleep(0.01)
                    cliente = subprocess.Popen(self.comando("cliente", ponte.porta),
                                               cwd=PASTA, env=ambiente, stdin=subprocess.PIPE,
                                               stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                                               text=True, encoding="utf-8")
                    processos.append(cliente)
                    try:
                        saida, _ = cliente.communicate(f"{modo}\n{controle}\n100\n{TEXTO}\n", timeout=10)
                    except subprocess.TimeoutExpired:
                        cliente.kill()
                        saida, _ = cliente.communicate(timeout=3)
                        self.fail(f"Cliente: {saida}\nServidor: {caminho_log.read_text(encoding='utf-8')}\nPonte: {ponte.erro!r}")
                    servidor.wait(timeout=5)
                    recebido = caminho_log.read_text(encoding="utf-8")
                    self.assertEqual(cliente.returncode, 0, saida)
                    self.assertEqual(servidor.returncode, 0, recebido)
                    self.assertIn(f"Texto completo: {TEXTO}", recebido)
                    self.assertIn("[FIM_CONFIRM]", recebido)
                    self.assertIsNone(ponte.erro)
                    if falha != "normal":
                        self.assertTrue(ponte.aplicada)
                    if falha == "nack":
                        self.assertIn("[NACK]", saida)
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
                    for processo in processos:
                        if processo.poll() is None:
                            processo.kill()
                        processo.wait(timeout=3)
                        for fluxo in [processo.stdin, processo.stdout, processo.stderr]:
                            if fluxo is not None:
                                fluxo.close()
                    ponte.fechar()

    def comando(self, programa, porta):
        codigo = (
            "import config, runpy; "
            f"config.ENDERECO_SERVIDOR = ('127.0.0.1', {porta}); "
            "config.TIMEOUT = 0.15; "
            f"runpy.run_path('{programa}.py', run_name='__main__')"
        )
        return [sys.executable, "-u", "-c", codigo]

    def test_quatro_combinacoes_sem_falhas(self):
        for modo in ["INDIVIDUAL", "LOTE"]:
            for controle in ["GBN", "SR"]:
                with self.subTest(modo=modo, controle=controle):
                    self.executar_transferencia(modo, controle)

    def test_recuperacao_com_falhas(self):
        falhas = ["perder_dados", "corromper_payload", "corromper_seq", "duplicar",
                  "inverter", "perder_ack", "corromper_ack", "perder_fim_ack", "nack"]
        for controle in ["GBN", "SR"]:
            for falha in falhas:
                with self.subTest(controle=controle, falha=falha):
                    self.executar_transferencia("LOTE", controle, falha)

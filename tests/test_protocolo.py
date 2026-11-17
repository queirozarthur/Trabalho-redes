import os
import unittest
from unittest.mock import patch

from config import carregar_chave
from protocolo_mensagem import (
    desmontar_pacote_integro,
    montar_pacote_integro,
)


class TestProtocolo(unittest.TestCase):
    def test_tipos_de_pacote(self):
        for tipo in ["DADOS", "ACK", "NACK", "FIM", "FIM_ACK", "FIM_CONFIRM"]:
            pacote = montar_pacote_integro(tipo, {"SEQ": 3}, "ab01")
            recebido, campos, payload = desmontar_pacote_integro(pacote)
            self.assertEqual((recebido, campos["SEQ"], payload), (tipo, "3", "ab01"))

    def test_recusa_alteracoes(self):
        pacote = montar_pacote_integro("DADOS", {"SEQ": 3}, "ab01")
        for antigo, novo in [("DADOS", "DADOT"), ("SEQ=3", "SEQ=4"),
                              ("ab01", "ab00")]:
            with self.assertRaises(ValueError):
                desmontar_pacote_integro(pacote.replace(antigo, novo))

    def test_recusa_campos_repetidos_e_checksum_ausente(self):
        for pacote in ["DADOS;SEQ=3;SEQ=4;CHK=0|ab", "DADOS;SEQ=0|ab"]:
            with self.assertRaises(ValueError):
                desmontar_pacote_integro(pacote)

    def test_ordem_dos_campos_nao_altera_checksum(self):
        pacote = montar_pacote_integro("ACK", {"SEQ": 3, "JANELA": 5})
        pacote = pacote.replace("SEQ=3;JANELA=5", "JANELA=5;SEQ=3")
        self.assertEqual(desmontar_pacote_integro(pacote)[1]["SEQ"], "3")

    def test_chave_do_ambiente(self):
        valor = "000102030405060708090a0b0c0d0e0f"
        with patch.dict(os.environ, {"REDES_CHAVE_HEX": valor}):
            self.assertEqual(carregar_chave(), bytes(range(16)))
        for valor in ["", "abc", "x" * 32, " " * 32]:
            with patch.dict(os.environ, {"REDES_CHAVE_HEX": valor}):
                with self.assertRaises(ValueError):
                    carregar_chave()

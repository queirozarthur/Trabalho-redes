import unittest

from checksum import calcular_checksum, checksum_valido


class TestChecksum(unittest.TestCase):
    def test_valores_calculados_manualmente(self):
        for dados, esperado in [(b"", 0xFFFF), (b"A", 0xBEFF),
                                (b"AB", 0xBEBD), (b"ABC", 0x7BBD),
                                (bytes.fromhex("ffff0001"), 0xFFFE)]:
            with self.subTest(dados=dados):
                self.assertEqual(calcular_checksum(dados), esperado)

    def test_texto_e_bytes_utf8_tem_mesmo_resultado(self):
        texto = "Olá 🌎"
        self.assertEqual(calcular_checksum(texto), calcular_checksum(texto.encode("utf-8")))

    def test_detecta_alteracao_de_um_bit(self):
        dados = b"mensagem original"
        checksum = calcular_checksum(dados)
        self.assertTrue(checksum_valido(dados, checksum))
        for posicao in range(len(dados)):
            for bit in range(8):
                alterado = bytearray(dados)
                alterado[posicao] ^= 1 << bit
                self.assertFalse(checksum_valido(alterado, checksum))

    def test_recusa_checksum_fora_do_intervalo(self):
        for valor in [-1, 65536, "123", None]:
            self.assertFalse(checksum_valido(b"abc", valor))

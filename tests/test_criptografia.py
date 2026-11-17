import unittest

from criptografia import AES128


class TestCriptografia(unittest.TestCase):
    def test_bloco_fips_197(self):
        aes = AES128(bytes.fromhex("000102030405060708090a0b0c0d0e0f"))
        bloco = bytes.fromhex("00112233445566778899aabbccddeeff")
        esperado = bytes.fromhex("69c4e0d86a7b0430d8cdb78070b4c55a")
        self.assertEqual(aes.cifrar_bloco(bloco), esperado)

    def test_ctr_nist_sp_800_38a(self):
        aes = AES128(bytes.fromhex("2b7e151628aed2a6abf7158809cf4f3c"))
        contador = bytes.fromhex("f0f1f2f3f4f5f6f7f8f9fafbfcfdfeff")
        original = bytes.fromhex(
            "6bc1bee22e409f96e93d7e117393172a"
            "ae2d8a571e03ac9c9eb76fac45af8e51"
            "30c81c46a35ce411e5fbc1191a0a52ef"
            "f69f2445df4f9b17ad2b417be66c3710"
        )
        esperado = bytes.fromhex(
            "874d6191b620e3261bef6864990db6ce"
            "9806f66b7970fdff8617187bb9fffdff"
            "5ae4df3edbd5d35e5b4f09020db03eab"
            "1e031dda2fbe03d1792170a0f3009cee"
        )
        self.assertEqual(aes.aplicar_ctr(original, contador), esperado)
        self.assertEqual(aes.aplicar_ctr(esperado, contador), original)
        self.assertEqual(aes.aplicar_ctr(original[:23], contador), esperado[:23])

    def test_fragmentos_independentes(self):
        aes = AES128(bytes(range(16)))
        nonce = bytes(range(12))
        original = "😀á|=".encode("utf-8")
        primeiro = aes.aplicar_fragmento(original, nonce, 0)
        segundo = aes.aplicar_fragmento(original, nonce, 1)
        self.assertNotEqual(primeiro, segundo)
        self.assertNotEqual(primeiro, aes.aplicar_fragmento(original, bytes(12), 0))
        self.assertEqual(aes.aplicar_fragmento(segundo, nonce, 1), original)
        self.assertEqual(aes.aplicar_fragmento(original, nonce, 0), primeiro)

    def test_limites(self):
        with self.assertRaises(ValueError):
            AES128(b"curta")
        aes = AES128(bytes(16))
        for dados, nonce, seq in [(bytes(17), bytes(12), 0),
                                  (b"a", bytes(11), 0),
                                  (b"a", bytes(12), -1),
                                  (b"a", bytes(12), 1 << 32)]:
            with self.assertRaises(ValueError):
                aes.aplicar_fragmento(dados, nonce, seq)
        with self.assertRaises(ValueError):
            aes.aplicar_ctr(bytes(17), bytes([255]) * 16)

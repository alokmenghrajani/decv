#!/usr/local/bin/python

from Crypto.Random import get_random_bytes, random
import sys
import argparse
import time
import humanfriendly
from binascii import hexlify
import os

def deffered_imports():
    # We want to control picking openssl vs libsecp256k1 at runtime, so we defer some imports
    import pycoin.ecdsa.native.openssl
    import pycoin.ecdsa.native.secp256k1

    global network, sigdecode_der, sigencode_der, secp256k1
    from pycoin.symbols.btc import network
    from pycoin.satoshi.der import sigdecode_der, sigencode_der
    from pycoin.ecdsa import secp256k1

class Progress:
    def __init__(self, total):
        self.total = total
        self.start = time.time()
        self.output_size = 0
        self.previous_update = 0

    def print(self, current):
        if sys.stdout.isatty():
            # Don't print progress unless stdout is redirected
            return
        if current + 1 == self.total:
            # Clear progress when we are done
            sys.stderr.write('\r{blank}\r'.format(blank = "".ljust(self.output_size)))
            return
        if (time.time() - self.previous_update < 1):
            return
        progress = str(round((current + 1.0) / self.total * 100, 2))+"%"
        elapsed = round(time.time() - self.start, 0)
        eta = round(elapsed / (current + 1.0) * (self.total - current - 1.0), 0)
        output = "progress:{progress} | elapsed:{elapsed} | eta:{eta}".format(progress=progress, elapsed=humanfriendly.format_timespan(elapsed), eta=humanfriendly.format_timespan(eta))
        output = output.ljust(self.output_size)
        self.output_size = len(output)
        sys.stderr.write('\r{output}'.format(output = output))
        self.previous_update = time.time()

# Use the fact that openssl doesn't return low s to tell libsecp256k1 and openssl apart.
# (see also https://github.com/richardkiss/pycoin/issues/178).
def detect_crypto_lib():
    key = network.keys.bip32_seed(bytearray(range(0, 16)))
    r, s1 = sigdecode_der(key.sign(bytearray(range(0, 32))))
    s2 = (secp256k1._r - s1) % secp256k1._r
    return "libsecp256k1" if s1 < s2 else "openssl"

def sign(key, msg):
    sig = key.sign(msg)

    # openssl doesn't return low s, so we have to compute it
    r, s1 = sigdecode_der(sig)
    s2 = (secp256k1._r - s1) % secp256k1._r

    return str(hexlify(sigencode_der(r, s1 if s1 < s2 else s2)), "utf-8")

def generate_random_chain():
    len = random.randint(0, 4)
    path = ["m", "0'"]
    for i in range(0, len):
        val = str(random.randint(0, 200))
        if random.randint(0, 1) == 1:
            val = val + "'"
        path.append(val)
    return "/".join(path)

def generate(args):
    # generate some test vectors
    progress = Progress(args.n)
    for i in range(0, args.n):
        progress.print(i)

        # generate a random seed
        seed_size = random.randint(16, 64)
        seed = get_random_bytes(seed_size)

        # generate a random chain
        chain = generate_random_chain()

        key = network.keys.bip32_seed(seed)
        key = key.subkey_for_path(chain[2:]) # remove m/ from the chain

        # generate a random message hash
        msg = get_random_bytes(32)

        # sign
        sig = sign(key, msg)
        print("{seed},{chain},{xpub},{xpriv},{hash},{sig}".format(seed=str(hexlify(seed), "utf-8"), chain=chain, xpub=key.hwif(), xpriv=key.hwif(as_private=True), hash=str(hexlify(msg), "utf-8"), sig=sig))

def verify(args):
    rows = 0
    for line in sys.stdin:
        line = line.rstrip()
        (seed, chain, expected_xpub, expected_xpriv, msg, expected_sig) = line.split(",")
        key = network.keys.bip32_seed(bytearray.fromhex(seed))
        key = key.subkey_for_path(chain[2:]) # remove m/ from the chain

        if expected_xpub != key.hwif():
            raise Exception("xpub mismatch ({expected} != {computed})".format(expected = expected_xpub, computed = key.hwif()))

        if expected_xpriv != key.hwif(as_private=True):
            raise Exception("xpriv mismatch ({expected} != {computed})".format(expected = expected_xpriv, computed = key.hwif(as_private=True)))

        sig = sign(key, bytearray.fromhex(msg))

        if expected_sig != sig:
            raise Exception("sig mismatch ({expected} != {computed})".format(expected = expected_sig, computed = sig))

        rows = rows + 1

    print("verified: {rows} signatures".format(rows = rows))

def main():
    parser = argparse.ArgumentParser(description='Generate or validate Deterministic ECDSA signatures.')
    parser.add_argument('--libsecp256k1', action='store_true', help='use libsecp256k1')
    parser.add_argument('--openssl', action='store_true', help='use openssl')
    subparsers = parser.add_subparsers(help='sub-command help')
    parser_generate = subparsers.add_parser('generate', help='generate test vectors')
    parser_generate.add_argument('n', metavar='N', type=int, help='generate N test vectors')
    parser_generate.set_defaults(func=generate)
    parser_verify = subparsers.add_parser('verify', help='verify test vectors')
    parser_verify.set_defaults(func=verify)

    args = parser.parse_args()
    # Note: the code below if fragile and assumes that the library will be found (i.e. that PYCOIN_LIBSECP256K1_PATH and
    # PYCOIN_LIBCRYPTO_PATH are set when needed. If one library is not found, pycoin falls back to the other.
    # We can tell which library was loaded because openssl doesn't return low s.
    if args.openssl and not args.libsecp256k1:
        os.environ["PYCOIN_NATIVE"] = "openssl"
    elif args.libsecp256k1 and not args.openssl:
        os.environ["PYCOIN_NATIVE"] = "secp256k1"
        if not hasattr(os.environ, "PYCOIN_LIBSECP256K1_PATH"):
            os.environ["PYCOIN_LIBSECP256K1_PATH"] = "/usr/lib/x86_64-linux-gnu/libsecp256k1.so.0"
    else:
        raise Exception("--libsecp256k1 or --openssl is required")

    deffered_imports()

    if args.openssl and detect_crypto_lib() != "openssl":
        raise Exception("openssl not loaded. Perhaps set PYCOIN_LIBCRYPTO_PATH?")
    if args.libsecp256k1 and detect_crypto_lib() != "libsecp256k1":
        raise Exception("libsecp256k1 not loaded. Perhaps set PYCOIN_LIBSECP256K1_PATH?")

    if not hasattr(args, "func"):
        raise Exception("generate or verify is required")
    args.func(args)

main()

# Deterministic ECDSA Cross Validation (DECV)

The purpose of this repo is to cross validate various different deterministic ECDSA implementations
([libsecp256k1](https://github.com/bitcoin-core/secp256k1), [OpenSSL](https://github.com/openssl/openssl),
[Trezor](https://github.com/trezor/trezor-firmware)). By verifying that each library produces the exact same
signatures for a large number of test vectors, we are able to confirm (with a high degree of confidence) that each
library is both correct and lacks subliminal channels (also known as kleptograms).

We focus on curve [secp256k1](https://en.bitcoin.it/wiki/Secp256k1) since our application is signing Bitcoin
transactions. Deterministic ECDSA is defined in [rfc6979](https://tools.ietf.org/html/rfc6979).

An ECDSA signature is represented as a pair of values (r, s). All implementations must generate the same r. However,
there exists two valid values for s: s and -s mod n (where n is the order of the group). Another Bitcoin-centric
decision is to always pick the lower s (see [BIP: 62](https://github.com/bitcoin/bips/blob/master/bip-0062.mediawiki), [BIP: 146](https://github.com/bitcoin/bips/blob/master/bip-0146.mediawiki)).

python/decv.py is used to generate test vectors. These test vectors can be saved to a file or can be streamed to any
other implementation. The test vectors also contain BIP32 derivations, which enables writing validation code which
is as close as feasible to actual Bitcoin wallet code.

To learn more about ECDSA backdoors: ["Wallet Security" by Stephan Verbücheln](https://media.ccc.de/v/35c3-9492-wallet_security), ["Deterministic Signatures, Subliminal channels and Hardware wallets" by Sergio Demian Lerner](https://bitslog.com/2014/06/09/deterministic-signatures-subliminal-channels-and-hardware-wallets/).

Note:
- libsecp256k1 and OpenSSL are used via [pycoin](https://github.com/richardkiss/pycoin), a python library.
- trezor is compiled using cmake, with build files copied from [Subzero](https://github.com/square/subzero).

# Running

The easiest way to run the code is to use [Docker](https://www.docker.com/), as following. The code should run fine
without Docker, as long as the various dependencies are available. It is recommended that you validate your crypto
library in an environment identical to your production environment (i.e. it's preferable to validate hardware wallets on
the actual hardware since the underlying library might run different code paths on different processors).

    $ docker build -t decv . && docker run --rm -it decv
    # ./python/decv.py --libsecp256k1 generate 10000 | ./python/decv.py --libsecp256k1 verify
    verified: 10000 signatures
    # ./python/decv.py --libsecp256k1 generate 10000 | ./python/decv.py --openssl verify
    verified: 10000 signatures    
    # ./python/decv.py --libsecp256k1 generate 10000 | ./trezor/build/decv
    verified: 10000 signatures
    # cat bip32_test_vectors.csv | ./python/decv.py --libsecp256k1 verify
    verified: 14 signatures
    # cat bip32_test_vectors.csv | ./python/decv.py --openssl verify
    verified: 14 signatures
    # cat bip32_test_vectors.csv | ./trezor/build/decv
    verified: 14 signatures
    # exit

# Test vector format

The test vectors are emitted using comma separated values (CSV). See following table for the field names and one sample
row.

| seed (hex) | chain | ext pub (base58) | ext priv (base58) | hash of message (hex) | signature (DER encoded, low s, hex) |
|------------|-------|------------------|-------------------|-----------------------|-------------------------------------|
| 78c72a6f7a2a488de34a11c1a7de6ab97133d321 | m/0'/50/41/168'/115 | xpub6FRofRU8HUx9T1cZLAvV46p7EsKL4TK4NXq2H2iVLn2CYBcTUaNbftBMZT9qqEnynndSZVVJhWwJKhER99Sa3Tjt5pS3CnBrrna4bhCNexV | xprvA2STFuwET7PrEXY6E9PUgxsNgqUqezbD1JuRUeJsnSVDfPHJw34M85rsiBjERcEkunJ3kZ4N2Lg5xbbQ3UuastcwHVoF2H2ohpfSc4xV2GL | bd7b0690546402a37af52e513bcdf965c15c4757e82354944552140727e08ede | 304402201e924d772d72030794b25ea216298b57cbc09003f1db90691da1bfe1e292bd850220676f325432f9d14e7873cc64ea74ad88138c8e9a1793931a457523d7f7e4a79a |

# Cross Validated Implementations

| Library       | Version                                  |
|---------------|------------------------------------------|
| OpenSSL       | 1.1.1d                                   |
| libsecp256k1  | 0.1~20170810-2                           |
| trezor-crypto | e6d884b145d0fb6201c0ae76c552547028793df9 |

# Future work

This project is considered complete and no future work is planned. However, we welcome pull requests which verify
additional libraries or which verify existing libraries using different programming language wrappers.

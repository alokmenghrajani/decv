#include <stdio.h>
#include <stdlib.h>

#include "bip32.h"
#include "bip39.h"
#include "curves.h"
#include "string.h"

/**
 * WARNING!
 *
 * The code in this file is only designed to validate the test vectors. The code skips various error checking and should
 * not be used as-is in a production setting.
 *
 * If you are looking for production worthy code, see https://github.com/square/subzero/tree/master/core/src
 */

void memzero(void*, size_t);
int csv_next(char* buffer, char* field);

// We don't care about memzero since we aren't handling any real private keys
void memzero(void* s, size_t n) {
  bzero(s, n);
}

int csv_next(char* buffer, char* field) {
  size_t read = 0;
  while (buffer[read] != '\n' && buffer[read] != ',') {
    field[read] = buffer[read];
    read++;
  }
  field[read] = 0;
  return read;
}

int main(int argc, char** argv) {
  (void) argc; (void) argv;
  char buf_static[1000];
  char *buf;
  char seed_hex[130];
  uint8_t seed[64];
  char chain_str[25];
  char xpub_expected[120];
  char xpub[120];
  char xpriv_expected[120];
  char xpriv[120];
  char hash_hex[65];
  uint8_t hash[32];
  uint8_t sig[64];
  char der_expected[150];
  uint8_t der[73];
  char der_str[150];
  int pos;
  int validated = 0;

  while (fgets(buf_static, sizeof(buf_static), stdin)) {
    buf = buf_static;

    // read seed as hex
    pos = csv_next(buf, seed_hex); buf += pos + 1;

    // convert seed_hex to bytes
    int seed_len = pos / 2;
    for (int i=0; i<seed_len; i++) {
      sscanf(seed_hex + i * 2, "%2hhx", &seed[i]);
    }

    // convert seed to HDNode
    HDNode node;
    int r = hdnode_from_seed(seed, seed_len, SECP256K1_NAME, &node);
    if (r != 1) {
      printf("hdnode_from_seed failed: %d", r);
      return -1;
    }

    // read and process chain
    pos = csv_next(buf, chain_str); buf += pos + 1;
    char *chain = chain_str + 1;
    uint32_t fingerprint;
    while (*chain == '/') {
      fingerprint = hdnode_fingerprint(&node);
      chain++;
      int num = (int)strtol(chain, &chain, 10);
      if (*chain == '\'') {
        chain++;
        hdnode_private_ckd_prime(&node, num);
      } else {
        hdnode_private_ckd(&node, num);
      }
    }

    // read xpub_expected and compare
    pos = csv_next(buf, xpub_expected); buf += pos + 1;

    hdnode_fill_public_key(&node);
    r = hdnode_serialize_public(&node, fingerprint, 0x0488b21e, xpub, sizeof(xpub));
    if (r <= 0) {
      printf("hdnode_serialize_public failed: %d", r);
      return -1;
    }
    if (strcmp(xpub_expected, xpub) != 0) {
      printf("xpub mismatch (%s != %s)", xpub_expected, xpub);
      exit(-1);
    }

    // read xpriv_expected and compare
    pos = csv_next(buf, xpriv_expected); buf += pos + 1;

    r = hdnode_serialize_private(&node, fingerprint, 0x0488ade4, xpriv, sizeof(xpriv));
    if (r <= 0) {
      printf("hdnode_serialize_private failed: %d", r);
      return -1;
    }
    if (strcmp(xpriv_expected, xpriv) != 0) {
      printf("xpriv mismatch (%s != %s)", xpriv_expected, xpriv);
      exit(-1);
    }

    // read hash to sign
    pos = csv_next(buf, hash_hex); buf += pos + 1;
    for (size_t i=0; i<32; i++) {
      sscanf(hash_hex + i * 2, "%2hhx", &hash[i]);
    }

    // sign the hash
    if (hdnode_sign_digest(&node, hash, sig, NULL, NULL) != 0) {
      printf("hdnode_sign_digest failed");
      return -1;
    }

    // read der_expected and compare
    pos = csv_next(buf, der_expected); buf += pos + 1;

    int der_len = ecdsa_sig_to_der(sig, der);
    bzero(der_str, sizeof(der_str));
    for (int i=0; i<der_len; i++) {
      sprintf(der_str + i*2, "%02x", der[i]);
    }

    if (strcmp(der_expected, der_str) != 0) {
      printf("der mismatch (%s != %s)", der_expected, der_str);
      exit(-1);
    }
    validated++;
  }

  printf("verified: %d signatures\n", validated);
}

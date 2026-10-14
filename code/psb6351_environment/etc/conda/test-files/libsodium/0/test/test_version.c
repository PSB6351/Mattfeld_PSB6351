#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include "sodium.h"

int main() {
    unsigned char key[crypto_secretbox_KEYBYTES];
    unsigned char nonce[crypto_secretbox_NONCEBYTES];
    const unsigned char message[] = "native libsodium runtime";
    unsigned char ciphertext[sizeof(message) + crypto_secretbox_MACBYTES];
    unsigned char plaintext[sizeof(message)];
    const char *pkg_version = getenv("PKG_VERSION");
    if (pkg_version == NULL) {
        fprintf(stderr, "$PKG_VERSION env not set\n");
        return 1;
    }

    printf("SODIUM_VERSION_STRING=%s, PKG_VERSION=%s\n", SODIUM_VERSION_STRING, pkg_version);

    if (strncmp(SODIUM_VERSION_STRING, pkg_version, 20) != 0) {
        fprintf(stderr, "version mismatch: SODIUM_VERSION_STRING=%s, PKG_VERSION=%s\n",
                SODIUM_VERSION_STRING, pkg_version);
        return 1;
    }

    if (sodium_init() < 0 || strcmp(sodium_version_string(), pkg_version) != 0) {
        fprintf(stderr, "runtime initialization or version check failed\n");
        return 1;
    }
    crypto_secretbox_keygen(key);
    randombytes_buf(nonce, sizeof(nonce));
    if (crypto_secretbox_easy(ciphertext, message, sizeof(message), nonce, key) != 0 ||
        crypto_secretbox_open_easy(plaintext, ciphertext, sizeof(ciphertext), nonce, key) != 0 ||
        memcmp(plaintext, message, sizeof(message)) != 0) {
        fprintf(stderr, "runtime encryption roundtrip failed\n");
        return 1;
    }
    puts("libsodium runtime encryption roundtrip passed.");

    return 0;
}

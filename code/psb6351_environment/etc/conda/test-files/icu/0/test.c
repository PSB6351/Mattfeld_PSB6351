#include <unicode/uversion.h>

int main(void) {
    UVersionInfo version;
    u_getVersion(version);
    return version[0] == 0;
}

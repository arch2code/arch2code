/* Stands in for common/systemc/xzCheck.cpp in xcheck_tb.sv: it counts the
 * a2c_xz_fail calls per checker instance instead of failing the run, so the
 * testbench can compare each count with what its case expects. */
#include <string.h>

#define XZ_MAX_PATHS 128
#define XZ_TEXT 256

static struct {
    char path[XZ_TEXT];
    char signal[XZ_TEXT];
    int count;
} entries[XZ_MAX_PATHS];
static int used;

static int find(const char *path)
{
    for (int i = 0; i < used; i++) {
        if (strcmp(entries[i].path, path) == 0) {
            return i;
        }
    }
    return -1;
}

void a2c_xz_fail(const char *path, const char *signal)
{
    int i = find(path);
    if (i < 0) {
        if (used == XZ_MAX_PATHS) {
            return;
        }
        i = used++;
        strncpy(entries[i].path, path, XZ_TEXT - 1);
        strncpy(entries[i].signal, signal, XZ_TEXT - 1);
    }
    entries[i].count++;
}

int xz_count(const char *path)
{
    int i = find(path);
    return i < 0 ? 0 : entries[i].count;
}

/* The signal of the instance's first report, or "" when it never reported. */
const char *xz_signal(const char *path)
{
    int i = find(path);
    return i < 0 ? "" : entries[i].signal;
}

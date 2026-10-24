/* Runtime shader compile progress, for the log and the on-screen status line
 * (touch.cpp status_draw). The compile wrapper (marvel_shims.c) reports each
 * compile; CreateFileA reports the cache file the game writes for the shader
 * it just compiled (<hash>.vcode / .pcode / .shader). */
#include "rt.h"
#include <string.h>
#include <time.h>

static pthread_mutex_t g_lock = PTHREAD_MUTEX_INITIALIZER;
static char g_name[64];
static unsigned g_done, g_active;
static uint64_t g_busy_ns, g_last_ns, g_end_ns;

static uint64_t now_ns(void) {
    struct timespec ts;
    clock_gettime(CLOCK_MONOTONIC, &ts);
    return (uint64_t)ts.tv_sec * 1000000000ull + (uint64_t)ts.tv_nsec;
}

void shader_status_note(const char *cache_name) {
    pthread_mutex_lock(&g_lock);
    snprintf(g_name, sizeof g_name, "%s", cache_name);
    pthread_mutex_unlock(&g_lock);
}

uint64_t shader_status_begin(void) {
    pthread_mutex_lock(&g_lock);
    g_active++;
    pthread_mutex_unlock(&g_lock);
    return now_ns();
}

void shader_status_end(uint64_t start) {
    uint64_t t = now_ns(), d = t - start;
    pthread_mutex_lock(&g_lock);
    g_active--;
    g_done++;
    g_busy_ns += d;
    g_last_ns = d;
    g_end_ns = t;
    unsigned n = g_done;
    uint64_t busy = g_busy_ns;
    pthread_mutex_unlock(&g_lock);
    if (n == 1 || n % 25 == 0)
        LOG("shader compiles: %u done, %.0f ms average, last %.0f ms", n, busy / 1e6 / n, d / 1e6);
}

/* Writes the status line; returns 0 when nothing has compiled for 2 s. */
int shader_status_text(char *buf, size_t n) {
    pthread_mutex_lock(&g_lock);
    int show = g_active || (g_done && now_ns() - g_end_ns < 2000000000ull);
    if (show)
        snprintf(buf, n, "COMPILING SHADERS: %u DONE, LAST %s (%.0f MS EACH)", g_done, g_name,
                 g_done ? g_busy_ns / 1e6 / g_done : 0.0);
    pthread_mutex_unlock(&g_lock);
    return show;
}

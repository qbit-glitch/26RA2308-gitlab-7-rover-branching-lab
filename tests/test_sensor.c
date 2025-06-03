/* test_sensor.c - unit test for the ultrasonic range reader */
#include <stdio.h>

#include "sensor.h"

struct range_case {
    const char *name;
    int echo_ms;
    int expected_cm;
};

int main(void)
{
    const struct range_case cases[] = {
        {"near object", 2, 34},
        {"mid-range object", 10, 171},
        {"far object", 20, 343},
        {"no echo", 60, SENSOR_NO_ECHO},
    };
    const int count = (int)(sizeof cases / sizeof cases[0]);
    int failed = 0;

    for (int i = 0; i < count; i++) {
        int got = sensor_read_cm(cases[i].echo_ms);
        if (got == cases[i].expected_cm) {
            printf("PASS %s (%d ms echo): %d cm\n", cases[i].name, cases[i].echo_ms, got);
        } else {
            printf("FAIL %s (%d ms echo): expected %d cm, got %d cm\n",
                   cases[i].name, cases[i].echo_ms, cases[i].expected_cm, got);
            failed++;
        }
    }
    if (failed == 0) {
        printf("ALL TESTS PASSED\n");
        return 0;
    }
    printf("%d of %d checks FAILED\n", failed, count);
    return 1;
}

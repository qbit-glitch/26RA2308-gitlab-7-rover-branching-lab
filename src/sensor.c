/* sensor.c - ultrasonic range reader for the Kestrel-1 rover */
#include "sensor.h"
#include "sensor_limits.h"

int sensor_read_cm(int echo_ms)
{
    if (echo_ms < 0 || echo_ms > SENSOR_TIMEOUT_MS) {
        return SENSOR_NO_ECHO;
    }
    /* sound travels about 343 m/s and the echo covers the distance twice */
    return (echo_ms * 343) / 20;
}

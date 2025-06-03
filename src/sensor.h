#ifndef SENSOR_H
#define SENSOR_H

#define SENSOR_NO_ECHO (-1)

/* Distance in cm for an echo that took echo_ms milliseconds, or SENSOR_NO_ECHO. */
int sensor_read_cm(int echo_ms);

#endif

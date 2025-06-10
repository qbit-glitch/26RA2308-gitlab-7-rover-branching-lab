#ifndef CONTROLLER_H
#define CONTROLLER_H

/* Controller module interface.
 *
 * move_forward: drive straight at 'speed' (0 to 100 percent).
 * turn_left:    rotate counter-clockwise by 'degrees'.
 */
void move_forward(int speed);
void turn_left(int degrees);

#endif

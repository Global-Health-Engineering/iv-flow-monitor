#ifndef UI_H
#define UI_H

#include <stdbool.h>
#include <stdint.h>

enum ui_state_e   { UI_RUN, UI_SET, UI_ALARM };
enum ui_button_e  { BTN_MINUS, BTN_PLUS, BTN_MODE, BTN_MUTE };
enum alarm_id_e   { ALARM_NONE, ALARM_FLOW, ALARM_STOP, ALARM_BATT };  /* match your table */

void ui_task(void);
void ui_on_button(enum ui_button_e btn, bool long_press);

void ui_alarm_start(enum alarm_id_e id);
void ui_alarm_clear(void);

#endif /* UI_H */

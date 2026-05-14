#ifndef BUTTONS_H
#define BUTTONS_H

#include "main.h"

void Buttons_Poll(void);

/* Short-press events: fire on release if the press was below the long
   threshold. One-shot — consume from one place. */
uint8_t Buttons_MutePressed(void);
uint8_t Buttons_ModePressed(void);
uint8_t Buttons_ResPressed(void);

/* Long-press events: fire on release if the press was held >= 700 ms.
   If a long-press fires, the matching short-press does NOT. One-shot. */
uint8_t Buttons_MuteLongPressed(void);
uint8_t Buttons_ModeLongPressed(void);
uint8_t Buttons_ResLongPressed(void);

extern volatile uint8_t Buttons_MuteState;   /* 1 = released (pull-up idle) */
extern volatile uint8_t Buttons_ModeState;
extern volatile uint8_t Buttons_ResState;

#endif /* BUTTONS_H */

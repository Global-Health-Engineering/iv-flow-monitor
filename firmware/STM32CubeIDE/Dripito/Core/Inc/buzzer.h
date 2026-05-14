#ifndef BUZZER_H
#define BUZZER_H

#include "main.h"
#include <stdint.h>

/* Blocking tone (busy-waits via HAL_Delay). Use only for boot chimes / cal
   confirmation where missing a drop event is acceptable. */
void Buzzer_PlayFreq(uint16_t freq, uint16_t duration_ms);

/* Non-blocking tone control. Start sets the PWM frequency on TIM1_CH1 and
   returns immediately; Stop silences and restores the LED_TOP CH2 duty so
   the optical chain is untouched. Idempotent. */
void Buzzer_StartTone(uint16_t freq);
void Buzzer_Stop(void);

void buzzer_mute(void);

#endif /* BUZZER_H */

#include "buzzer.h"

extern TIM_HandleTypeDef htim1;

static void Buzzer_SetDuty(uint16_t duty)
{
    __HAL_TIM_SET_COMPARE(&htim1, TIM_CHANNEL_1, duty);
}

void Buzzer_PlayFreq(uint16_t freq, uint16_t duration_ms)
{
    uint32_t timer_clk = 1000000;  /* TIM1 clock after prescaler = 64 MHz / (63 + 1) */
    uint32_t period    = timer_clk / freq;

    /* TIM1 is shared with LED_CTRL_TOP (CH2). Save the original ARR and
       CH2 compare so the LED PWM duty/freq is restored after the note. */
    uint32_t saved_arr = __HAL_TIM_GET_AUTORELOAD(&htim1);
    uint32_t saved_ch2 = __HAL_TIM_GET_COMPARE(&htim1, TIM_CHANNEL_2);

    /* Scale the LED CH2 compare to the new ARR so its duty cycle is
       preserved while the buzzer plays. */
    uint32_t scaled_ch2 = (saved_arr ? (saved_ch2 * (period - 1) / saved_arr) : 0);

    __HAL_TIM_SET_AUTORELOAD(&htim1, period - 1);
    __HAL_TIM_SET_COMPARE(&htim1, TIM_CHANNEL_2, scaled_ch2);
    __HAL_TIM_SET_COMPARE(&htim1, TIM_CHANNEL_1, period / 2);  /* 50 % duty */

    HAL_Delay(duration_ms);

    Buzzer_SetDuty(0);
    __HAL_TIM_SET_AUTORELOAD(&htim1, saved_arr);
    __HAL_TIM_SET_COMPARE(&htim1, TIM_CHANNEL_2, saved_ch2);
}

void buzzer_mute(void)
{
    Buzzer_SetDuty(0);
}

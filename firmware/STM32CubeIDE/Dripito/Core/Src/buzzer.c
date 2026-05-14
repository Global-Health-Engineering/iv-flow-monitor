#include "buzzer.h"

extern TIM_HandleTypeDef htim1;

/* Saved state so a non-blocking tone can restore the LED_TOP PWM duty
   without disturbing the optical chain. Only valid while tone_on == 1. */
static uint32_t saved_arr  = 0;
static uint32_t saved_ch2  = 0;
static uint8_t  tone_on    = 0;

static void Buzzer_SetDuty(uint16_t duty)
{
    __HAL_TIM_SET_COMPARE(&htim1, TIM_CHANNEL_1, duty);
}

/* Configure TIM1 ARR for `freq`, scale CH2 (LED_TOP) compare to preserve
   its duty cycle, drive CH1 (buzzer) at 50 %. Returns the (period - 1)
   value loaded into ARR so callers can derive 50 % duty for CH1. */
static uint32_t buzzer_apply_freq(uint16_t freq)
{
    uint32_t timer_clk = 1000000U;          /* TIM1 PSC=63 → 1 MHz tick    */
    uint32_t period    = timer_clk / freq;  /* ARR = period - 1            */
    uint32_t cur_arr   = __HAL_TIM_GET_AUTORELOAD(&htim1);
    uint32_t cur_ch2   = __HAL_TIM_GET_COMPARE(&htim1, TIM_CHANNEL_2);
    uint32_t scaled_ch2 = (cur_arr ? (cur_ch2 * (period - 1U) / cur_arr) : 0U);

    __HAL_TIM_SET_AUTORELOAD(&htim1, period - 1U);
    __HAL_TIM_SET_COMPARE(&htim1, TIM_CHANNEL_2, scaled_ch2);
    __HAL_TIM_SET_COMPARE(&htim1, TIM_CHANNEL_1, period / 2U);
    return period - 1U;
}

void Buzzer_PlayFreq(uint16_t freq, uint16_t duration_ms)
{
    uint32_t cur_arr = __HAL_TIM_GET_AUTORELOAD(&htim1);
    uint32_t cur_ch2 = __HAL_TIM_GET_COMPARE(&htim1, TIM_CHANNEL_2);

    (void)buzzer_apply_freq(freq);
    HAL_Delay(duration_ms);

    Buzzer_SetDuty(0);
    __HAL_TIM_SET_AUTORELOAD(&htim1, cur_arr);
    __HAL_TIM_SET_COMPARE(&htim1, TIM_CHANNEL_2, cur_ch2);
}

void Buzzer_StartTone(uint16_t freq)
{
    if (tone_on) return;   /* re-entrant: ignore until Stop'd */
    saved_arr = __HAL_TIM_GET_AUTORELOAD(&htim1);
    saved_ch2 = __HAL_TIM_GET_COMPARE(&htim1, TIM_CHANNEL_2);
    (void)buzzer_apply_freq(freq);
    tone_on = 1;
}

void Buzzer_Stop(void)
{
    if (!tone_on) return;
    Buzzer_SetDuty(0);
    __HAL_TIM_SET_AUTORELOAD(&htim1, saved_arr);
    __HAL_TIM_SET_COMPARE(&htim1, TIM_CHANNEL_2, saved_ch2);
    tone_on = 0;
}

void buzzer_mute(void)
{
    Buzzer_Stop();
}

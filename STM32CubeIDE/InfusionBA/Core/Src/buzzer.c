#include "buzzer.h"

extern TIM_HandleTypeDef htim1;

static void Buzzer_SetDuty(uint16_t duty)
{
    __HAL_TIM_SET_COMPARE(&htim1, TIM_CHANNEL_1, duty);
}

void Buzzer_PlayFreq(uint16_t freq, uint16_t duration_ms)
{
    uint32_t timer_clk = 1000000;  // TIM1 clock after prescaler = 64 MHz / (63 + 1)
    uint32_t period = timer_clk / freq;

    __HAL_TIM_SET_AUTORELOAD(&htim1, period - 1);
    __HAL_TIM_SET_COMPARE(&htim1, TIM_CHANNEL_1, period / 2);  // 50% duty
    HAL_Delay(duration_ms);
    Buzzer_SetDuty(0);
}

void buzzer_mute(void)
{
    Buzzer_SetDuty(0);
}


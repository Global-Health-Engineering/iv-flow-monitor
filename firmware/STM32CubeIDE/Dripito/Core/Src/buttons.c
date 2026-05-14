#include "buttons.h"
#include "lcd.h"

/* Sampled state, exported for whoever wants to read it. The main loop
   owns the LCD; this module is side-effect-free. */
volatile uint8_t Buttons_MuteState = 1;   /* 1 = released (pull-up idle) */
volatile uint8_t Buttons_ModeState = 1;
volatile uint8_t Buttons_ResState  = 1;

/* Long-press threshold: 700 ms feels deliberate without being annoying. */
#define LONG_PRESS_MS 700U

static uint8_t  prev_mute = 1, prev_mode = 1, prev_res = 1;
static uint32_t mute_press_tick = 0, mode_press_tick = 0, res_press_tick = 0;
static volatile uint8_t pending_mute_short = 0, pending_mute_long = 0;
static volatile uint8_t pending_mode_short = 0, pending_mode_long = 0;
static volatile uint8_t pending_res_short  = 0, pending_res_long  = 0;

void Buttons_Poll(void)
{
    uint32_t now = HAL_GetTick();
    uint8_t mute = (HAL_GPIO_ReadPin(BTN_MUTE_GPIO_Port, BTN_MUTE_Pin)
                    == GPIO_PIN_SET) ? 1 : 0;
    uint8_t mode = (HAL_GPIO_ReadPin(BTN_MODE_GPIO_Port, BTN_MODE_Pin)
                    == GPIO_PIN_SET) ? 1 : 0;
    uint8_t res  = (HAL_GPIO_ReadPin(BTN_RES_GPIO_Port,  BTN_RES_Pin)
                    == GPIO_PIN_SET) ? 1 : 0;

    /* released (1) -> pressed (0): record the press tick. */
    if (prev_mute && !mute) mute_press_tick = now;
    if (prev_mode && !mode) mode_press_tick = now;
    if (prev_res  && !res ) res_press_tick  = now;

    /* pressed (0) -> released (1): classify short vs long by duration.
       The main loop polls sub-ms, so natural switch bounce hides inside
       one press (the first transition latches, subsequent same-value
       reads no-op until the user releases). */
    if (!prev_mute && mute) {
        if ((now - mute_press_tick) >= LONG_PRESS_MS) pending_mute_long = 1;
        else                                          pending_mute_short = 1;
    }
    if (!prev_mode && mode) {
        if ((now - mode_press_tick) >= LONG_PRESS_MS) pending_mode_long = 1;
        else                                          pending_mode_short = 1;
    }
    if (!prev_res && res) {
        if ((now - res_press_tick) >= LONG_PRESS_MS) pending_res_long = 1;
        else                                         pending_res_short = 1;
    }

    prev_mute = mute;
    prev_mode = mode;
    prev_res  = res;

    Buttons_MuteState = mute;
    Buttons_ModeState = mode;
    Buttons_ResState  = res;
}

uint8_t Buttons_MutePressed(void)
{
    if (pending_mute_short) { pending_mute_short = 0; return 1; }
    return 0;
}

uint8_t Buttons_ModePressed(void)
{
    if (pending_mode_short) { pending_mode_short = 0; return 1; }
    return 0;
}

uint8_t Buttons_ResPressed(void)
{
    if (pending_res_short) { pending_res_short = 0; return 1; }
    return 0;
}

uint8_t Buttons_MuteLongPressed(void)
{
    if (pending_mute_long) { pending_mute_long = 0; return 1; }
    return 0;
}

uint8_t Buttons_ModeLongPressed(void)
{
    if (pending_mode_long) { pending_mode_long = 0; return 1; }
    return 0;
}

uint8_t Buttons_ResLongPressed(void)
{
    if (pending_res_long) { pending_res_long = 0; return 1; }
    return 0;
}

#include "buttons.h"
#include "lcd.h"

/* Sampled state, exported for whoever wants to react to button events
   (currently no one — dashboard owns the LCD). Keep the poll cheap and
   side-effect-free until a real UX layer claims the buttons. */
volatile uint8_t Buttons_MuteState = 1;   /* 1 = released (pull-up idle) */
volatile uint8_t Buttons_ModeState = 1;

void Buttons_Poll(void)
{
    Buttons_MuteState = (HAL_GPIO_ReadPin(BTN_MUTE_GPIO_Port, BTN_MUTE_Pin)
                         == GPIO_PIN_SET) ? 1 : 0;
    Buttons_ModeState = (HAL_GPIO_ReadPin(BTN_MODE_GPIO_Port, BTN_MODE_Pin)
                         == GPIO_PIN_SET) ? 1 : 0;
    /* Intentionally no LCD writes here — lines 2 & 3 are owned by the
       dashboard. Add an event/state-machine layer when buttons are real. */
}

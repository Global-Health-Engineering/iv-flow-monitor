/*---------------------------------------------------------------------------
 * ui.c – IV‑Flow‑Meter user‑interface layer
 *
 * Implements the runtime (RUN), set‑target (SET) and alarm (ALARM) screens
 * exactly as described in the “IV Flow‑Meter User‑Interface Specification”.
 * Designed to be linked with the existing main.c that already provides:
 *   – LCD_*() primitives
 *   – button debouncing IRQ @1 kHz that posts BTN_* events
 *   – global flow / battery / time variables
 *   – TIM1‑buzzer driver
 *---------------------------------------------------------------------------*/
#include <stdio.h>
#include <string.h>
#include <stdbool.h>
#include <stdint.h>
#include "stm32g0xx_hal.h"
#include "main.h"     /* for BTN_* pin definitions */
#include "ui.h"
#include "lcd.h"      /* thin wrapper around LCD_Write*() from main.c */
#include "buzzer.h"   /* start/stop helpers – see ui_alarm_start() */
#include "alarm.h"    /* for alarm_mute() */

/*---------------------------------------------------------------------------
 *  Compile‑time constants
 *---------------------------------------------------------------------------*/
#define UI_REFRESH_PERIOD_MS   200   /* spec: update every 500 ms – we aim for 200 ms scheduler */
#define UI_ALARM_BLINK_MS      500   /* 2 Hz blink for alarm headline        */
#define UI_SET_FIELD_BLINK_MS  500   /* 1 Hz blink of editable field         */
#define UI_INACTIVITY_TO_RUN   10000 /* 10 s timeout to leave SET            */
#define UI_HOLD_REPEAT_MS      100   /* auto‑repeat interval for BTN +/-     */

#define LCD_CHARS 16

/*---------------------------------------------------------------------------
 *  Types & globals shared with main.c (extern)
 *---------------------------------------------------------------------------*/
extern volatile uint16_t            target_rate_mlh;   /* user target (0 => unset) */
extern volatile float               flow_mlh;          /* rate from last drop      */
extern volatile float               total_volume_ml;   /* accumulated volume       */
extern uint8_t                      Battery_mV_to_percent(uint32_t mv);
extern uint32_t                     Read_Battery_mV(void);

/* exported so alarm.c can drive UI */
volatile enum ui_state_e ui_state = UI_RUN;

/* local */
static uint32_t last_refresh_ms  = 0;
static uint32_t last_blink_ms    = 0;
static uint32_t last_activity_ms = 0;   /* for SET timeout                  */
static bool     blink_phase      = false;
static bool     alarm_blink      = false;
static char     lcd_shadow[4][LCD_CHARS+1]; /* hold last text to minimise SPI */
static uint32_t last_hold_ms     = 0;   /* auto-repeat timer for BTN +/-    */

/*---------------------------------------------------------------------------
 *  Helpers – format fixed‑width fields as per spec
 *---------------------------------------------------------------------------*/
static void print_rjust(char *dst, int width, int32_t val, const char *suffix)
{
    /* formats right‑aligned number (leading spaces) followed by optional suffix */
    char tmp[8];
    sprintf(tmp, "%d", (int)val);
    int len = strlen(tmp);
    int pad = (width > len) ? width - len : 0;
    memset(dst, ' ', pad);
    strcpy(dst+pad, tmp);
    if (suffix) strcat(dst, suffix);
}

static void lcd_line(uint8_t y, const char *txt)
{
    char buf[LCD_CHARS+1];
    strncpy(buf, txt, LCD_CHARS);
    buf[LCD_CHARS] = '\0';

    if (strcmp(buf, lcd_shadow[y]) != 0) {
        LCD_Print(y, buf);            /* write only if changed */
        strcpy(lcd_shadow[y], buf);
    }
}

static void lcd_clear_shadow(void)
{
    for (int i=0;i<4;i++) memset(lcd_shadow[i], 0, sizeof(lcd_shadow[i]));
}

/*---------------------------------------------------------------------------
 *  RUN screen rendering
 *---------------------------------------------------------------------------*/
static void ui_render_run(void)
{
    /* L0: Flow ### mL/h 99%   (battery right aligned) */
    char l0[LCD_CHARS+1]="Flow ";
    print_rjust(l0+5, 3, (int)flow_mlh, NULL);
    strcat(l0, " mL/h ");
    uint8_t batt = Battery_mV_to_percent(Read_Battery_mV());
    char batt_buf[5];
    sprintf(batt_buf, "%3u%%", batt);
    int pad = LCD_CHARS - strlen(l0) - strlen(batt_buf);
    while(pad-->0) strcat(l0, " ");
    strcat(l0, batt_buf);

    /* L1: Target### mL/h or blanks */
    char l1[LCD_CHARS+1]="Target";
    if (target_rate_mlh) {
        print_rjust(l1+6, 3, target_rate_mlh, NULL);
        strcat(l1, " mL/h");
    }

    /* L2: Infused####.# mL (one decimal place) */
    char l2[LCD_CHARS+1]="Infused";
    sprintf(l2+7, "%5.1f mL", total_volume_ml);

    /* L3: Time HH:MM:SS (HAL tick based) */
    uint32_t s = HAL_GetTick()/1000;
    uint32_t hh=s/3600; uint32_t mm=(s/60)%60; uint32_t ss=s%60;
    char l3[LCD_CHARS+1];
    sprintf(l3, "Time  %02lu:%02lu:%02lu", hh%24, mm, ss);

    lcd_line(0,l0); lcd_line(1,l1); lcd_line(2,l2); lcd_line(3,l3);
}

/*---------------------------------------------------------------------------
 *  SET screen
 *---------------------------------------------------------------------------*/
static uint16_t edit_rate = 0;

static void ui_render_set(bool blink)
{
    /* keep within 16 character limit using ASCII dashes */
    char l0[LCD_CHARS+1]="   - SET TARGET -"; // centred (3 spaces prefix)
    char l1[LCD_CHARS+1]="Rate: ";

    if (!blink) {
        print_rjust(l1+6, 3, edit_rate, NULL);
        strcat(l1, " mL/h");
    } else {
        strcat(l1, "           "); /* clear field while blinking */
    }

    const char *l2="+/- = adjust     ";
    const char *l3="Mode = save/exit";

    lcd_line(0,l0); lcd_line(1,l1); lcd_line(2,l2); lcd_line(3,l3);
}

/*---------------------------------------------------------------------------
 *  ALARM screen – headline blinks @2 Hz
 *---------------------------------------------------------------------------*/
/* simple alarm description used for UI titles */
struct alarm_desc_s {
    const char *title;
};

static const struct alarm_desc_s alarm_table[] = {
    [ALARM_NONE] = { "" },
    [ALARM_FLOW] = { "FLOW" },
    [ALARM_STOP] = { "STOP" },
    [ALARM_BATT] = { "BATT" },
};

static enum alarm_id_e current_alarm = ALARM_NONE;   /* current active alarm */

static void ui_render_alarm(bool blink)
{
    char l0[LCD_CHARS+1]="*ALARM*  ";
    if (!blink) {
        strcat(l0, alarm_table[current_alarm].title);
    } else {
        memset(l0, ' ', LCD_CHARS); l0[LCD_CHARS]='\0';
    }

    char l1[LCD_CHARS+1]="Meas:   mL/h";
    print_rjust(l1+6,3,(int)flow_mlh,NULL);
    char l2[LCD_CHARS+1]="Targ:   mL/h";
    print_rjust(l2+6,3,target_rate_mlh,NULL);
    const char *l3="Mute=Silence     ";

    lcd_line(0,l0); lcd_line(1,l1); lcd_line(2,l2); lcd_line(3,l3);
}

/*---------------------------------------------------------------------------
 *  Public UI task – call from main loop every 1 ms (or in SysTick). It handles
 *  periodic refresh + timeout logic. Button events come from ui_on_button().
 *---------------------------------------------------------------------------*/
void ui_task(void)
{
    uint32_t now = HAL_GetTick();

    /* handle BTN_PLUS / BTN_MINUS hold for fast adjust in SET screen */
    if (ui_state == UI_SET) {
        GPIO_PinState plus  = HAL_GPIO_ReadPin(BTN_PLUS_GPIO_Port, BTN_PLUS_Pin);
        GPIO_PinState minus = HAL_GPIO_ReadPin(BTN_MINUS_GPIO_Port, BTN_MINUS_Pin);

        if ((plus == GPIO_PIN_RESET || minus == GPIO_PIN_RESET) &&
            (now - last_hold_ms >= UI_HOLD_REPEAT_MS)) {
            if (plus == GPIO_PIN_RESET) {
                ui_on_button(BTN_PLUS, true);
            } else if (minus == GPIO_PIN_RESET) {
                ui_on_button(BTN_MINUS, true);
            }
            last_hold_ms = now;
        }

        if (plus == GPIO_PIN_SET && minus == GPIO_PIN_SET) {
            last_hold_ms = now; /* reset when neither pressed */
        }
    }

    /* 200‑ms refresh ticker */
    if (now - last_refresh_ms >= UI_REFRESH_PERIOD_MS) {
        last_refresh_ms = now;

        /* toggle blink phase */
        if (now - last_blink_ms >= UI_SET_FIELD_BLINK_MS) {
            last_blink_ms = now;
            blink_phase = !blink_phase;
        }

        switch (ui_state) {
        case UI_RUN:
            ui_render_run();
            break;
        case UI_SET:
            ui_render_set(blink_phase);
            /* inactivity auto‑exit */
            if (now - last_activity_ms >= UI_INACTIVITY_TO_RUN) {
                target_rate_mlh = edit_rate;
                ui_state = UI_RUN; lcd_clear_shadow();
            }
            break;
        case UI_ALARM:
            alarm_blink = !alarm_blink; /* 2 Hz w/ 200‑ms task */
            ui_render_alarm(alarm_blink);
            break;
        }
    }
}

/*---------------------------------------------------------------------------
 *  Button handler – called from irq context when a **debounced** event occurs
 *---------------------------------------------------------------------------*/
void ui_on_button(enum ui_button_e btn, bool long_press)
{
    last_activity_ms = HAL_GetTick();

    switch (ui_state) {
    /*-------------------------------------------------- RUN -------------*/
    case UI_RUN:
        if (btn == BTN_MODE) {
            ui_state = UI_SET;
            edit_rate = target_rate_mlh ? target_rate_mlh : 1;
            lcd_clear_shadow();
        } else if (btn == BTN_MUTE) {
            alarm_mute();             /* silence active alarm */
        }
        break;
    /*-------------------------------------------------- SET -------------*/
    case UI_SET:
        if (btn == BTN_PLUS || btn == BTN_MINUS) {
            int16_t delta = long_press ? 10 : 1;
            if (btn == BTN_MINUS) delta = -delta;
            int32_t tentative = (int32_t)edit_rate + delta;
            if (tentative < 1) tentative = 1;
            if (tentative > 400) tentative = 400;
            edit_rate = (uint16_t)tentative;
        } else if (btn == BTN_MODE) {
            target_rate_mlh = edit_rate;    /* save */
            ui_state = UI_RUN; lcd_clear_shadow();
        }
        /* Mute does nothing in SET */
        break;
    /*------------------------------------------------- ALARM ------------*/
    case UI_ALARM:
        if (btn == BTN_MUTE) {
            alarm_mute();                     /* silence buzzer only */
        }
        /* other buttons ignored */
        break;
    }
}

/*---------------------------------------------------------------------------
 *  Alarm interface (called from alarm manager)
 *---------------------------------------------------------------------------*/
void ui_alarm_start(enum alarm_id_e id)
{
    current_alarm = id;
    ui_state = UI_ALARM;
    LCD_Clear();
    lcd_clear_shadow();
}

void ui_alarm_clear(void)
{
    if (ui_state == UI_ALARM) {
        ui_state = UI_RUN;
        lcd_clear_shadow();
    }
}

/*---------------------------------------------------------------------------
 *  End of file
 *---------------------------------------------------------------------------*/
